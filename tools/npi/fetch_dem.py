#!/usr/bin/env python3
"""Fetch AWS terrarium terrain tiles (keyless, ~30m at z12) for the Vic Goldfields
region. Cache to terrain_z12/. Idempotent: skips tiles already on disk."""
import math, os, sys, time, urllib.request, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "terrain_z12")
os.makedirs(CACHE, exist_ok=True)
Z = 12
# Regions (west, south, east, north) — generous around the 12 trip spots.
REGIONS = [
    (142.95, -37.60, 145.15, -36.05),   # western goldfields cluster (spots 1-11 + subs/camps)
    (146.30, -36.42, 146.72, -36.08),   # Chiltern-Mt Pilot / Eldorado (spot 12)
]
UA = {"User-Agent": "AuraGold-NPI-build/1.0 (offline prospecting PWA)"}

def lon2x(lon, z): return int((lon + 180.0) / 360.0 * (1 << z))
def lat2y(lat, z):
    r = math.radians(lat)
    return int((1.0 - math.asinh(math.tan(r)) / math.pi) / 2.0 * (1 << z))

tiles = set()
for (w, s, e, n) in REGIONS:
    x0, x1 = lon2x(w, Z), lon2x(e, Z)
    y0, y1 = lat2y(n, Z), lat2y(s, Z)   # north has smaller y
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            tiles.add((x, y))
tiles = sorted(tiles)
print(f"[fetch] {len(tiles)} z{Z} tiles across {len(REGIONS)} regions", flush=True)

def fetch(t):
    x, y = t
    path = os.path.join(CACHE, f"{x}_{y}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return ("cache", t)
    url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            return ("ok", t)
        except Exception as ex:
            if attempt == 3:
                return ("FAIL:" + str(ex), t)
            time.sleep(1.5 * (attempt + 1))

ok = cache = fail = 0
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for i, (status, t) in enumerate(ex.map(fetch, tiles)):
        if status == "ok": ok += 1
        elif status == "cache": cache += 1
        else:
            fail += 1
            print(f"[fetch] {status} {t}", flush=True)
        if (i + 1) % 100 == 0:
            print(f"[fetch] {i+1}/{len(tiles)} (ok={ok} cache={cache} fail={fail})", flush=True)
print(f"[fetch] DONE ok={ok} cache={cache} fail={fail} total={len(tiles)}", flush=True)
