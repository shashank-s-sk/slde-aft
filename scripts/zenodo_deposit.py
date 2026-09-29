"""Zenodo deposit for the submitted version (KBS research data policy,
Option C: mandatory deposit with a citation in the article).

Three explicit steps, so that nothing irreversible happens by accident:

  python -m scripts.zenodo_deposit create  [--sandbox]
      Creates a DRAFT deposition from paper/zenodo_metadata.json with a
      pre-reserved DOI, and writes the DOI and deposition id to
      paper/zenodo_state.json. The DOI can then go into the manuscript
      before the final commit. A draft can be deleted.

  python -m scripts.zenodo_deposit upload --commit <hash> [--sandbox]
      Builds `git archive` of that commit (raw third-party corpora
      excluded) and uploads it to the draft.

  python -m scripts.zenodo_deposit publish --i-confirm [--sandbox]
      PUBLISHES the record. IRREVERSIBLE: a published Zenodo record
      cannot be deleted. Run only after the authors approve.

The token is read from ZENODO_TOKEN in .env (git-ignored); it needs the
deposit:write and deposit:actions scopes. --sandbox uses
sandbox.zenodo.org (a separate account and token) for a dry run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

META = Path("paper/zenodo_metadata.json")
STATE = Path("paper/zenodo_state.json")
EXCLUDE = [":(exclude)data/BioRED/BioRED", ":(exclude)data/carb_dev_sample.jsonl"]


def token() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("ZENODO_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("ZENODO_TOKEN not set in .env")


def base(sandbox: bool) -> str:
    return "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"


def metadata() -> dict:
    meta = json.loads(META.read_text(encoding="utf-8"))
    meta.pop("_comment", None)
    missing = [k for k, v in meta.items() if "[NEEDED" in json.dumps(v)]
    if missing:
        sys.exit(f"fill in paper/zenodo_metadata.json first: {missing}")
    for c in meta["creators"]:
        if not c.get("orcid"):
            c.pop("orcid", None)
    meta["prereserve_doi"] = True
    return meta


def create(a):
    r = requests.post(f"{base(a.sandbox)}/deposit/depositions", params={"access_token": token()},
                      json={"metadata": metadata()}, timeout=60)
    r.raise_for_status()
    d = r.json()
    doi = d["metadata"]["prereserve_doi"]["doi"]
    STATE.write_text(json.dumps({"id": d["id"], "doi": doi, "bucket": d["links"]["bucket"],
                                 "sandbox": a.sandbox, "published": False}, indent=2), encoding="utf-8")
    print(f"draft created: id {d['id']}, reserved DOI {doi} (not yet public)")


def upload(a):
    st = json.loads(STATE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        zp = Path(tmp) / f"slde-aft-{a.commit[:7]}.zip"
        subprocess.run(["git", "archive", "--format=zip", "-o", str(zp), a.commit, "--", "."] + EXCLUDE, check=True)
        with open(zp, "rb") as f:
            r = requests.put(f"{st['bucket']}/{zp.name}", data=f, params={"access_token": token()}, timeout=3600)
        r.raise_for_status()
    st["commit"] = a.commit
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(f"uploaded {zp.name} ({r.json().get('size', 0) / 1e6:.1f} MB) to draft {st['id']}")


def publish(a):
    if not a.i_confirm:
        sys.exit("publishing is irreversible; rerun with --i-confirm after the authors approve")
    st = json.loads(STATE.read_text(encoding="utf-8"))
    r = requests.post(f"{base(st['sandbox'])}/deposit/depositions/{st['id']}/actions/publish",
                      params={"access_token": token()}, timeout=120)
    r.raise_for_status()
    st["published"] = True
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(f"PUBLISHED: https://doi.org/{st['doi']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["create", "upload", "publish"])
    ap.add_argument("--commit")
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--i-confirm", action="store_true")
    a = ap.parse_args()
    {"create": create, "upload": upload, "publish": publish}[a.step](a)


if __name__ == "__main__":
    main()
