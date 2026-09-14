#!/usr/bin/env bash
# DEC-006 multi-seed confirmation run (DEC-006 steps 6-8).
#
# EVID-027's positive result (F1 0.3231 -> 0.3958, 90-example training
# set) was a single run at seed 42 (the previously-implicit HF default).
# This script trains and evaluates two more seeds (43, 44) on the SAME
# 90-example training set and hyperparameters, to check the improvement
# direction replicates rather than being a one-seed fluke.
#
# The base model is NOT re-evaluated per seed -- it's deterministic
# (greedy decoding, do_sample=False), so seed 42's base_model/metrics.json
# already IS every seed's "before" number. Only the fine-tuned adapter
# changes per seed.
#
# Run this ONCE per rented pod, right after `git clone` + `pip install
# -q transformers peft trl accelerate bitsandbytes datasets`.
#
# Usage:
#   bash scripts/dec006_multiseed_run.sh

set -e

export PYTHONPATH="$(pwd)"

echo "=== Step 0: GPU sanity check ==="
if ! python3 -c "
import torch, sys
ok = torch.cuda.is_available()
print(f'torch {torch.__version__} (cuda {torch.version.cuda}) -> cuda.is_available() = {ok}')
sys.exit(0 if ok else 1)
"; then
    echo ""
    echo "!!! NO GPU VISIBLE TO TORCH. Do not proceed. !!!"
    echo "Terminate this pod now and deploy a fresh one instead of debugging further."
    exit 1
fi
echo "GPU OK, proceeding."

for SEED in 43 44; do
    echo ""
    echo "=== Seed $SEED: train ==="
    python scripts/dec006_lora_finetune.py --seed $SEED

    echo ""
    echo "=== Seed $SEED: evaluate ==="
    python scripts/dec006_evaluate_adapter.py --adapter outputs/dec006_adapters/mistral7b_qlora_seed$SEED
done

echo ""
echo "=== Save all results to GitHub ==="
git add -f outputs/dec006_adapters outputs/dec006_eval
git commit -m "DEC-006 multi-seed confirmation: seeds 43, 44 (90-example training set)" || echo "(nothing new to commit)"
git push origin dec003-pkb-validation

echo ""
echo "=== DONE. Results below (seed 42 is EVID-027's existing result). Safe to Terminate the pod now. ==="
echo "--- Base model (same for all seeds, deterministic) ---"
cat outputs/dec006_eval/base_model/metrics.json
echo ""
echo "--- Seed 42 (existing, EVID-027) ---"
cat outputs/dec006_eval/mistral7b_qlora/metrics.json
echo ""
echo "--- Seed 43 ---"
cat outputs/dec006_eval/mistral7b_qlora_seed43/metrics.json
echo ""
echo "--- Seed 44 ---"
cat outputs/dec006_eval/mistral7b_qlora_seed44/metrics.json
