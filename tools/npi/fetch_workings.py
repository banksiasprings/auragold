#!/usr/bin/env python3
"""Fetch the same VicMine gold occurrence points the app uses (for workings density).
Caches to workings.json (list of [lon,lat])."""
import json, os, urllib.request, urllib.parse
import regions as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "workings.json")
WFS = "https://opendata.maps.vic.gov.au/geoserver/open-data-platform/wfs"
# Union of the fetch regions, padded a touch — single source of truth (regions.py).
_W = min(r[1] for r in R.FETCH) - 0.1; _S = min(r[2] for r in R.FETCH) - 0.1
_E = max(r[3] for r in R.FETCH) + 0.1; _N = max(r[4] for r in R.FETCH) + 0.1
CQL = f"pri_comm LIKE 'Gold%' AND BBOX(geom,{_W:.2f},{_S:.2f},{_E:.2f},{_N:.2f},'EPSG:4326')"
PAGE = 5000

def page(start):
    qs = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": "open-data-platform:minsite", "outputFormat": "application/json",
        "srsName": "EPSG:4326", "propertyName": "geom",
        "count": str(PAGE), "startIndex": str(start), "CQL_FILTER": CQL,
    }
    url = WFS + "?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": "AuraGold-NPI-build/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

pts, start = [], 0
while True:
    d = page(start)
    feats = d.get("features", [])
    for f in feats:
        g = f.get("geometry") or {}
        c = g.get("coordinates")
        if c and len(c) >= 2:
            pts.append([round(c[0], 6), round(c[1], 6)])
    nmatch = d.get("numberMatched")
    start += len(feats)
    print(f"[workings] {start} fetched (matched={nmatch})", flush=True)
    if not feats or (isinstance(nmatch, int) and start >= nmatch) or len(feats) < PAGE:
        break

json.dump(pts, open(OUT, "w"))
print(f"[workings] DONE {len(pts)} points -> {OUT}", flush=True)
