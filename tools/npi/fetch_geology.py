#!/usr/bin/env python3
"""Fetch Vic 1:250k surface geology polygons (geol250_polygon) per region from the
DataVic open-data WFS, paginated past the 5000-feature cap. Keep only the geometry
+ the fields the lithology classifier needs. Cached to geology_<region>.geojson.

Lithology is the second half of the Mt Cole fix: Devonian granite/granodiorite
intrusions (e.g. 'Mount Cole Suite', 'Wedderburn Granodiorite') and Ordovician/Cambrian
turbidite metasediments are the favourable orogenic-gold hosts; Newer Volcanics basalt
and Murray-Basin Tertiary cover are unfavourable.
"""
import json, os, urllib.request, urllib.parse
import regions as R

HERE = os.path.dirname(os.path.abspath(__file__))
WFS = "https://opendata.maps.vic.gov.au/geoserver/open-data-platform/wfs"
TYPE = "open-data-platform:geol250_polygon"
KEEP = ("subtype", "unittype", "unitname", "parents", "rank",
        "ageyoungno", "ageoldno", "map_symb")
PAGE = 5000


def page(bbox, start):
    qs = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": TYPE, "outputFormat": "application/json", "srsName": "EPSG:4326",
        "count": str(PAGE), "startIndex": str(start),
        "CQL_FILTER": f"BBOX(geom,{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},'EPSG:4326')",
    }
    url = WFS + "?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": "AuraGold-NPI-build/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch(slug, w, s, e, n):
    out = os.path.join(HERE, "geology_" + slug + ".geojson")
    if os.path.exists(out):
        print(f"[geology] cache {out}", flush=True); return
    feats, start = [], 0
    while True:
        d = page((w, s, e, n), start)
        got = d.get("features", [])
        for f in got:
            props = {k: f["properties"].get(k) for k in KEEP}
            feats.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
        nmatch = d.get("numberMatched")
        start += len(got)
        print(f"[geology] {slug} {start} (matched={nmatch})", flush=True)
        if not got or (isinstance(nmatch, int) and start >= nmatch) or len(got) < PAGE:
            break
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"))
    print(f"[geology] DONE {slug} {len(feats)} polys -> {out} ({os.path.getsize(out)/1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    for slug, w, s, e, n in R.FETCH:
        fetch(slug, w, s, e, n)
    print("[geology] DONE", flush=True)
