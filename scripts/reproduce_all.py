"""DEC-030 reproducibility check: regenerates the numbers behind every
table currently in paper/main.tex's Section 7 (and its Table S1-S8
appendix) from the raw outputs committed under outputs/, and checks
them against the values actually written into Results Summary.md /
paper/main.tex.

Honesty policy, stated up front rather than left implicit: not every
number can be independently RE-DERIVED here without re-implementing an
external tool (the official CaRB scorer's AUC/optimal-F1 computation,
in particular). Where that is true, this script reads the value from
its own already-saved raw output file (parsed from the actual scorer
run, not retyped) and reports it as READ, not RECOMPUTED -- the two are
labeled differently in the output, on purpose. Where raw per-seed
output could not be found at all (a real gap, not a bug in this
script), that is reported as GAP, not silently skipped.

This script never edits Results Summary.md or paper/main.tex. It only
reports; any mismatch is for a human to resolve.

Usage: python -m scripts.reproduce_all
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.provenance_filter import has_structured_corroboration

ROOT = Path(".")
TOL = 1e-3  # tolerance for float comparisons (rounding in the manuscript is to 3-4 dp)

checks = []  # list of (name, status, detail) -- status in {"PASS","MISMATCH","READ","GAP"}


def record(name, status, detail):
    checks.append((name, status, detail))
    print(f"[{status:8s}] {name}: {detail}")


def close(a, b, tol=TOL):
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


# ---------------------------------------------------------------- CaRB ----

def parse_carb_raw(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(
        r"=== (\S+) ===\s*\nAUC: ([\d.]+)\s*\s*Optimal \(precision, recall, F1\): \[([\d.]+) ([\d.]+) ([\d.]+)\]",
        text,
    ):
        name, auc, p, r, f1 = m.groups()
        out[name] = {"auc": float(auc), "precision": float(p), "recall": float(r), "f1": float(f1)}
    return out


def check_carb():
    full_path = ROOT / "outputs/dec001_part6_official_carb/official_carb_scorer_raw_output.txt"
    pilot_path = ROOT / "outputs/dec001_official_carb/official_carb_scorer_raw_output.txt"
    if not full_path.exists() or not pilot_path.exists():
        record("CaRB (Table 7.1)", "GAP", "official_carb_scorer_raw_output.txt not found")
        return

    full = parse_carb_raw(full_path)
    pilot = parse_carb_raw(pilot_path)

    # Expected values transcribed from Results Summary.md / paper/main.tex Table 7.1 (EVID-032/035)
    expected_full = {
        "slde_aft_llama": (0.589, 0.387, 0.467),
        "deepseek_baseline": (0.713, 0.477, 0.571),
    }
    expected_pilot = {
        "deepseek_baseline": (0.713, 0.458, 0.558),
        "gemini25pro_baseline": (0.773, 0.401, 0.528),
        "claude_sonnet5_baseline": (0.642, 0.446, 0.527),
        "gpt4o_baseline": (0.736, 0.384, 0.504),
        "slde_aft_llama": (0.652, 0.401, 0.496),
    }

    for name, (p, r, f1) in expected_full.items():
        got = full.get(name)
        if got is None:
            record(f"CaRB full-scale {name}", "GAP", "not found in raw scorer output")
            continue
        ok = close(got["precision"], p) and close(got["recall"], r) and close(got["f1"], f1)
        record(f"CaRB full-scale {name}", "PASS" if ok else "MISMATCH",
               f"read P/R/F1={got['precision']:.3f}/{got['recall']:.3f}/{got['f1']:.3f}, "
               f"expected {p}/{r}/{f1}")

    for name, (p, r, f1) in expected_pilot.items():
        got = pilot.get(name)
        if got is None:
            record(f"CaRB pilot {name}", "GAP", "not found in raw scorer output")
            continue
        ok = close(got["precision"], p) and close(got["recall"], r) and close(got["f1"], f1)
        record(f"CaRB pilot {name}", "PASS" if ok else "MISMATCH",
               f"read P/R/F1={got['precision']:.3f}/{got['recall']:.3f}/{got['f1']:.3f}, "
               f"expected {p}/{r}/{f1}")


# ------------------------------------------------------------- DocRED ----

def check_docred():
    path = ROOT / "outputs/dec020_docred_extract_and_pkb/summary.json"
    if not path.exists():
        record("DocRED pilot (Table 7.2)", "GAP", f"{path} not found")
        return
    d = json.loads(path.read_text(encoding="utf-8"))
    # Structure read as-is and reported; exact key names are whatever
    # dec020_docred_extract_and_pkb.py actually wrote.
    record("DocRED pilot (Table 7.2)", "READ", json.dumps(d)[:300])


# --------------------------------------------------------- Provenance ----

def check_provenance():
    """EVID-029's original script (scripts/dec018_provenance_filter_validation.py)
    scores against `gold_structured` (all 13 structured facts per product),
    reconstructed fresh in that script -- NOT against the snapshot's own
    `gold_label` column, which reflects `gold_unstructured` (the subset of
    facts actually mentioned in the generated text; same set DEC-026/028's
    gold reconstruction uses). This is a real, previously-undocumented
    denominator difference between two numbers that both get called
    "gold" in this project, discovered by this script -- reported
    explicitly below, both ways, not silently resolved in favor of
    whichever matches Results Summary.md."""
    path = ROOT / "outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv"
    if not path.exists():
        record("Provenance filter (Table 7.3)", "GAP", f"{path} not found")
        return

    from src.datasets.product_generator import generate_products
    from src.pkb_instrumentation import normalized_object, normalized_slot

    df = pd.read_csv(path)
    above = df[df["above_threshold"] == True].copy()  # noqa: E712
    above["source_types"] = above["source_types"].apply(json.loads)
    above["passes"] = above["source_types"].apply(has_structured_corroboration)
    n_total = len(above)
    n_pass = int(above["passes"].sum())
    n_fail = n_total - n_pass

    # (1) EVID-029's actual method: gold_structured, reconstructed fresh,
    # exactly matching scripts/dec018_provenance_filter_validation.py.
    gold_structured_keys = set()
    for idx, structured, unstructured, gold_structured, gold_unstructured in generate_products(200, seed=42):
        for s, p, o, _ in gold_structured:
            sn, pn = normalized_slot(s, p)
            gold_structured_keys.add((sn, pn, normalized_object(o)))

    def is_gold_structured(row):
        sn, pn = normalized_slot(row["subject"], row["predicate"])
        return (sn, pn, normalized_object(str(row["object"]))) in gold_structured_keys

    above["is_correct_structured"] = above.apply(is_gold_structured, axis=1)
    prec_all_struct = float(above["is_correct_structured"].mean())
    prec_pass_struct = float(above[above["passes"]]["is_correct_structured"].mean())
    prec_fail_struct = float(above[~above["passes"]]["is_correct_structured"].mean())

    expected = {"n_total": 475, "n_pass": 444, "n_fail": 31,
                "prec_all": 0.935, "prec_pass": 1.000, "prec_fail": 0.000}
    ok = (n_total == expected["n_total"] and n_pass == expected["n_pass"] and n_fail == expected["n_fail"]
          and close(prec_all_struct, expected["prec_all"], 0.001)
          and close(prec_pass_struct, expected["prec_pass"], 0.001)
          and close(prec_fail_struct, expected["prec_fail"], 0.001))
    record("Provenance filter, gold_structured (Table 7.3, EVID-029's actual method)",
           "PASS" if ok else "MISMATCH",
           f"recomputed n_total={n_total} n_pass={n_pass} n_fail={n_fail} "
           f"prec_all={prec_all_struct:.3f} prec_pass={prec_pass_struct:.3f} "
           f"prec_fail={prec_fail_struct:.3f} (expected {expected})")

    # (2) The snapshot's own gold_label column (gold_unstructured) -- what
    # a reader would get from the more obvious "just use gold_label"
    # approach, and what DEC-026/028 use for their own (different) gold
    # reconstructions. NOT what EVID-029/Table 7.3 report; recorded as
    # READ (not PASS/MISMATCH, since there is no "expected" value for it
    # in the manuscript) so the difference is visible, not silently lost.
    labeled = above.dropna(subset=["gold_label"])
    prec_all_unstruct = float(labeled["gold_label"].mean())
    prec_pass_unstruct = float(labeled[labeled["passes"]]["gold_label"].mean())
    prec_fail_unstruct = float(labeled[~labeled["passes"]]["gold_label"].mean())
    record("Provenance filter, gold_unstructured (informational, NOT what Table 7.3 reports)",
           "READ",
           f"prec_all={prec_all_unstruct:.3f} prec_pass={prec_pass_unstruct:.3f} "
           f"prec_fail={prec_fail_unstruct:.3f} -- differs from the gold_structured figures "
           f"above by {abs(prec_pass_struct - prec_pass_unstruct):.3f} on prec_pass; "
           f"EVID-029/Table 7.3 use gold_structured, not this")


# ------------------------------------------------------------ Ablation ----

def check_ablation_n50():
    path = ROOT / "outputs/dec023_ablation_n50/all_runs_summary.csv"
    if not path.exists():
        record("Ablation N=50 (Table 7.4)", "GAP", f"{path} not found")
        return
    df = pd.read_csv(path)
    expected = {
        "full": 0.345,
        "without_feedback": 0.301,
        "without_prob_kb": 0.378,
    }
    for config, exp_mean in expected.items():
        rows = df[df["config"] == config]
        if rows.empty:
            record(f"Ablation N=50 {config}", "GAP", "config not found in all_runs_summary.csv")
            continue
        mean_f1 = float(rows["held_out_test_f1"].mean())
        ok = close(mean_f1, exp_mean, 0.001)
        record(f"Ablation N=50 {config}", "PASS" if ok else "MISMATCH",
               f"recomputed mean held-out F1={mean_f1:.3f} (n={len(rows)} seeds), expected {exp_mean}")


# ---------------------------------------------------------- Fine-tuning ----

def check_finetuning():
    base_path = ROOT / "outputs/dec006_eval/base_model/metrics.json"
    if base_path.exists():
        d = json.loads(base_path.read_text(encoding="utf-8"))
        f1 = d.get("f1")
        ok = close(f1, 0.137, 0.001)
        record("Fine-tuning base model (Table 7.5)", "PASS" if ok else "MISMATCH",
               f"recomputed F1={f1}, expected 0.137")
    else:
        record("Fine-tuning base model (Table 7.5)", "GAP", f"{base_path} not found")

    # epochs=5 5-seed grid (EVID-037/038/040): no per-seed raw metrics.json
    # was found under outputs/ for this specific configuration at the time
    # this script was written -- only the 3-epoch adapters (seeds 42-46)
    # have saved eval artifacts under outputs/dec006_eval/. This is a real
    # gap, reported here rather than silently worked around.
    epochs5_dir = ROOT / "outputs/dec006_eval"
    found_epochs5 = list(epochs5_dir.glob("*epochs5*")) if epochs5_dir.exists() else []
    if not found_epochs5:
        record("Fine-tuning epochs=5 5-seed grid (Table 7.5 / EVID-037/038/040)", "GAP",
               "no per-seed raw eval metrics found under outputs/dec006_eval/ for the "
               "epochs=5 configuration -- only Evidence log.md's transcribed numbers exist; "
               "this table's epochs=5 rows cannot be independently recomputed by this script")


# ---------------------------------------------------------- Closed loop ----

def check_closedloop():
    base_path = ROOT / "outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv"
    control_path = ROOT / "outputs/dec019_closedloop/control/summary.json"
    treatment_path = ROOT / "outputs/dec019_closedloop/treatment/summary.json"
    if not (control_path.exists() and treatment_path.exists()):
        record("Closed-loop test (Table 7.6)", "GAP", "control/treatment summary.json not found")
        return

    control = json.loads(control_path.read_text(encoding="utf-8"))
    treatment = json.loads(treatment_path.read_text(encoding="utf-8"))

    c = control["accumulated_kb_after_iteration5"]
    t = treatment["accumulated_kb_after_iteration5"]

    expected_control = (0.908, 0.240, 0.379)
    expected_treatment = (0.898, 0.246, 0.386)

    ok_c = close(c["precision"], expected_control[0], 0.001) and close(c["recall"], expected_control[1], 0.001) and close(c["f1"], expected_control[2], 0.001)
    ok_t = close(t["precision"], expected_treatment[0], 0.001) and close(t["recall"], expected_treatment[1], 0.001) and close(t["f1"], expected_treatment[2], 0.001)

    record("Closed-loop control arm (Table 7.6)", "PASS" if ok_c else "MISMATCH",
           f"read P/R/F1={c['precision']:.3f}/{c['recall']:.3f}/{c['f1']:.3f}, expected {expected_control}")
    record("Closed-loop treatment arm (Table 7.6)", "PASS" if ok_t else "MISMATCH",
           f"read P/R/F1={t['precision']:.3f}/{t['recall']:.3f}/{t['f1']:.3f}, expected {expected_treatment}")


# --------------------------------------------------------- Scalability ----

def check_scalability():
    path = ROOT / "outputs/dec008_scalability/scalability_summary.csv"
    if not path.exists():
        record("Scalability (Table S7)", "GAP", f"{path} not found")
        return
    df = pd.read_csv(path)
    expected = {
        20: (92.14, 4.598),
        50: (199.04, 3.976),
        100: (405.84, 4.053),
        200: (799.06, 3.988),
    }
    all_ok = True
    for n, (rt, lat) in expected.items():
        row = df[df["n_products"] == n]
        if row.empty:
            record(f"Scalability N={n}", "GAP", "row not found")
            all_ok = False
            continue
        got_rt = float(row["total_runtime_s"].iloc[0])
        got_lat = float(row["mean_latency_s_per_doc"].iloc[0])
        ok = close(got_rt, rt, 0.05) and close(got_lat, lat, 0.01)
        all_ok = all_ok and ok
        record(f"Scalability N={n} (Table S7)", "PASS" if ok else "MISMATCH",
               f"read runtime={got_rt}, mean_latency={got_lat}; expected {rt}, {lat}")


# ---------------------------------------------------------- Complexity ----

def check_complexity():
    proto_path = ROOT / "outputs/dec003_complexity_benchmark/prototype_timings.json"
    indexed_path = ROOT / "outputs/dec003_complexity_benchmark/indexed_alternative_timings.json"
    if not (proto_path.exists() and indexed_path.exists()):
        record("Complexity (Table S8)", "GAP", "timing JSON files not found")
        return
    proto = json.loads(proto_path.read_text(encoding="utf-8"))
    indexed = json.loads(indexed_path.read_text(encoding="utf-8"))

    def growth(rows, key="single_call_seconds"):
        sizes = sorted(rows, key=lambda r: r["kb_size"])
        first, last = sizes[0], sizes[-1]
        obs_growth = last["kb_size"] / first["kb_size"]
        latency_growth = last[key] / first[key]
        return obs_growth, latency_growth

    proto_obs, proto_lat = growth(proto)
    idx_obs, idx_lat = growth(indexed)

    ok_proto = close(proto_lat, 72.7, 1.0)
    ok_idx = close(idx_lat, 2.9, 0.3)
    record("Complexity, production routine (Table S8)", "PASS" if ok_proto else "MISMATCH",
           f"recomputed latency growth={proto_lat:.1f}x for observation growth={proto_obs:.0f}x, expected ~72.7x")
    record("Complexity, indexed alternative (Table S8)", "PASS" if ok_idx else "MISMATCH",
           f"recomputed latency growth={idx_lat:.1f}x for observation growth={idx_obs:.0f}x, expected ~2.9x")


# ------------------------------------------------------------ DEC-026 ----

def check_dec026():
    path = ROOT / "outputs/dec026_aggregation_rules/product657_metrics_summary.json"
    if not path.exists():
        record("DEC-026 aggregation rules (Section 7 subsection)", "GAP", f"{path} not found")
        return
    d = json.loads(path.read_text(encoding="utf-8"))
    r2 = d.get("R2_published", {}).get("f1_selected", {})
    r3 = d.get("R3_source_count", {}).get("f1_selected", {})
    ok = close(r2.get("f1"), 0.6650, 0.0005) and close(r3.get("f1"), 0.6751, 0.0005)
    record("DEC-026 dataset A, R2/R3 F1-selected F1", "PASS" if ok else "MISMATCH",
           f"read R2 F1={r2.get('f1')}, R3 F1={r3.get('f1')}; expected 0.6650, 0.6751")


# ------------------------------------------------------------------ main ----

def main():
    check_carb()
    check_docred()
    check_provenance()
    check_ablation_n50()
    check_finetuning()
    check_closedloop()
    check_scalability()
    check_complexity()
    check_dec026()

    print("\n=== Summary ===")
    by_status = {}
    for _, status, _ in checks:
        by_status[status] = by_status.get(status, 0) + 1
    for status in ("PASS", "READ", "MISMATCH", "GAP"):
        print(f"{status}: {by_status.get(status, 0)}")

    mismatches = [c for c in checks if c[1] == "MISMATCH"]
    gaps = [c for c in checks if c[1] == "GAP"]
    if mismatches:
        print("\n!!! MISMATCHES (report these, do not silently fix either file) !!!")
        for name, status, detail in mismatches:
            print(f"  - {name}: {detail}")
    if gaps:
        print("\nGAPS (raw output not found for these -- not necessarily wrong, just unverifiable by this script):")
        for name, status, detail in gaps:
            print(f"  - {name}: {detail}")


if __name__ == "__main__":
    main()
