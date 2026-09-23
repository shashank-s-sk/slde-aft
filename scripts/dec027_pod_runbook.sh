#!/bin/bash
# DEC-027 pod runbook: leakage-free fine-tuning evaluation.
# Run this ON a freshly rented RunPod GPU pod (RTX 4090, fall back to
# 3090 if GPU passthrough fails), as a whole script with:
#   bash dec027_pod_runbook.sh
#
# Estimated GPU wall-clock: 35-45 minutes (Decision log.md DEC-027 cost
# estimate). After it finishes: copy/commit
# outputs/dec027_leakage_free_finetuning/ and outputs/dec006_eval/ back
# to your own machine (e.g. `git add`, commit, push from the pod, or
# scp/rsync the two directories off), send them back, then STOP THE POD
# to avoid burning remaining credit.

set -e  # stop on first real error rather than silently continuing

echo "=== Step 1: GPU sanity check ==="
nvidia-smi
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
echo "If the line above did not say True, STOP here, terminate this pod, and deploy a fresh one instead of continuing."
read -p "Press Enter once you've confirmed CUDA is True..."

echo "=== Step 2: Clone and checkout ==="
git clone https://github.com/shashank-s-sk/slde-aft.git
cd slde-aft
git checkout q1-rework

echo "=== Step 3: Install dependencies ==="
pip install -q -r requirements.txt -r requirements-finetune.txt

echo "=== Step 4: Set PYTHONPATH ==="
export PYTHONPATH=$(pwd)

echo "=== Step 5: Confirm the training data is present (should already be committed) ==="
DATA_PATH="outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl"
if [ ! -f "$DATA_PATH" ]; then
  echo "ERROR: $DATA_PATH not found after checkout. This file should already be committed"
  echo "to q1-rework (2026-09-22 commit 'Commit the 90-example unfiltered synthetic training"
  echo "set for DEC-025'). Do not regenerate it from a different snapshot -- stop and report"
  echo "this instead."
  exit 1
fi
LINE_COUNT=$(wc -l < "$DATA_PATH")
echo "Training file has $LINE_COUNT lines (should be 90)."

echo "=== Step 6: run the full DEC-027 orchestration (leakage guard, epoch grid, LoRA grid, confirmatory run, base eval) ==="
python scripts/dec027_pod_run.py

echo "=== DONE ==="
echo "Copy/commit outputs/dec027_leakage_free_finetuning/ and outputs/dec006_eval/ back,"
echo "then STOP THE POD to avoid burning remaining RunPod credit."
