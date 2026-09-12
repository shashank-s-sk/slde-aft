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
    python scripts/dec006_lora_finetune.py
"""

from __future__ import annotations

from pathlib import Path

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
USE_4BIT = True  # QLoRA — fits comfortably in 24GB VRAM

SYNTHETIC_DATA_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train.jsonl"
OUTPUT_DIR = "outputs/dec006_adapters/mistral7b_qlora"

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
    import torch
    from datasets import load_dataset
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer, SFTConfig

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if USE_4BIT:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, quantization_config=bnb_config, device_map="auto",
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, torch_dtype=torch.float16, device_map="auto",
        )

    model = get_peft_model(model, LoraConfig(
        r=LORA_RANK, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
        bias="none", task_type="CAUSAL_LM",
    ))

    train_ds = load_dataset("json", data_files=SYNTHETIC_DATA_PATH)["train"]
    print(f"Training on {len(train_ds)} examples -> {OUTPUT_DIR}")

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        args=SFTConfig(
            output_dir=OUTPUT_DIR,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM_STEPS,
            num_train_epochs=NUM_EPOCHS,
            learning_rate=LEARNING_RATE,
            logging_steps=10,
            save_strategy="no",
            report_to="none",
            dataset_text_field="text",
            bf16=False,  # T4 does not support bf16
            fp16=True,
        ),
    )

    trainer.train()
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    config_used = {
        "base_model": BASE_MODEL, "use_4bit": USE_4BIT,
        "lora_rank": LORA_RANK, "lora_alpha": LORA_ALPHA, "lora_dropout": LORA_DROPOUT,
        "learning_rate": LEARNING_RATE, "num_epochs": NUM_EPOCHS,
        "batch_size": BATCH_SIZE, "grad_accum_steps": GRAD_ACCUM_STEPS,
        "n_training_examples": len(train_ds),
    }
    import json
    with open(Path(OUTPUT_DIR) / "training_config.json", "w") as f:
        json.dump(config_used, f, indent=2)

    print(f"LoRA adapter saved: {OUTPUT_DIR}")
    del trainer, model
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
