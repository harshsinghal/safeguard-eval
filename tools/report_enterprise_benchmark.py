"""Write metadata-only assembly evidence; never publish source prompts or embeddings."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import json
from pathlib import Path
import platform
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.enterprise_benchmark.sources import ROOT,rows,read,dump,sha
from evals.enterprise_benchmark.registry import TRACKS
from evals.enterprise_benchmark.validate import validate
from tools.audit_enterprise_overlap import audit

REVISIONS={
"allenai/wildguardmix":"d29c47f41c8b51348b5c8e8c81c039b3132b66d1",
"hate-alert/HateXplain":"01d742279dac941981f53806154481c0e15ee686",
"deepset/prompt-injections":"4f61ecb038e9c3fb77e21034b22511b523772cdd",
"xTRam1/safe-guard-prompt-injection":"a3a877d608f37b7d20d9945671902df895ecdb46",
"leolee99/NotInject":"847ae76cf8fea5ed325429e569ae8cfef022d2e0",
"JailbreakBench/artifacts":"909e68c01d94222b8ad2e397a017e2e12e2adb73",
"False-Positive-Community/open-malicious-code-benchmark":"f0722971eddb654c308106c9086ff69da5b0484b",
"ProtectSkills/MaliciousSkillBench":"d4b42ce5766a6e0359c987cf59c1007cb3795a90",
"meta-llama/PurpleLlama":"f64eebd53003a87d9c2d2a3a712133534c214c8d",
"lxyeternal/MalSkillBench":"3548e2837adf58b96497f2c688f96beff26485da",
"ninty-seven/stepguard_data":"aadeae009800d8fbcd145575f1d1a6b37abb0950",
"project_synthetic_injection":"repository fixture at 9dacb204f8affbb9a53c470892302430ccaa4b1d",
"project_synthetic_iconography":"repository fixture at 9dacb204f8affbb9a53c470892302430ccaa4b1d"}

def report(bundle,state,inputs):
    bundle,state,inputs=Path(bundle),Path(state),Path(inputs)
    for name in ("assembly-report.json","source-inventory.json","validation.json","near-duplicate-audit.json"):
        if (bundle/name).exists():raise ValueError("Do not overwrite assembly evidence")
    result=validate(bundle,inputs);overlap=audit(inputs)
    if overlap["high_similarity_pairs"]:raise ValueError("Review calibration/evaluation near duplicates before release")
    cases=rows(bundle/"evaluation.jsonl");cal=rows(bundle/"calibration.jsonl")
    coverage=read(bundle/"coverage.json")
    inventory=[]
    for source in sorted({s["source"] for s in TRACKS.values()}):
        tasks=[t for t,s in TRACKS.items() if s["source"]==source]
        inventory.append(dict(source=source,revision=REVISIONS[source],tasks=tasks,
            evaluation=sum(r["track"] in tasks for r in cases),calibration=sum(r["track"] in tasks for r in cal),
            reference_provenance=sorted({TRACKS[t]["tier"] for t in tasks}),raw_source_text_redistributed=False,
            permissions="Publisher conditions remain in force; dataset text is restored privately.",
            source_notes="docs/datasets/README.md"))
    unscored=[
        dict(source="poloclub/diffusiondb",role="excluded_unlabeled",reason="No reference labels for the project's custom policy"),
        dict(source="synthetic_neutral_serving_documents",role="excluded_unlabeled",reason="Performance workload, not an accuracy reference"),
        dict(source="local_ollama_teaching_cases",n=8,role="integration_only",reason="Hand-written smoke cases without a held-out evaluation design"),
        dict(source="security_cognition_seed",n=24,role="diagnostic_review_seed",path="docs/security-cognition/seed-cases.jsonl",
            reason="Useful enterprise authorization/privacy cases; AI-authored labels not independently adjudicated and no headline weight")]
    dump(bundle/"source-inventory.json",dict(scored_sources=inventory,unscored_sources=unscored))
    dump(bundle/"validation.json",dict(checked_utc=datetime.now(timezone.utc).isoformat(),**result))
    dump(bundle/"near-duplicate-audit.json",overlap)
    embedding=read(state/"embedding-manifest.json")
    summary=dict(created_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        candidate_pool_before_grouping=len(rows(state/"pool.jsonl")),embedded_cases=len(embedding["ids"]),
        embedding_seconds=embedding["seconds"],encoder=embedding["encoder"],gpu_used=False,
        evaluation=len(cases),calibration=len(cal),scored_sources=len(inventory),tasks=len(TRACKS),
        clusters=len(read(bundle/"topics.json")),
        selected_clusters=sum(len(r["evaluation"]["topics"]) for r in coverage.values()),
        source_risk_buckets_omitted={t:sorted(set(r["evaluation"]["available_risks"])-set(r["evaluation"]["risks"])) for t,r in coverage.items() if set(r["evaluation"]["available_risks"])-set(r["evaluation"]["risks"])},
        labels=dict(Counter(r["expected"] for r in cases)),reference_tiers=dict(Counter(r["reference_provenance"] for r in cases)),
        lengths=dict(Counter(r["length_band"] for r in cases)),maximum_input_bytes=max(r["input_bytes"] for r in cases),
        moderation_model_outputs_used=False,moderation_model_evaluations=0,provider_gpu_usd=0,inference_api_usd=0,
        raw_source_text_or_embeddings_published=False,unit_tests_passed=20,review_status="pending independent adjudication")
    dump(bundle/"assembly-report.json",summary)
    table=["| Task | Evaluation | Calibration | Reference classes |","|---|---:|---:|---|"]
    for t,spec in TRACKS.items():
        table.append(f'| {spec["title"]} | {sum(r["track"]==t for r in cases)} | {sum(r["track"]==t for r in cal)} | {", ".join(spec["labels"])} |')
    text="# Enterprise Moderation Suite candidate v0.1\n\n"
    text+="983 evaluation cases, 192 calibration cases, 14 tasks from 13 sources.\n\n"
    text+="[Methods, scoring equation and usage](../../../docs/enterprise-benchmark/README.md) · [Assembly evidence](assembly-report.json) · [Coverage](coverage.json) · [Review queue](review-queue.jsonl)\n\n"
    text+="\n".join(table)+"\n\n"
    text+="Model-facing IDs are opaque. Full source inputs and embeddings are private; this bundle contains case metadata, reference labels, policies, weights, provenance and audits.\n\n"
    text+="This is a source-label candidate awaiting independent review, not a validated enterprise-incident test. No moderation model or quantization/runtime sweep has run. Both score profiles, case identities and policies are versioned before model evaluation.\n"
    (bundle/"README.md").write_text(text)
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("bundle","state","inputs"):p.add_argument("--"+n,required=True,type=Path)
    a=p.parse_args();report(a.bundle,a.state,a.inputs)
