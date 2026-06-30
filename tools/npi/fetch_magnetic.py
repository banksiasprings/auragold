#!/usr/bin/env python3
"""Fetch GA magnetic TMI-RTP grid (magmap_v7_2019_RTP) per region via WCS as a float
GeoTIFF (PIL reads it as mode 'F' — no GDAL). Real mineralization proxy: high magnetic
= ironstone / magnetite / hot ground (PI loves it, VLF hates it). Cache to mag_<region>.npz
with the bbox so the build can resample it onto the NPI grid."""
import os, json, urllib.request, numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WCS = "https://services.ga.gov.au/gis/geophysical-grids/wcs"
COV = "geophys__magmap_v7_2019_RTP"
# (name, west, south, east, north) — must match build_npi.REGIONS (padded a touch)
REGIONS = [
    ("western", 142.90, -37.65, 145.20, -36.00),
    ("chiltern-eldorado", 146.25, -36.47, 146.77, -36.03),
]

def fetch(name, w, s, e, n):
    out = os.path.join(HERE, "mag_" + name + ".npz")
    if os.path.exists(out):
        print(f"[mag] cache {out}", flush=True); return
    url = (WCS + "?service=WCS&version=2.0.1&request=GetCoverage&coverageId=" + COV +
           f"&subset=Lat({s},{n})&subset=Long({w},{e})&format=image/tiff")
    tif = os.path.join(HERE, "mag_" + name + ".tif")
    req = urllib.request.Request(url, headers={"User-Agent": "AuraGold-NPI-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tif, "wb") as f:
        f.write(r.read())
    a = np.asarray(Image.open(tif)).astype(np.float32)
    a = np.where(np.isfinite(a), a, np.nan)
    print(f"[mag] {name} {a.shape} nT [{np.nanmin(a):.0f},{np.nanmax(a):.0f}]", flush=True)
    np.savez_compressed(out, mag=a, bbox=np.array([w, s, e, n], np.float64))

for r in REGIONS:
    fetch(*r)
print("[mag] DONE", flush=True)
