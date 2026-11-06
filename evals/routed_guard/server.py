"""Local CPU routing gateway and one-at-a-time GPU model workers."""
import argparse
import asyncio
from contextlib import asynccontextmanager
import gc
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .common import *

class Request(BaseModel):
    content:str=Field(min_length=1,max_length=1024*1024)
    policy_id:str="harmful_requests-v0"
    request_id:str|None=None
    model:str|None=None


def http(base,path,body=None,timeout=180):
    data=canonical(body).encode() if body is not None else None
    req=urllib.request.Request(base+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as response:return json.loads(response.read())


def free_port():
    with socket.socket() as sock:sock.bind(("127.0.0.1",0));return sock.getsockname()[1]


class Manager:
    def __init__(self,config):self.config=config;self.process=None;self.active=None;self.base=None;self.log=None
    def unload(self):
        if self.process is not None:
            if self.process.poll() is None:
                os.killpg(self.process.pid,signal.SIGTERM)
                try:self.process.wait(timeout=20)
                except subprocess.TimeoutExpired:os.killpg(self.process.pid,signal.SIGKILL);self.process.wait()
            if self.log:self.log.close()
        self.process=None;self.active=None;self.base=None;self.log=None

    def ensure(self,slug):
        if self.active==slug and self.process and self.process.poll() is None:return 0.
        self.unload();start=time.perf_counter();port=free_port()
        runtime=Path(self.config["runtime_dir"])/(slug+"-"+uuid.uuid4().hex[:12]);runtime.mkdir(parents=True)
        self.log=(runtime/"worker.log").open("w")
        command=[self.config["interpreters"].get(slug,sys.executable),"-B","-m","evals.routed_guard.server","worker","--config",self.config["config_path"],"--model",slug,"--port",str(port),"--runtime",str(runtime)]
        env=dict(os.environ,HF_HUB_OFFLINE="1",TOKENIZERS_PARALLELISM="false")
        self.process=subprocess.Popen(command,stdout=self.log,stderr=subprocess.STDOUT,cwd=ROOT,env=env,start_new_session=True)
        self.base="http://127.0.0.1:"+str(port)
        deadline=time.monotonic()+300
        while time.monotonic()<deadline:
            if self.process.poll() is not None:
                self.unload();raise RuntimeError("Guard worker startup failed")
            try:
                result=http(self.base,"/health",timeout=1)
                if result.get("model")==slug:
                    self.active=slug;return time.perf_counter()-start
            except (OSError,ValueError):pass
            time.sleep(.25)
        self.unload();raise TimeoutError("Guard worker startup timeout")

    def guard(self,slug,content,policy_id):
        if slug not in MODELS:raise ValueError("Unknown model")
        cold=self.ensure(slug)
        try:result=http(self.base,"/infer",dict(content=content,policy_id=policy_id),timeout=180)
        except Exception:
            self.unload();raise
        expected=policy_hash(self.config["policies"][policy_id])
        if result.get("input_sha256")!=sha(content) or result.get("policy_sha256")!=expected or result.get("model")!=slug:
            self.unload();raise ValueError("Worker input/policy identity mismatch")
        return dict(result,model_load_seconds=cold)


class Gateway:
    def __init__(self,config,router,manager):self.config=config;self.router=router;self.manager=manager
    def moderate(self,request,forced=False):
        if request.policy_id not in self.config["policies"]:raise ValueError("Unknown policy")
        started=time.perf_counter();router_result=None;router_error=False
        selection=read(self.config["selection_path"]) if Path(self.config["selection_path"]).exists() else dict(default_model="shieldstral",category_models={},selection_status="bootstrap")
        if forced:
            if request.model not in MODELS:raise ValueError("Unknown model")
            model,route=request.model,"forced_control"
        else:
            try:router_result=self.router.predict(request.content)
            except Exception:router_error=True
            model,route=choose_model(router_result,selection)
        route_seconds=time.perf_counter()-started;attempts=[];answer=None
        default=selection["default_model"]
        candidates=[model]+([default] if not forced and default!=model else [])
        for chosen in candidates:
            attempts.append(chosen)
            try:
                answer=self.manager.guard(chosen,request.content,request.policy_id);break
            except Exception as exc:
                error_type=type(exc).__name__
        if answer is None:
            answer=dict(prediction="REVIEW",status="error",error="guard_backend_error",error_type=error_type,
                model=attempts[-1],input_sha256=sha(request.content),policy_sha256=policy_hash(self.config["policies"][request.policy_id]))
        else:answer["status"]="ok"
        answer.update(request_id=request.request_id,route_reason=route,requested_model=model,
            router=router_result,router_error=router_error,router_seconds=route_seconds,
            guard_attempts=attempts,guard_attempted=True,latency_ms=1000*(time.perf_counter()-started),
            residency="one_gpu_guard_at_a_time",selection_status=selection.get("selection_status","frozen"))
        return answer


def serve_gateway(config_path,port):
    import uvicorn
    from evals.liquid_router.model import Router
    config=read(config_path);config["config_path"]=str(Path(config_path).resolve())
    router=Router(config["router_checkpoint"],threads=4,int8=False)
    manager=Manager(config);gateway=Gateway(config,router,manager);lock=asyncio.Lock()
    @asynccontextmanager
    async def lifespan(app):
        yield
        await asyncio.to_thread(manager.unload)
    app=FastAPI(title="Routed guard system",lifespan=lifespan)
    @app.get("/health")
    async def health():return dict(status="ready",role="gateway",instance_id=config["instance_id"],active_model=manager.active)
    @app.get("/v1/models")
    async def models():return dict(models=MODELS,active_model=manager.active,residency="one_gpu_guard_at_a_time")
    async def execute(request,forced):
        if request.policy_id not in config["policies"]:raise HTTPException(422,"Unknown policy")
        if forced and request.model not in MODELS:raise HTTPException(422,"Unknown model")
        async with lock:return await asyncio.to_thread(gateway.moderate,request,forced)
    @app.post("/v1/moderate")
    async def moderate(request:Request):return await execute(request,False)
    @app.post("/v1/guard")
    async def guard(request:Request):return await execute(request,True)
    @app.post("/v1/unload")
    async def unload():
        async with lock:await asyncio.to_thread(manager.unload)
        return dict(status="unloaded")
    uvicorn.run(app,host="127.0.0.1",port=port,access_log=False)


def serve_worker(config_path,slug,port,runtime):
    import torch
    import uvicorn
    from evals.liquid_router.study import ModerateGPU
    from .backend import Backend
    torch.set_num_threads(4)
    if not torch.cuda.is_available():raise RuntimeError("CUDA unavailable")
    config=read(config_path)
    # The estimate only gates admission; actual OOM remains a recorded error.
    free,total=torch.cuda.mem_get_info()
    minimum=(MODELS[slug]["parameters_billion"]*2+2)*10**9
    if free<minimum:raise RuntimeError("Insufficient free VRAM for native BF16 worker")
    with ModerateGPU(runtime) as budget:
        backend=budget.run(lambda:Backend(slug,config["vendor"],config.get("max_context",16384)))
        app=FastAPI(title="Native guard worker")
        @app.get("/health")
        def health():return dict(status="ready",model=slug)
        @app.post("/infer")
        def infer(request:Request):
            if request.policy_id not in config["policies"]:raise HTTPException(422,"Unknown policy")
            result=budget.run(lambda:backend.infer(request.content,config["policies"][request.policy_id],request.policy_id))
            return result
        uvicorn.run(app,host="127.0.0.1",port=port,access_log=False)
        del backend;gc.collect();torch.cuda.empty_cache()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("role",choices=["gateway","worker"]);p.add_argument("--config",required=True)
    p.add_argument("--port",type=int,default=8765);p.add_argument("--model",choices=list(MODELS));p.add_argument("--runtime")
    a=p.parse_args()
    if a.role=="gateway":serve_gateway(a.config,a.port)
    else:serve_worker(a.config,a.model,a.port,a.runtime)
