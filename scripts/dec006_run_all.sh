#!/usr/bin/env bash
# DEC-006 one-shot GPU runner. Run this ONCE per rented pod, right after
# `git clone` + `pip install -q transformers peft trl accelerate bitsandbytes datasets`.
#
# It fails fast (before any model download) if the pod's GPU passthrough
# is broken — the exact failure mode hit on pod yzalh0cgl6qf4p, see
# dec006_runpod_plan memory — so a bad host costs you ~5 seconds, not
# 15-20 minutes of a stuck CPU fallback.
#
# On success it trains the adapter, evaluates base vs. fine-tuned,
# prints both F1 lines, and commits+pushes the results to GitHub so
# nothing depends on scp/manual file transfer before you terminate.
#
# Usage:
#   bash scripts/dec006_run_all.sh

set -e

# scripts/ importing `src...` needs the repo root on PYTHONPATH — python
# only puts the script's own directory (scripts/) on sys.path by default.
export PYTHONPATH="$(pwd)"

echo "=== Step 0/4: GPU sanity check ==="
if ! python3 -c "
import torch, sys
ok = torch.cuda.is_available()
print(f'torch {torch.__version__} (cuda {torch.version.cuda}) -> cuda.is_available() = {ok}')
sys.exit(0 if ok else 1)
"; then
    echo ""
    echo "!!! NO GPU VISIBLE TO TORCH. Do not proceed. !!!"
    echo "This pod's GPU passthrough is broken (known RunPod host issue - see"
    echo "dec006_runpod_plan memory). Terminate this pod now and deploy a fresh"
    echo "one instead of debugging further."
    exit 1
fi
echo "GPU OK, proceeding."
echo ""

echo "=== Step 1/4: Train QLoRA adapter (Mistral-7B, 3 epochs) ==="
python scripts/dec006_lora_finetune.py

echo ""
echo "=== Step 2/4: Evaluate base model (before) ==="
python scripts/dec006_evaluate_adapter.py

echo ""
echo "=== Step 3/4: Evaluate fine-tuned adapter (after) ==="
python scripts/dec006_evaluate_adapter.py --adapter outputs/dec006_adapters/mistral7b_qlora

echo ""
echo "=== Step 4/4: Save results to GitHub ==="
git add -f outputs/dec006_adapters outputs/dec006_eval
git commit -m "DEC-006 GPU run: Mistral-7B QLoRA adapter + eval results" || echo "(nothing new to commit)"
git push origin dec003-pkb-validation

echo ""
echo "=== DONE. Results below. Safe to Terminate the pod now. ==="
echo "--- Base model ---"
cat outputs/dec006_eval/base_model/metrics.json
echo ""
echo "--- Fine-tuned adapter ---"
cat outputs/dec006_eval/mistral7b_qlora/metrics.json
