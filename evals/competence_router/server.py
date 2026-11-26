"""Optional competence gateway; existing frozen category gateway is unchanged."""
import argparse
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import time
from fastapi import FastAPI, HTTPException
from evals.routed_guard.common import MODELS, labels_for, policy_hash, read, sha
from evals.routed_guard.server import Manager, Request
from .model import CompetenceRouter


class Gateway:
    def __init__(self, config, router, manager):
        self.config, self.router, self.manager = config, router, manager

    def moderate(self, request, forced=False):
        if request.policy_id not in self.config['policies']: raise ValueError('Unknown policy')
        started = time.perf_counter(); result = None; router_error = False
        default = self.router.config['default_model']; policy = self.config['policies'][request.policy_id]
        if forced:
            if request.model not in MODELS: raise ValueError('Unknown guard')
            model, reason = request.model, 'forced_control'
        else:
            try:
                result = self.router.predict(request.content, policy, labels_for(request.policy_id))
                model, reason = result['selected_model'], result['route_reason']
                if model not in MODELS: raise ValueError('Unknown guard')
            except Exception:
                model, reason, router_error = default, 'router_error_default', True
        route_seconds = time.perf_counter()-started; attempts = []; answer = None; error_type = None
        for chosen in [model]+([default] if not forced and model!=default else []):
            attempts.append(chosen)
            try:
                answer = self.manager.guard(chosen, request.content, request.policy_id); break
            except Exception as exc: error_type = type(exc).__name__
        if answer is None:
            answer = dict(prediction='REVIEW', status='error', error='guard_backend_error', error_type=error_type,
                model=attempts[-1], input_sha256=sha(request.content), policy_sha256=policy_hash(policy))
        else: answer['status'] = 'ok'
        answer.update(request_id=request.request_id, router=result, router_error=router_error,
            requested_model=model, route_reason=reason, guard_attempted=True, guard_attempts=attempts,
            router_seconds=route_seconds, latency_ms=1000*(time.perf_counter()-started),
            residency='one_gpu_guard_at_a_time', selection_status='competence_frozen')
        return answer


def serve(config_path, port):
    import uvicorn
    config = read(config_path); config['config_path'] = str(Path(config_path).resolve())
    router = CompetenceRouter(config['competence_checkpoint'], threads=4)
    manager = Manager(config); gateway = Gateway(config, router, manager); lock = asyncio.Lock()
    @asynccontextmanager
    async def lifespan(app):
        yield
        await asyncio.to_thread(manager.unload)
    app = FastAPI(title='Liquid guard competence router', lifespan=lifespan)
    @app.get('/health')
    async def health():
        return dict(status='ready', role='competence_gateway', instance_id=config['instance_id'], active_model=manager.active)
    @app.get('/v1/models')
    async def models(): return dict(models=MODELS, active_model=manager.active)
    async def execute(request, forced):
        if request.policy_id not in config['policies']: raise HTTPException(422, 'Unknown policy')
        if forced and request.model not in MODELS: raise HTTPException(422, 'Unknown guard')
        async with lock: return await asyncio.to_thread(gateway.moderate, request, forced)
    @app.post('/v1/moderate')
    async def moderate(request:Request): return await execute(request, False)
    @app.post('/v1/guard')
    async def guard(request:Request): return await execute(request, True)
    @app.post('/v1/unload')
    async def unload():
        async with lock: await asyncio.to_thread(manager.unload)
        return dict(status='unloaded')
    uvicorn.run(app, host='127.0.0.1', port=port, access_log=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--config', required=True); p.add_argument('--port', type=int, default=8766)
    a=p.parse_args(); serve(a.config,a.port)
