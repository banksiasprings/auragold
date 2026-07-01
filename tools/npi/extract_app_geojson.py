#!/usr/bin/env python3
"""Extract the goldfield + endowment + fire GeoJSON the app already ships (inline in
index.html) into standalone files the NPI build reads. Keeps the build reproducible
from the repo alone (no manual copy-paste). Run before build_npi.py.

dataGoldfields / dataEndowment = the official Vic goldfield + endowment polygons that
drive the goldfield prior (replaces the old hardcoded distance term, v35).
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "..", "..", "index.html")
WANT = [("dataGoldfields", "dataGoldfields.geojson"),
        ("dataEndowment", "dataEndowment.geojson")]


def main():
    src = open(INDEX).read()
    for var, out in WANT:
        m = re.search(r"const\s+" + var + r"\s*=\s*(\{.*?\});", src, re.S)
        if not m:
            raise SystemExit(f"[extract] {var} not found in index.html")
        obj = json.loads(m.group(1))
        json.dump(obj, open(os.path.join(HERE, out), "w"))
        print(f"[extract] {out}: {len(obj['features'])} features", flush=True)


if __name__ == "__main__":
    main()
