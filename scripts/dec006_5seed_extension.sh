#!/usr/bin/env bash
# DEC-006 5-seed extension (completes DEC-006 steps 6-8, matching
# DEC-005's 5-seed convention for a properly powered statistical test).
#
# Seeds 42/43/44 already exist (EVID-028, leakage-safe, 90-example
# unfiltered training set). This trains and evaluates seeds 45 and 46
# on the SAME training data (product_domain_synth_train.jsonl was
# deliberately reverted to the unfiltered 90-example version for this
# run -- see the commit that did this) so all 5 seeds are directly
# comparable.
#
# Run this ONCE per rented pod, right after `git clone` + `pip install
# -q transformers peft trl accelerate bitsandbytes datasets`.
#
# Usage:
#   bash scripts/dec006_5seed_extension.sh

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

echo ""
echo "=== Sanity check: training data must be the UNFILTERED 90-example set ==="
N_EXAMPLES=$(wc -l < outputs/dec006_synthetic_data/product_domain_synth_train.jsonl)
echo "product_domain_synth_train.jsonl has $N_EXAMPLES lines (expected 90)"
if [ "$N_EXAMPLES" -ne 90 ]; then
    echo "!!! WRONG TRAINING DATA (expected 90 examples, got $N_EXAMPLES). Do not proceed."
    echo "git pull to get the reverted unfiltered version before running this."
    exit 1
fi

for SEED in 45 46; do
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
git commit -m "DEC-006 5-seed extension: seeds 45, 46 (unfiltered 90-example set)" || echo "(nothing new to commit)"
git push origin dec003-pkb-validation

echo ""
echo "=== DONE. Results below. Safe to Terminate the pod now. ==="
echo "--- Seed 45 ---"
cat outputs/dec006_eval/mistral7b_qlora_seed45/metrics.json
echo ""
echo "--- Seed 46 ---"
cat outputs/dec006_eval/mistral7b_qlora_seed46/metrics.json
