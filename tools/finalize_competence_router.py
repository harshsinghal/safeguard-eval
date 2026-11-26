"""Local readout, resource cleanup and prompt-free evidence; never commits or pushes."""
import argparse
from importlib.metadata import version
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.routed_guard.common import ROOT, ORDER, read, rows, write, canonical
from evals.routed_guard.server import http
from evals.competence_router.study import verify_freeze
from tools.report_competence_router import package


def finalize(state,bundle):
    state,bundle=Path(state),Path(bundle);verify_freeze(state)
    if not (state/'public/actual-results.json').exists():raise ValueError('Complete actual evaluation first')
    config=read(state/'config.private.json');entry=read(state/'gateway.private.json')
    health=http(entry['base'],'/health',timeout=3)
    if health['instance_id']!=config['instance_id']:raise ValueError('Collection gateway identity mismatch')
    http(entry['base'],'/v1/unload',{},timeout=30);os.killpg(entry['pid'],signal.SIGTERM)
    for _ in range(100):
        try:http(entry['base'],'/health',timeout=.2)
        except OSError:break
        time.sleep(.1)
    else:raise RuntimeError('Collection gateway still running')
    cleanup=read(state/'public/cleanup.json');cleanup.update(collection_gateway_stopped=True,
        previous_pilot_service_untouched=True,no_git_commit_or_push=True)
    write(state/'public/cleanup.json',cleanup)
    resource={};all_samples=[]
    for split in ('fit','validation','test','actual'):
        rr=rows(state/'public'/(split+'-device.jsonl'));all_samples+=rr
        resource[split]=dict(samples=len(rr),elapsed_seconds=rr[-1]['seconds'],
            sampled_peak_temperature_c=max(r['temperature_c'] for r in rr),sampled_peak_power_w=max(r['power_w'] for r in rr),
            sampled_mean_power_w=sum(r['power_w'] for r in rr)/len(rr),samples_above_250w=sum(r['power_w']>250 for r in rr))
    resource.update(sampled_peak_temperature_c=max(r['temperature_c'] for r in all_samples),
        sampled_peak_power_w=max(r['power_w'] for r in all_samples),
        sampled_mean_power_w=sum(r['power_w'] for r in all_samples)/len(all_samples),
        sampled_peak_device_memory_mib=max(r['memory_mib'] for r in all_samples),paid_compute_usd=0,
        hardware_power_or_clock_settings_changed=False,
        limitation='Whole-device 0.5s samples include other applications and may miss instantaneous peaks. Software duty reduces sustained use, not instantaneous power.')
    write(state/'public/resources.json',resource)
    cpu=next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),'unknown')
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip()
    write(state/'public/environment.json',dict(cpu=cpu,gpu_and_driver=gpu,cpu_threads=4,
        python=sys.version.split()[0],packages={p:version(p) for p in ('torch','transformers','scikit-learn','numpy','safetensors','fastapi')},
        git_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        study_changes_uncommitted=True,publication_authorized=False))
    results=read(state/'public/results.json');actual=read(state/'public/actual-results.json');selection=read(state/'public/validation-selection.json')
    chosen=selection['selected_route'];baseline=results['test']['arms']['clef']['accuracy'];score=actual['accuracy']
    def pct(x):return f'{100*x:.2f}%'
    labels=dict(clef='Clef alone',original_category='Original category router',conservative_category='Conservative policy-category control',competence='Liquid competence router')
    table='| System | Reserved test | Exposed pilot diagnostic |\n|---|---:|---:|\n'
    for arm,label in labels.items():table+=f"| {label} | {pct(results['test']['arms'][arm]['accuracy'])} | {pct(results['pilot_diagnostic']['arms'][arm]['accuracy'])} |\n"
    message=('Validation supported switching to '+', '.join(chosen['config']['enabled_models'])+'.') if chosen['config']['enabled_models'] else 'Validation did not support any challenger; the frozen routing rule uses Clef for every input.'
    text=f'''# Learning which guard is likely to succeed

Implemented and evaluated locally. No Git commit or push was made.

The actual two-stage system scored **{pct(score)} ({round(score*112)}/112)** on the
reserved competence test, versus **{pct(baseline)}** for Clef alone. {message}
These are exploratory reference-label results, not independently adjudicated
enterprise deployment accuracy.

{table}
The reserved panel contains 112 binary cases across ten tasks, selected by
category/label strata from the archived Liquid validation pool. Those texts and
family labels were exposed in earlier category-classifier validation; this is a
new competence-routing holdout, not a wholly unseen benchmark. The original
112-case pilot was already inspected and is only a diagnostic. Neither panel
was used to select this study's final routing configuration. Official enterprise
profiles are withheld for the reserved panel because four suite tasks are absent.
The available-task macro recall and per-task/class errors remain in the evidence.

## Model and selection

A pinned pretrained Liquid LFM2.5 Encoder 350M remains frozen on CPU. Four
independent L2 logistic heads learn whether PolicyLM, Shieldstral, Kev and Clef
return the reference decision on the same prompt and policy. Multiple guards can
be correct. Technical failures are masked in semantic fitting and count wrong in
system evaluation. There were 640 training cases (including 192 reused, exact-
configuration calibration cases), 112 validation cases and 112 test cases. Known
source/near-duplicate audit groups and identical bounded views do not cross these
splits. The source benchmark's 983 evaluation cases are protected from fitting.
The original calibration cases are intentionally development data in this study;
see the recorded protocol clarification.

Features comprise a bounded prompt view (256 tokens), a separately bounded
semantic policy view (192), the allowed decision contract and ten structure/
length features. Source names, benchmark IDs, reference labels and guard outputs
are excluded from model features. The selected guard always receives full text.
Policies are trusted application configuration. Editing policy semantics or the
allowed decisions uses the default until supported by validation.

C={selection['selected_C']} was selected by validation binary log loss. The frozen
switch margin is {chosen['config']['switch_margin']}; each challenger requires
at least eight switched validation cases and a positive 90% group-bootstrap
lower bound of paired improvement. The combined route must also clear that gate.
This is a conservative exploratory selection heuristic, not a guarantee after
multiple candidate comparisons. All candidates and negative results are retained.
Only ten fitting examples are REVIEW; neither ternary policy has enough separate
validation support to switch away from Clef. Native guard weights, policy text,
thresholds, BF16 precision and adapters were held fixed.

## System verification and resources

Actual HTTP requests attempted a guard on {pct(actual['guard_attempt_coverage'])}
of test cases, with {pct(actual['successful_guard_coverage'])} successful guard
coverage. Actual decisions differed from the matching direct guard controls on
{actual['control_decision_changes']} cases. Router/primary-backend failures fall
back to Clef; unresolved errors remain failed REVIEW, never successful ALLOW.
CPU inference is FP32 with four threads; the saved encoder reproduced its features
exactly on an offline reload check. Dynamic INT8 was not part of this study.

Actual request latency: median {actual['actual_latency_ms']['p50']:.1f}ms,
p95 {actual['actual_latency_ms']['p95']:.1f}ms, p99 {actual['actual_latency_ms']['p99']:.1f}ms.
This includes CPU routing, native inference, deliberate cooldown, HTTP and cold
loads when needed. Requests were grouped by selected guard, so this does not
measure simultaneous model residency or natural-traffic switching latency.

Sampled device peak: **{resource['sampled_peak_temperature_c']:.0f}C** and
**{resource['sampled_peak_power_w']:.2f}W**; mean sampled power across collection
and actual-evaluation windows was **{resource['sampled_mean_power_w']:.2f}W**.
The software 20% operation duty and cooldown checks limit sustained use and do
not cap instantaneous power. Brief high-power samples are preserved. Device
samples include other applications. No clocks or power limits were changed and
no paid compute was used. All study guard workers and both study gateways were
stopped; the earlier pilot's CPU service was left untouched.

[Plan](PLAN.md) · [Run locally](RUNNING.md) ·
[Local prompt-free evidence](../../{bundle.as_posix()}/manifest.json)

Recompute and check the evidence without prompts, weights or a GPU:

```bash
python -B tools/report_competence_router.py verify --bundle {bundle.as_posix()}
```
'''
    (ROOT/'docs/competence-router/README.md').write_text(text)
    p=ROOT/'README.md';s=p.read_text();old=next(l for l in s.splitlines() if l.startswith('**Local routing development:**'))
    s=s.replace(old,f'**Local routing development:** [Learning which guard is likely to succeed](docs/competence-router/README.md) — four Liquid CPU guard-correctness heads with mandatory guard dispatch. Reserved 112-case system accuracy {pct(score)} versus {pct(baseline)} for Clef. Uncommitted local results; no push requested.')
    p.write_text(s)
    write(state/'public/readout-summary.json',dict(actual_accuracy=score,clef_accuracy=baseline,validation_switching_supported=bool(chosen['config']['enabled_models']),
        selected_models=chosen['config']['enabled_models'],switch_margin=chosen['config']['switch_margin'],
        unchanged_core_hashes_verified=True,limitations=['Small binary competence holdout','Prior category-classifier exposure','Ternary routes default-only','Dataset labels await human review'],
        scope='Local exploratory study; no commit or push'))
    package(state,bundle)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--bundle',required=True)
    a=p.parse_args();finalize(a.state,a.bundle)
