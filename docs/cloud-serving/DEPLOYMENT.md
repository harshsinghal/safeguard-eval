# What a moderation team takes on when it hosts the model

A model's benchmark score helps decide whether it understands the boundary you
care about. A serving benchmark asks a different question: can your system apply
that boundary quickly, reliably and at an acceptable cost when requests arrive?
Both questions matter. A fast wrong decision is still wrong; a correct decision
that arrives after a workflow has already acted can be too late to help.

## Our results make the deployment a system choice

The [seven-model L40S study](../serving/README.md) did not reveal one universal
serving recipe. Shared-policy caching helped Shieldstral substantially, but
Qwen's short shared prefix produced no cache hits in the measured configuration.
Optimized kernels helped Kev. A larger PolicyLM batch ran out of memory, and
another batch configuration shifted scores enough to fail our consistency gate.
WildGuard needed its original tokenizer restored before its timing study could
proceed. These are concrete examples of engineering work behind a model endpoint.

The Liquid classifier was fast, but it had learned a particular task boundary
through fine-tuning. That is different from interpreting a new policy document
at inference time. Likewise, a model that returns a typed score through a custom
head cannot be assumed to work through a generic chat endpoint. An engineer
should preserve the model's actual classification interface before optimizing it.

Running open weights within your own environment gives you control over the
processing location and serving configuration. It does not itself establish
zero retention: request logs, traces, backups, access and storage still need to
be configured. Jev was API-only in our experiments, so it is not part of these
self-hosted GPU comparisons.

## Choose capacity for the requests you actually receive

The first serving study used mostly short benchmark prompts. An employee might
instead paste a long email thread, a draft report or several retrieved passages.
Those are different loads. The server first processes the input and then
produces the classification. Even a one-letter answer may require substantial
work on a long input.

Measure three lengths separately: the policy, the submitted content, and the
full serialized model input. Token counts differ between tokenizers. A limit of
4,096 words is not a limit of 4,096 tokens, and an advertised context window must
also accommodate policy framing and output. Define behavior for oversized inputs
explicitly. Truncation can remove the very passage that changes the decision;
splitting a document requires a tested rule for combining segment decisions.

Our [L4 pilot](PLAN.md) holds policy text fixed and varies content length. Its
synthetic documents measure processing load; they do not establish moderation
accuracy on long enterprise documents. A production evaluation should add
labeled examples with important content at the beginning, middle and end,
quoted instructions, benign lookalikes, and the actual languages used.

Concurrency is another axis. Batching may process more requests per second
while making each person wait longer. Test realistic mixtures of short and long
requests, then test arrival rates and bursts. Record complete-decision p50, p95
and p99 latency, errors and backlog. Our closed-loop pilots estimate capacity
under bounded in-flight load; they do not establish production latency targets.

## vLLM or SGLang is an empirical choice

Both are actively developed inference systems. Their supported architectures,
memory management, kernels and caching behavior change over versions. Compare
the same model revision, precision, token IDs, output contract and hardware.
Use the same tuning allowance, retain failures, and check whether decisions or
scores changed. A faster engine that changed the classification is not a clean
replacement until its quality is evaluated.

Cache behavior needs its own workload. A service that repeatedly uses one long
policy may benefit from sharing its processed prefix. A service with many
tenants, frequent policy changes or many distinct prefixes may benefit less.
Measure both cache hits and misses; do not present a warm-cache maximum as the
capacity every request will receive. The primary L4 comparison disables caches.

The matched pilot can inform this particular model and workload. It cannot
establish that either engine is universally superior, or that a custom decision
head will receive the same optimizations as an ordinary language model.
See the official [SGLang serving benchmark guide](https://docs.sglang.io/docs/developer_guide/bench_serving)
and [server configuration reference](https://docs.sglang.io/docs/advanced_features/server_arguments)
for the controls behind that comparison.

## A practical cloud target

NVIDIA's 24 GB L4 is offered in
[AWS G6](https://aws.amazon.com/ec2/instance-types/g6/) and
[Google Cloud G2](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines).
It is a useful common starting point for the smaller systems studied here.
We rent an L4 through GPU.ai to test model execution without accessing either
cloud account. This is a hardware selection, not a provider endorsement.

An L4 result is a starting estimate for another L4 deployment. CPU count, RAM,
power limits, driver versions, network paths and VM overhead can differ.
The published cloud families do not guarantee capacity in a particular zone
or sufficient quota. Cloud pricing, storage, network traffic, replicas and
availability design must be priced separately. Our GPU.ai rate is not an AWS
or Google Cloud cost estimate.

## Divide the work deliberately

Policy owners define the intended boundary, expensive mistakes, exceptions and
review cases. Engineers preserve that intent through the adapter, threshold,
input limits and serving runtime. Together they maintain a representative
benchmark and a release check that covers both quality and performance.

For each proposed deployment, keep a versioned record of the weights, policy,
adapter, tokenizer, decision cutoff, engine, precision and batch/cache settings.
Set a waiting-time target before choosing throughput. Measure cold starts,
queue saturation, timeouts and recovery as well as warm inference. Decide what
the application should do when moderation is unavailable or uncertain, and
test that behavior. Release changes with a rollback path and observe real
traffic for drift.

A prompt policy is also only one layer in an enterprise AI system. It cannot
repair incorrect source permissions or guarantee what an agent subsequently
retrieves or does. Keep access control, retrieval checks, tool permissions and
response controls as separate responsibilities. Our experiments do not validate
an enterprise authorization system.
