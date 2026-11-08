"""Native next-token scoring and bounded BF16 language-attention LoRA."""
import json
import math
import subprocess
import time

from evals.run import build_payload

MODEL = "mistralai/Shieldstral-1.0-3B"
REVISION = "003ec7e2b0bab5f0e6307edbaf186fa5822b76f5"
ANSWERS = {"BLOCK": 13059, "ALLOW": 2649}
SEED = 20261107


def snapshot():
    from huggingface_hub import snapshot_download

    return snapshot_download(MODEL, revision=REVISION, local_files_only=True,
                             ignore_patterns=["consolidated.safetensors"])


def tokenizer():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(snapshot(), local_files_only=True)
    for answer, label in (("yes", "BLOCK"), ("no", "ALLOW")):
        if tok.encode(answer, add_special_tokens=False) != [ANSWERS[label]]:
            raise ValueError("Unexpected answer token")
    return tok


def encode(tok, row, policy, verify=False):
    messages = build_payload("shieldstral", MODEL, policy, row["text"])["messages"]
    ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)["input_ids"]
    if verify:
        word = "yes" if row["expected"] == "BLOCK" else "no"
        full = tok.apply_chat_template(messages + [{"role": "assistant", "content": word}],
                                       tokenize=True)["input_ids"]
        if full != ids + [ANSWERS[row["expected"]], tok.eos_token_id]:
            raise ValueError("Rendered answer is not a canonical one-token continuation")
    return ids


def device_status():
    output = subprocess.check_output(
        ["nvidia-smi", "-i", "0",
         "--query-gpu=temperature.gpu,power.draw,memory.used,memory.free",
         "--format=csv,noheader,nounits"], text=True, timeout=5,
    )
    return dict(zip(("temperature_c", "power_w", "used_mib", "free_mib"),
                    map(float, output.strip().split(",")), strict=True))


class Budget:
    def __init__(self, log):
        self.log = log
        self.started = time.monotonic()
        self.last_sample = -math.inf
        self.high_power_since = None
        self.samples = []
        self.work_seconds = 0.0

    def before(self, force=False):
        now = time.monotonic()
        if now - self.started >= 35 * 60:
            raise TimeoutError("GPU stage exceeded 35 minutes")
        if not force and now - self.last_sample < 1:
            return
        end = now + 180
        while True:
            now = time.monotonic()
            sample = device_status()
            self.last_sample = now
            self.samples.append(sample)
            self.log.write(json.dumps({"elapsed_seconds": now - self.started, **sample}) + "\n")
            self.log.flush()
            if sample["temperature_c"] >= 70:
                raise RuntimeError("GPU reached the temperature stop limit")
            if sample["power_w"] >= 250:
                if self.high_power_since is None:
                    self.high_power_since = now
                elif now - self.high_power_since >= 5:
                    raise RuntimeError("GPU reached the sustained power stop limit")
            else:
                self.high_power_since = None
            if sample["temperature_c"] < 60 and sample["power_w"] < 200:
                return
            if now >= end:
                raise TimeoutError("GPU did not recover within the cooldown window")
            time.sleep(1)

    def rest(self, start):
        seconds = time.monotonic() - start
        self.work_seconds += seconds
        time.sleep(3 * seconds)

    def summary(self):
        return {
            "elapsed_seconds": time.monotonic() - self.started,
            "operation_seconds": self.work_seconds,
            "sampled_peak": {key: max(sample[key] for sample in self.samples)
                             for key in ("temperature_c", "power_w", "used_mib")},
        }


def load_base():
    import torch
    from transformers import Mistral3ForConditionalGeneration

    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("A BF16 CUDA device is required")
    torch.cuda.set_per_process_memory_fraction(0.50, 0)
    if torch.cuda.mem_get_info()[0] < 16 * 1024 ** 3:
        raise RuntimeError("Less than 16 GiB VRAM available before loading")
    model, info = Mistral3ForConditionalGeneration.from_pretrained(
        snapshot(), dtype=torch.bfloat16, attn_implementation="sdpa",
        local_files_only=True, output_loading_info=True,
    )
    for field in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"):
        if info.get(field):
            raise ValueError(f"Weight loader reported {field}: {info[field]}")
    return model.to("cuda").requires_grad_(False)


def new_adapter(base):
    from peft import LoraConfig, get_peft_model

    adapter = get_peft_model(base, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.0, task_type="CAUSAL_LM",
        target_modules=r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj)",
        revision=REVISION,
    ))
    adapter.peft_config["default"].base_model_name_or_path = MODEL
    trainable = [name for name, value in adapter.named_parameters() if value.requires_grad]
    if len(trainable) != 8 * base.config.text_config.num_hidden_layers:
        raise RuntimeError("Unexpected trainable parameter count")
    if any(".language_model." not in n or ".lora_" not in n for n in trainable):
        raise RuntimeError("Unexpected trainable parameter scope")
    base.model.language_model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    return adapter


def logits(base, tok, inputs):
    """Gather the last real position of each input before the vocabulary head."""
    import torch

    lengths = torch.tensor([len(ids) for ids in inputs], device="cuda")
    width = max(map(len, inputs))
    tokens = torch.tensor(
        [ids + [tok.pad_token_id] * (width - len(ids)) for ids in inputs],
        device="cuda",
    )
    mask = torch.arange(width, device="cuda").unsqueeze(0) < lengths.unsqueeze(1)
    hidden = base.model.language_model(
        input_ids=tokens, attention_mask=mask, use_cache=False, return_dict=True,
    ).last_hidden_state
    return base.lm_head(hidden[torch.arange(len(inputs), device="cuda"), lengths - 1]).float()


def answer_scores(values):
    return values[:, [ANSWERS["BLOCK"], ANSWERS["ALLOW"]]].softmax(-1)[:, 0]
