#!/usr/bin/env python3
"""Fetch Vic DELWP fire history perimeters (fire_history) per region from the DataVic
open-data WFS, filtered to RECENT seasons (fresh ground exposure). Cached to
fire_<region>.geojson with season + firetype so the build can apply a recency-weighted
fresh-exposure multiplier.

NOTE (honest): this is the perimeter-and-recency proxy, not per-pixel Sentinel-2 NBR
burn severity — computing NBR from Sentinel-2 COGs needs rasterio/gdal, which the
build environment doesn't have. Bushfires (uncontrolled, hot) are weighted above
planned fuel-reduction burns; the most recent fires get the biggest multiplier.
"""
import json, os, urllib.request, urllib.parse
import regions as R

HERE = os.path.dirname(os.path.abspath(__file__))
WFS = "https://opendata.maps.vic.gov.au/geoserver/open-data-platform/wfs"
TYPE = "open-data-platform:fire_history"
SINCE = 2008          # only seasons >= this (recent fresh exposure)
KEEP = ("season", "firetype", "fire_cover", "area_ha")
PAGE = 5000


def page(bbox, start):
    cql = (f"season>={SINCE} AND "
           f"BBOX(geom,{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},'EPSG:4326')")
    qs = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": TYPE, "outputFormat": "application/json", "srsName": "EPSG:4326",
        "count": str(PAGE), "startIndex": str(start), "CQL_FILTER": cql,
    }
    url = WFS + "?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": "AuraGold-NPI-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch(slug, w, s, e, n):
    out = os.path.join(HERE, "fire_" + slug + ".geojson")
    if os.path.exists(out):
        print(f"[fire] cache {out}", flush=True); return
    feats, start = [], 0
    while True:
        d = page((w, s, e, n), start)
        got = d.get("features", [])
        for f in got:
            props = {k: f["properties"].get(k) for k in KEEP}
            feats.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
        nmatch = d.get("numberMatched")
        start += len(got)
        print(f"[fire] {slug} {start} (matched={nmatch})", flush=True)
        if not got or (isinstance(nmatch, int) and start >= nmatch) or len(got) < PAGE:
            break
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"))
    seasons = sorted({f["properties"]["season"] for f in feats if f["properties"].get("season")})
    print(f"[fire] DONE {slug} {len(feats)} perimeters, seasons {seasons[:3]}..{seasons[-3:]} -> {out}", flush=True)


if __name__ == "__main__":
    for slug, w, s, e, n in R.FETCH:
        fetch(slug, w, s, e, n)
    print("[fire] DONE", flush=True)
