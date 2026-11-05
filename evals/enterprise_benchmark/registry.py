"""Task contracts and normative scoring profiles; no model-result selection inputs."""
TRACKS={
"harmful_requests":dict(domain="content",title="Harmful user requests",labels=["ALLOW","BLOCK"],group_namespace="wildguard",family="wildguard",tier="human_test_model_assisted_development",source="allenai/wildguardmix",policy_path="evals/wildguard/policies/p0.json"),
"hate_speech":dict(domain="content",title="Hate versus offensive/normal speech",labels=["ALLOW","BLOCK"],group_namespace="hatexplain",family="hatexplain",tier="human_majority_with_disagreement",source="hate-alert/HateXplain",policy_path="evals/hatexplain/policies/p0.json"),
"injection_deepset":dict(domain="injection",title="Deepset instruction-boundary attacks",labels=["ALLOW","BLOCK"],group_namespace="injection",family="injections",tier="source_labels_context_ambiguity",source="deepset/prompt-injections",policy_path="evals/injection/binary-policy.json"),
"injection_xtram":dict(domain="injection",title="xTRam1 injection collection",labels=["ALLOW","BLOCK"],group_namespace="injection",family="injections",tier="largely_synthetic_source_labels",source="xTRam1/safe-guard-prompt-injection",policy_path="evals/injection/binary-policy.json"),
"benign_lookalikes":dict(domain="injection",title="Benign injection lookalikes",labels=["ALLOW"],group_namespace="injection",family="injections",tier="source_benign_stress_labels",source="leolee99/NotInject",policy_path="evals/injection/binary-policy.json"),
"jailbreak_attempts":dict(domain="injection",title="Released jailbreak-attempt detection",labels=["BLOCK"],group_namespace="injection",family="injections",tier="released_attack_intent_not_success",source="JailbreakBench/artifacts",policy_path="evals/injection/binary-policy.json"),
"injection_context":dict(domain="injection",title="Injection/context ambiguity",labels=["ALLOW","BLOCK","REVIEW"],group_namespace="synthetic_injection",family="synthetic",tier="ai_authored_unadjudicated",source="project_synthetic_injection",policy_path="evals/injection/policy.json"),
"source_code":dict(domain="artifacts",title="Static source-file screening",labels=["ALLOW","BLOCK"],group_namespace="omc",family="artifacts",tier="mixed_model_and_benign_package_labels",source="False-Positive-Community/open-malicious-code-benchmark"),
"skill_text":dict(domain="artifacts",title="Static agent-skill text",labels=["ALLOW","BLOCK"],group_namespace="maliciousskill",family="artifacts",tier="mixed_source_labels",source="ProtectSkills/MaliciousSkillBench"),
"skill_packages":dict(domain="artifacts",title="Complete textual skill packages",labels=["ALLOW","BLOCK"],group_namespace="malskill",family="skill_packages",tier="predominantly_synthetic_research_only",source="lxyeternal/MalSkillBench"),
"cyber_requests":dict(domain="cyber",title="Cyber abuse versus legitimate administration",labels=["ALLOW","BLOCK"],group_namespace="cyber",family="cyber",tier="source_intent_mapping_dual_use_ambiguity",source="meta-llama/PurpleLlama"),
"agent_actions":dict(domain="agent",title="Pending agent actions in context",labels=["ALLOW","BLOCK"],group_namespace="stepguard",family="stepguard",tier="synthetic_automatically_reviewed",source="ninty-seven/stepguard_data"),
"agent_runs":dict(domain="agent",title="Completed agent-run audits",labels=["ALLOW","BLOCK"],group_namespace="stepguard",family="stepguard",tier="synthetic_automatically_reviewed",source="ninty-seven/stepguard_data"),
"custom_policy":dict(domain="custom_policy",title="Configurable image-prompt policy",labels=["ALLOW","BLOCK","REVIEW"],group_namespace="iconography",family="synthetic",tier="ai_authored_unadjudicated",source="project_synthetic_iconography",policy_path="evals/policy.json")}
DOMAIN_WEIGHTS={"agent":.35,"injection":.25,"artifacts":.20,"cyber":.10,"content":.05,"custom_policy":.05}
PROFILES={"enterprise_reference_v0":dict(domain_weights=DOMAIN_WEIGHTS,within_domain="equal_task",within_task="equal_reference_class",
    interpretation="Normative reference priorities, not incident frequencies or validated business loss."),
    "equal_task_v0":dict(task_weights={t:1/len(TRACKS) for t in TRACKS},within_task="equal_reference_class",
    interpretation="Every task has equal influence; corpus size does not determine weight.")}
ENCODER=dict(repo="sentence-transformers/all-MiniLM-L6-v2",revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    device="cpu",threads=4,batch_size=16,view_tokens=224,width=384,pooling="attention-mask mean and L2 normalization")
SEED=20261105

def case_id(track,source_id):
    import hashlib
    return "ems-"+hashlib.sha256((track+"\0"+source_id).encode()).hexdigest()[:24]
