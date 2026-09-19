#!/bin/bash
# DEC-022 Stage 3 runbook: 5-seed confirmatory run of the winning
# epoch/LoRA config (epochs=5, rank=16, alpha=32, lr=2e-4) found by
# Stages 1-2 (EVID-037/038). Seed 42 is already done (F1=0.2222,
# P=1.0, R=0.125) -- this covers seeds 43-46.
#
# Run this ON a freshly rented RunPod GPU pod (RTX 4090, fall back to
# 3090 if GPU passthrough fails), one line/section at a time, or as a
# whole script with: bash dec022_stage3_pod_runbook.sh
#
# After it finishes: paste the printed P/R/F1 lines from each of the
# 4 eval steps back to Claude to compute the final 5-seed significance
# test against both the base model and the existing epochs=3 default
# (EVID-034, p=0.066).

set -e  # stop on first real error rather than silently continuing

echo "=== Step 1: GPU sanity check ==="
nvidia-smi
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
echo "If the line above did not say True, STOP here, terminate this pod, and deploy a fresh one instead of continuing."
read -p "Press Enter once you've confirmed CUDA is True..."

echo "=== Step 2: Clone and checkout ==="
git clone https://github.com/shashank-s-sk/slde-aft.git
cd slde-aft
git checkout dec003-pkb-validation

echo "=== Step 3: Install dependencies ==="
pip install -q transformers peft trl accelerate bitsandbytes datasets

echo "=== Step 4: Set PYTHONPATH ==="
export PYTHONPATH=$(pwd)

echo "=== Step 5: Regenerate the 90-example unfiltered training set ==="
mkdir -p outputs/dec006_synthetic_data
git show eaf300f:outputs/dec006_synthetic_data/product_domain_synth_train.jsonl > outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl
LINE_COUNT=$(wc -l < outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl)
echo "Training file has $LINE_COUNT lines (should be 90)"

DATA_PATH="outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl"

echo "=== Step 6: Train seeds 43-46 with the winning config (epochs=5, rank=16, alpha=32, lr=2e-4) ==="
for SEED in 43 44 45 46; do
  echo "--- Training seed $SEED ---"
  python scripts/dec006_lora_finetune.py --seed $SEED --epochs 5 \
    --data-path "$DATA_PATH" \
    --output-dir "outputs/dec022_stage3/seed_${SEED}"
done

echo "=== Step 7: Evaluate all 4 adapters ==="
for SEED in 43 44 45 46; do
  echo "--- Evaluating seed $SEED ---"
  python scripts/dec006_evaluate_adapter.py \
    --adapter "outputs/dec022_stage3/seed_${SEED}" \
    --training-data-path "$DATA_PATH"
done

echo "=== DONE ==="
echo "Copy the P/R/F1 lines printed above (for seeds 43, 44, 45, 46) and send them back to Claude."
echo "Then STOP THE POD to avoid burning remaining RunPod credit."
