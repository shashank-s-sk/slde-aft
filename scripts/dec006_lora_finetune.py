"""DEC-006 LoRA/QLoRA fine-tuning — run this on a rented GPU (RunPod
RTX 4090 24GB), NOT locally (needs torch + CUDA + transformers/peft/trl,
none of which are installed in this project's local dev environment).

Decision (see Decision log.md DEC-006 and dec006_runpod_plan memory):
  going straight to the 7B QLoRA target on a rented RTX 4090 — the
  TinyLlama-1.1B "Stage 0" sanity check is skipped by user decision.
  Model is Mistral-7B-Instruct-v0.3 (ungated on Hugging Face) rather
  than Llama-3.1-8B-Instruct, specifically to avoid the gated-repo
  approval wait, which would burn paid pod time unpredictably.

Pod setup (run first):
    pip install -q transformers peft trl accelerate bitsandbytes datasets

Usage, after `git clone`-ing this repo onto the pod:
    python scripts/dec006_lora_finetune.py               # seed 42 (default)
    python scripts/dec006_lora_finetune.py --seed 43
    python scripts/dec006_lora_finetune.py --seed 44

Multi-seed note: prior to this --seed flag, every run silently used
HF TrainingArguments' hardcoded default seed=42 regardless of intent --
EVID-026/EVID-027's single "seed" was always actually seed 42. This
flag makes seed 42 explicit (so old results are directly reproducible)
and lets 43/44 etc. produce genuinely different LoRA initializations
(via transformers.set_seed, called before model/LoRA construction --
passing seed only to SFTConfig would NOT reseed the LoRA init, since
that happens before the Trainer exists) and data ordering, for a real
multi-seed replication check (DEC-006 steps 6-8).

DEC-022 (epoch/LoRA grid) additions: --epochs and --data-path let a
single run override NUM_EPOCHS / SYNTHETIC_DATA_PATH without touching
the module-level defaults (which stay pointed at DEC-018's current
73-example provenance-filtered default -- the production default, NOT
what DEC-022's grid uses). DEC-022 Stage 1 explicitly passes
--data-path outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl
(the exact 90-example unfiltered set from EVID-028/034, extracted from
git commit eaf300f) so results stay comparable to the existing
epoch=3/seed=42 data point (F1=0.2029, EVID-034) -- do not use the
default 73-example path for DEC-022 comparisons, they are not the same
training set.

Usage (DEC-022 Stage 1):
    python scripts/dec006_lora_finetune.py --seed 42 --epochs 2 \\
        --data-path outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl \\
        --output-dir outputs/dec022_epoch_grid/epochs_2
"""

from __future__ import annotations

import argparse
from pathlib import Path

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
USE_4BIT = True  # QLoRA — fits comfortably in 24GB VRAM

SYNTHETIC_DATA_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train.jsonl"

# LoRA hyperparameters — rank/alpha/lr match the original prototype's
# proven config (paper Section 4.6 / 5.4); epochs bumped from the
# prototype's 1 to 3 per DEC-006 step 5 ("test 2-3 epochs"), since 127
# examples at 1 epoch is only ~16 optimizer steps — likely underfit.
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM_STEPS = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=None,
                         help="Override NUM_EPOCHS (DEC-022 grid); defaults to the module constant.")
    parser.add_argument("--lora-rank", type=int, default=None, help="Override LORA_RANK (DEC-022 grid).")
    parser.add_argument("--lora-alpha", type=int, default=None, help="Override LORA_ALPHA (DEC-022 grid).")
    parser.add_argument("--learning-rate", type=float, default=None, help="Override LEARNING_RATE (DEC-022 grid).")
    parser.add_argument("--data-path", type=str, default=None,
                         help="Override SYNTHETIC_DATA_PATH -- DEC-022 grid MUST pass the "
                              "90-example unfiltered set to stay comparable to EVID-034.")
    parser.add_argument("--output-dir", type=str, default=None,
                         help="Override the default output_dir naming.")
    args = parser.parse_args()
    seed = args.seed
    num_epochs = args.epochs if args.epochs is not None else NUM_EPOCHS
    lora_rank = args.lora_rank if args.lora_rank is not None else LORA_RANK
    lora_alpha = args.lora_alpha if args.lora_alpha is not None else LORA_ALPHA
    learning_rate = args.learning_rate if args.learning_rate is not None else LEARNING_RATE
    data_path = args.data_path if args.data_path is not None else SYNTHETIC_DATA_PATH
    if args.output_dir is not None:
        output_dir = args.output_dir
    else:
        output_dir = f"outputs/dec006_adapters/mistral7b_qlora_seed{seed}" if seed != 42 else "outputs/dec006_adapters/mistral7b_qlora"

    import torch
    from datasets import load_dataset
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, set_seed
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer, SFTConfig

    set_seed(seed)  # must happen before model/LoRA construction, not just via SFTConfig
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if USE_4BIT:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, quantization_config=bnb_config, device_map="auto",
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto",
        )

    model = get_peft_model(model, LoraConfig(
        r=lora_rank, lora_alpha=lora_alpha, lora_dropout=LORA_DROPOUT,
        bias="none", task_type="CAUSAL_LM",
    ))

    train_ds = load_dataset("json", data_files=data_path)["train"]
    print(f"Training on {len(train_ds)} examples (seed={seed}, epochs={num_epochs}, "
          f"rank={lora_rank}, alpha={lora_alpha}, lr={learning_rate}) -> {output_dir}")
    print(f"Data source: {data_path}")

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        args=SFTConfig(
            output_dir=output_dir,
            seed=seed,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM_STEPS,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            logging_steps=10,
            save_strategy="no",
            report_to="none",
            dataset_text_field="text",
            bf16=True,  # matches Mistral's native dtype and the RTX 4090's native bf16 support;
            fp16=False,  # avoids the fp16 GradScaler, which can't handle bf16 grad tensors
        ),
    )

    trainer.train()
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    config_used = {
        "base_model": BASE_MODEL, "use_4bit": USE_4BIT, "seed": seed,
        "lora_rank": lora_rank, "lora_alpha": lora_alpha, "lora_dropout": LORA_DROPOUT,
        "learning_rate": learning_rate, "num_epochs": num_epochs,
        "batch_size": BATCH_SIZE, "grad_accum_steps": GRAD_ACCUM_STEPS,
        "n_training_examples": len(train_ds), "data_path": data_path,
    }
    import json
    with open(Path(output_dir) / "training_config.json", "w") as f:
        json.dump(config_used, f, indent=2)

    print(f"LoRA adapter saved: {output_dir}")
    del trainer, model
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
