#!/usr/bin/env python3
"""Fetch GA national geophysics grids per region via WCS as float GeoTIFFs
(PIL reads them as mode 'F' — no GDAL needed). Four real mineral-system signals:

  tmi : magmap_v7_2019_RTP          — TMI reduced-to-pole. High = ironstone/magnetite
                                       /hot ground (PI tolerant, VLF struggles).
  as  : magmap_v7_2019_VRTP_AS      — analytic signal. High = magnetic GRADIENT =
                                       structure (shears, contacts) = the gold control.
  k   : radmap_v4_2019_filtered_pctk — % potassium. Granitic / K-alteration signal.
  th  : radmap_v4_2019_filtered_ppmth — thorium ppm. Felsic host-rock / placer signal.

Cached to geophys_<region>.npz (one array per channel + the requested bbox). Global
p2/p98 normalisation is done at build time across ALL regions (build_npi), not here,
so the three detector variants stay comparable region-to-region (v35 fix).
"""
import os, sys, urllib.request, urllib.error, numpy as np
from PIL import Image
import regions as R

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
WCS = "https://services.ga.gov.au/gis/geophysical-grids/wcs"
CHANNELS = {
    "tmi": "geophys__magmap_v7_2019_RTP",
    "as":  "geophys__magmap_v7_2019_VRTP_AS",
    "k":   "geophys__radmap_v4_2019_filtered_pctk",
    "th":  "geophys__radmap_v4_2019_filtered_ppmth",
}


def get_tiff(cov, w, s, e, n, dst):
    url = (WCS + "?service=WCS&version=2.0.1&request=GetCoverage&coverageId=" + cov +
           f"&subset=Lat({s},{n})&subset=Long({w},{e})&format=image/tiff")
    req = urllib.request.Request(url, headers={"User-Agent": "AuraGold-NPI-build/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=240) as r, open(dst, "wb") as f:
                f.write(r.read())
            return
        except (urllib.error.URLError, TimeoutError) as ex:
            if attempt == 3:
                raise
            print(f"    retry {attempt+1} ({ex})", flush=True)


def fetch(slug, w, s, e, n):
    out = os.path.join(HERE, "geophys_" + slug + ".npz")
    if os.path.exists(out):
        print(f"[geophys] cache {out}", flush=True); return
    data = {"bbox": np.array([w, s, e, n], np.float64)}
    for key, cov in CHANNELS.items():
        tif = os.path.join(HERE, f"_{slug}_{key}.tif")
        print(f"[geophys] {slug}/{key} <- {cov}", flush=True)
        get_tiff(cov, w, s, e, n, tif)
        a = np.asarray(Image.open(tif)).astype(np.float32)
        a = np.where(np.isfinite(a), a, np.nan)
        finite = a[np.isfinite(a)]
        lo = float(np.nanmin(finite)) if finite.size else float("nan")
        hi = float(np.nanmax(finite)) if finite.size else float("nan")
        print(f"           {a.shape}  range [{lo:.3f}, {hi:.3f}]  valid {finite.size/a.size:.0%}", flush=True)
        data[key] = a
        os.remove(tif)
    np.savez_compressed(out, **data)
    print(f"[geophys] saved {out} ({os.path.getsize(out)/1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    for slug, w, s, e, n in R.FETCH:
        fetch(slug, w, s, e, n)
    print("[geophys] DONE", flush=True)
