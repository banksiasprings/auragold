#!/usr/bin/env python3
"""
AuraGold NPI build — Nugget Potential Index heatmap pipeline.

Inputs (all free / Australia-licensed):
  - DEM: AWS terrarium terrain tiles (z12 ~30 m), keyless. SRTM-derived globally.
  - Reef polygons: dataGoldfields + dataEndowment (extracted from the app).
  - Workings: VicMine gold occurrence points (same WFS the app uses).

Derives per cell: slope, convex curvature (bedrock proxy), D8 flow accumulation
(drainage), distance-to-reef, workings density. Combines per the v0 heuristic:

  NPI = 0.35*dist_to_reef + 0.25*workings + 0.15*drainage + 0.15*slope + 0.10*bedrock

Outputs:
  data/npi/{z}/{x}/{y}.png  — RdYlGn heatmap tiles z10-12 (browser upsamples 13-14)
  data/npi/npi-grid.png     — packed component grid (z8 ~490 m cells) for tap-to-explain
  data/npi/npi-meta.json    — bbox, grid geo-referencing, weights, limitations
"""
import json, math, os, sys, heapq
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/Users/openclaw/Documents/auragold"
TERRAIN = os.path.join(HERE, "terrain_z12")
OUT = os.path.join(REPO, "data", "npi")
Z = 12
R_EARTH = 6378137.0
WORLD = 2 * math.pi * R_EARTH  # 40075016.69

WEIGHTS = dict(dist_reef=0.35, workings=0.25, drainage=0.15, slope=0.15, bedrock=0.10)
NPI_FLOOR = 6           # below this -> transparent (negligible potential)
REGIONS = [
    ("Western goldfields", 142.95, -37.60, 145.15, -36.05),
    ("Chiltern-Eldorado",  146.30, -36.42, 146.72, -36.08),
]
# 12 trip spots for the report sanity-check
SPOTS = [
    (1, "Mount Cole / Bayindeen", -37.2670, 143.2920), (2, "Avoca / Pyrenees", -37.0900, 143.5000),
    (3, "Tarnagulla / Waanyarra", -36.7300, 143.8230), (4, "Talbot / Daisy Hill", -37.1850, 143.7050),
    (5, "Heathcote / McIvor", -36.9270, 144.7050), (6, "Whroo / Rushworth", -36.8600, 145.0080),
    (7, "Inglewood / Kingower", -36.5670, 143.8740), (8, "Hepburn / Sailors Ck", -37.3550, 144.1500),
    (9, "Maldon / Muckleford", -37.0010, 144.0700), (10, "WEDDERBURN (HEADLINE)", -36.4170, 143.6200),
    (11, "Wombat / Bullarook", -37.4500, 144.1000), (12, "Chiltern / Eldorado", -36.2000, 146.5170),
]

# ---------- web-mercator helpers ----------
def lon2px(lon, z): return (lon + 180.0) / 360.0 * 256.0 * (1 << z)
def lat2px(lat, z):
    s = math.sin(math.radians(lat)); s = min(max(s, -0.9999), 0.9999)
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * 256.0 * (1 << z)
def lon2tile(lon, z): return int(math.floor(lon2px(lon, z) / 256.0))
def lat2tile(lat, z): return int(math.floor(lat2px(lat, z) / 256.0))

# ---------- 1. load terrarium tiles -> elevation mosaic ----------
def load_mosaic(w, s, e, n):
    xmin, xmax = lon2tile(w, Z), lon2tile(e, Z)
    ymin, ymax = lat2tile(n, Z), lat2tile(s, Z)
    W = (xmax - xmin + 1) * 256; H = (ymax - ymin + 1) * 256
    elev = np.full((H, W), np.nan, np.float32)
    miss = 0
    for ty in range(ymin, ymax + 1):
        for tx in range(xmin, xmax + 1):
            p = os.path.join(TERRAIN, f"{tx}_{ty}.png")
            if not os.path.exists(p): miss += 1; continue
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
            z = im[:, :, 0] * 256.0 + im[:, :, 1] + im[:, :, 2] / 256.0 - 32768.0
            elev[(ty - ymin) * 256:(ty - ymin + 1) * 256, (tx - xmin) * 256:(tx - xmin + 1) * 256] = z
    # fill any gaps with nearest finite
    if np.isnan(elev).any():
        idx = ndimage.distance_transform_edt(np.isnan(elev), return_distances=False, return_indices=True)
        elev = elev[tuple(idx)]
    return elev, xmin, ymin, xmax, ymax

# ground resolution (m/px) at z12 for a given pixel-row latitude
def px2lat(py, z):
    n = math.pi - 2 * math.pi * py / (256.0 * (1 << z))
    return math.degrees(math.atan(math.sinh(n)))

# ---------- terrain derivatives ----------
def slope_curv(elev, ymin):
    H, W = elev.shape
    rows_lat = np.array([px2lat(ymin * 256 + r + 0.5, Z) for r in range(H)])
    gres = (WORLD / (256.0 * (1 << Z))) * np.cos(np.radians(rows_lat))   # m/px per row
    gres = gres[:, None]
    gy, gx = np.gradient(elev.astype(np.float64))
    slope_deg = np.degrees(np.arctan(np.hypot(gx / gres, gy / gres)))
    # convex-up proxy: negative Laplacian, clipped positive, normalised by 95th pct
    lap = ndimage.laplace(elev.astype(np.float64))
    convex = np.clip(-lap, 0, None)
    p95 = np.percentile(convex, 95) or 1.0
    convex_score = np.clip(convex / p95, 0, 1)
    return slope_deg.astype(np.float32), convex_score.astype(np.float32), float(gres.mean())

# ---------- D8 priority-flood flow accumulation (computed at ~120 m) ----------
def flow_accum(elev, factor=4):
    H, W = elev.shape
    h, w = H // factor, W // factor
    dem = elev[:h * factor, :w * factor].reshape(h, factor, w, factor).mean(axis=(1, 3)).astype(np.float64)
    EPS = 1e-3
    filled = np.full((h, w), np.inf)
    visited = np.zeros((h, w), bool)
    heap = []
    for i in range(h):
        for j in (range(w) if i in (0, h - 1) else (0, w - 1)):
            filled[i, j] = dem[i, j]; visited[i, j] = True
            heapq.heappush(heap, (dem[i, j], i * w + j))
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while heap:
        e, idx = heapq.heappop(heap)
        ci, cj = divmod(idx, w)
        for di, dj in nb:
            ni, nj = ci + di, cj + dj
            if 0 <= ni < h and 0 <= nj < w and not visited[ni, nj]:
                visited[ni, nj] = True
                fv = dem[ni, nj] if dem[ni, nj] > e else e + EPS
                filled[ni, nj] = fv
                heapq.heappush(heap, (fv, ni * w + nj))
    # D8 receiver (steepest descent on filled+eps surface)
    inf = filled
    dist = np.array([1, 1, 1, 1, math.sqrt(2)] * 1)  # placeholder
    best_drop = np.zeros((h, w)); recv = np.full((h, w), -1, np.int64)
    for di, dj in nb:
        d = math.hypot(di, dj)
        shifted = np.full((h, w), np.inf)
        si0, si1 = max(0, di), h + min(0, di); sj0, sj1 = max(0, dj), w + min(0, dj)
        ti0, ti1 = max(0, -di), h + min(0, -di); tj0, tj1 = max(0, -dj), w + min(0, -dj)
        shifted[ti0:ti1, tj0:tj1] = inf[si0:si1, sj0:sj1]
        drop = (inf - shifted) / d
        nidx = np.full((h, w), -1, np.int64)
        ii, jj = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        ni = ii + di; nj = jj + dj
        valid = (ni >= 0) & (ni < h) & (nj >= 0) & (nj < w)
        nidx[valid] = (ni[valid] * w + nj[valid])
        take = (drop > best_drop) & valid
        best_drop[take] = drop[take]; recv[take] = nidx[take]
    # accumulation in descending filled order
    acc = np.ones(h * w, np.float64)
    order = np.argsort(filled.ravel())[::-1]
    rflat = recv.ravel()
    for idx in order:
        r = rflat[idx]
        if r >= 0: acc[r] += acc[idx]
    acc2d = acc.reshape(h, w)
    score = np.clip(np.log1p(acc2d) / math.log(100.0), 0, 1)
    # upsample back to full res
    return np.kron(score, np.ones((factor, factor))).astype(np.float32)[:H, :W]

# ---------- rasterise reef polygons -> distance ----------
def reef_distance(xmin, ymin, H, W, gres):
    mask = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(mask)
    nfeat = 0
    for fn in ("dataGoldfields.geojson", "dataEndowment.geojson"):
        gj = json.load(open(os.path.join(HERE, fn)))
        for ft in gj["features"]:
            g = ft.get("geometry") or {}; t = g.get("type"); cs = g.get("coordinates")
            if not cs: continue
            polys = [cs] if t == "Polygon" else (cs if t == "MultiPolygon" else [])
            for poly in polys:
                ring = poly[0]
                pts = [(lon2px(x, Z) - xmin * 256, lat2px(y, Z) - ymin * 256) for x, y in ring]
                if len(pts) >= 3: dr.polygon(pts, fill=255); nfeat += 1
    m = np.asarray(mask) > 0
    dist_m = ndimage.distance_transform_edt(~m) * gres
    score = np.clip(1.0 - dist_m / 1000.0, 0, 1)
    return score.astype(np.float32), dist_m.astype(np.float32), nfeat

# ---------- workings density (count within 500 m) ----------
def workings_density(pts, xmin, ymin, H, W, gres):
    cnt = np.zeros((H, W), np.float32)
    for lon, lat in pts:
        px = lon2px(lon, Z) - xmin * 256; py = lat2px(lat, Z) - ymin * 256
        if 0 <= px < W and 0 <= py < H: cnt[int(py), int(px)] += 1
    rad = max(1, int(round(500.0 / gres)))
    yk, xk = np.ogrid[-rad:rad + 1, -rad:rad + 1]
    disk = (xk * xk + yk * yk <= rad * rad).astype(np.float32)
    within = ndimage.convolve(cnt, disk, mode="constant")
    score = np.clip(within / 5.0, 0, 1)
    return score.astype(np.float32), within.astype(np.float32)

# ---------- colormap (RdYlGn reversed: low=green, high=red), PALETTISED ----------
# Palette PNGs (mode 'P' + per-index alpha via tRNS) are ~10x smaller than RGBA for a
# smooth heatmap — essential to hit the <15 MB precache budget.
_STOPS = [(0.0, (26, 152, 80)), (0.25, (145, 207, 96)), (0.5, (255, 255, 191)),
          (0.75, (253, 174, 97)), (1.0, (215, 48, 39))]
def _ramp(t):
    for k in range(len(_STOPS) - 1):
        a, ca = _STOPS[k]; b, cb = _STOPS[k + 1]
        if a <= t <= b:
            f = (t - a) / (b - a)
            return tuple(int(round(ca[c] + (cb[c] - ca[c]) * f)) for c in range(3))
    return _STOPS[-1][1]
NLEV = 20   # NPI levels floor..100 (+ index 0 = transparent) — fewer levels compress far better
PAL_FLAT, TRNS = [], [0]
for _i in range(NLEV):
    _npi = NPI_FLOOR + (100 - NPI_FLOOR) * _i / (NLEV - 1); _t = _npi / 100.0
    PAL_FLAT += list(_ramp(_t)); TRNS.append(int(min(210, 60 + _t * 150)))
PAL_FLAT = [0, 0, 0] + PAL_FLAT                     # index 0 = transparent black
PAL_FLAT += [0] * (768 - len(PAL_FLAT))
TRNS = bytes(TRNS + [255] * (256 - len(TRNS)))
def quantize(npi):  # npi 0..100 float -> uint8 palette index (0 = transparent)
    idx = np.zeros(npi.shape, np.uint8)
    m = npi >= NPI_FLOOR
    lev = np.clip(np.round((npi - NPI_FLOOR) / (100 - NPI_FLOOR) * (NLEV - 1)), 0, NLEV - 1).astype(np.uint8)
    idx[m] = 1 + lev[m]
    return idx
def save_palette_tile(idx_tile, path):
    im = Image.fromarray(idx_tile, "P"); im.putpalette(PAL_FLAT)
    im.info["transparency"] = TRNS
    im.save(path, optimize=False, compress_level=9, transparency=TRNS)

def block_mean(a, f):
    H, W = a.shape; h, w = H // f, W // f
    return a[:h * f, :w * f].reshape(h, f, w, f).mean(axis=(1, 3))

# ---------- main ----------
def main():
    os.makedirs(OUT, exist_ok=True)
    pts = json.load(open(os.path.join(HERE, "workings.json")))
    # union z8 popup grid extent
    g8x0 = min(int(lon2px(r[1], 8)) for r in REGIONS); g8x1 = max(int(lon2px(r[3], 8)) for r in REGIONS)
    g8y0 = min(int(lat2px(r[4], 8)) for r in REGIONS); g8y1 = max(int(lat2px(r[2], 8)) for r in REGIONS)
    gcols, grows = g8x1 - g8x0 + 1, g8y1 - g8y0 + 1
    # packed grid planes (top RGBA + bottom RGBA stacked)
    grid = np.zeros((grows * 2, gcols, 4), np.uint8)
    spot_vals = {}
    region_npi = {}   # for sampling spots
    tiles_written = 0; total_bytes = 0; tile_paths = []

    for (rname, w, s, e, n) in REGIONS:
        print(f"\n=== {rname} ===", flush=True)
        cache = os.path.join(HERE, "cache_" + rname.split()[0].lower() + ".npz")
        if os.path.exists(cache):                       # fast retile path
            z = np.load(cache)
            npi = z["npi"]; xmin = int(z["xmin"]); ymin = int(z["ymin"]); H = int(z["H"]); W = int(z["W"])
            dist_score = z["dist_score"]; work_cnt = z["work_cnt"]; drain = z["drain"]
            slope_deg = z["slope_deg"]; bedrock = z["bedrock"]
            print(f"  loaded cache {cache}", flush=True)
        else:
            elev, xmin, ymin, xmax, ymax = load_mosaic(w, s, e, n)
            H, W = elev.shape; print(f"  mosaic {W}x{H}", flush=True)
            slope_deg, convex, gres = slope_curv(elev, ymin)
            print(f"  gres~{gres:.1f} m/px; slope computed", flush=True)
            drain = flow_accum(elev); print("  flow accumulation done", flush=True)
            dist_score, dist_m, nreef = reef_distance(xmin, ymin, H, W, gres)
            print(f"  reef distance ({nreef} rings)", flush=True)
            work_score, work_cnt = workings_density(pts, xmin, ymin, H, W, gres)
            print("  workings density done", flush=True)
            slope_score = np.clip(1.0 - np.abs((slope_deg - 17.5) / 17.5), 0, 1)
            bedrock = (slope_score * convex).astype(np.float32)
            npi = (WEIGHTS["dist_reef"] * dist_score + WEIGHTS["workings"] * work_score +
                   WEIGHTS["drainage"] * drain + WEIGHTS["slope"] * slope_score +
                   WEIGHTS["bedrock"] * bedrock) * 100.0
            npi = np.clip(ndimage.gaussian_filter(npi, 1.2), 0, 100).astype(np.float32)
            np.savez_compressed(cache, npi=npi, xmin=xmin, ymin=ymin, H=H, W=W,
                                dist_score=dist_score, work_cnt=work_cnt, drain=drain,
                                slope_deg=slope_deg, bedrock=bedrock)
        region_npi[rname] = (npi, xmin, ymin, H, W)

        # ---- render palettised tiles z10,11,12 ----
        for z in (10, 11, 12):
            tx0, tx1 = lon2tile(w, z), lon2tile(e, z)
            ty0, ty1 = lat2tile(n, z), lat2tile(s, z)
            f = 1 << (Z - z)             # z12 px per this-tile px
            idxmap = quantize(block_mean(npi, f).astype(np.float32) if f > 1 else npi)
            cH, cW = idxmap.shape        # this-zoom px dims of region
            ox = (xmin * 256) // f; oy = (ymin * 256) // f   # region origin in this-zoom global px
            for tx in range(tx0, tx1 + 1):
                for ty in range(ty0, ty1 + 1):
                    sx = tx * 256 - ox; sy = ty * 256 - oy
                    tile = np.zeros((256, 256), np.uint8)
                    ax0, ax1 = max(0, sx), min(cW, sx + 256)
                    ay0, ay1 = max(0, sy), min(cH, sy + 256)
                    if ax1 <= ax0 or ay1 <= ay0: continue
                    tile[ay0 - sy:ay1 - sy, ax0 - sx:ax1 - sx] = idxmap[ay0:ay1, ax0:ax1]
                    if tile.max() == 0: continue
                    d = os.path.join(OUT, str(z), str(tx)); os.makedirs(d, exist_ok=True)
                    p = os.path.join(d, f"{ty}.png")
                    save_palette_tile(tile, p)
                    tiles_written += 1; total_bytes += os.path.getsize(p)
                    tile_paths.append(f"./data/npi/{z}/{tx}/{ty}.png")

        # ---- accumulate popup grid (z8) ----
        def to8(a): return block_mean(a.astype(np.float32), 16)
        g_npi = to8(npi); g_dist = to8(dist_score); g_work = to8(work_cnt)
        g_drain = to8(drain); g_slopeD = to8(slope_deg); g_bed = to8(bedrock)
        gh, gw = g_npi.shape
        rx0 = (xmin * 256) // 16 - g8x0; ry0 = (ymin * 256) // 16 - g8y0
        for r in range(gh):
            for c in range(gw):
                gr, gc = ry0 + r, rx0 + c
                if not (0 <= gr < grows and 0 <= gc < gcols): continue
                # Alpha is the validity MASK only (0/255). Canvas premultiplies alpha, so any
                # DATA in the alpha channel would corrupt the RGB on getImageData — keep data in RGB.
                grid[gr, gc] = (min(255, int(g_npi[r, c])), int(np.clip(g_dist[r, c] * 255, 0, 255)),
                                min(255, int(round(g_work[r, c]))), 255)
                grid[grows + gr, gc] = (int(np.clip(g_drain[r, c] * 255, 0, 255)),
                                        min(255, int(round(g_slopeD[r, c]))), int(np.clip(g_bed[r, c] * 255, 0, 255)), 255)
        del slope_deg, drain, dist_score, work_cnt, bedrock, npi

    # ---- sample the 12 spots ----
    for num, name, lat, lon in SPOTS:
        v = None
        for rname, (npi, xmin, ymin, H, W) in region_npi.items():
            px = int(lon2px(lon, Z) - xmin * 256); py = int(lat2px(lat, Z) - ymin * 256)
            if 0 <= px < W and 0 <= py < H:
                v = float(npi[max(0, py-3):py+4, max(0, px-3):px+4].max()); break
        spot_vals[num] = (name, round(v, 1) if v is not None else None)

    Image.fromarray(grid, "RGBA").save(os.path.join(OUT, "npi-grid.png"), optimize=True)
    gsize = os.path.getsize(os.path.join(OUT, "npi-grid.png"))
    # SW precache manifest — every tile path, so the service worker can cache the
    # whole NPI region for offline field use in one install pass.
    json.dump(sorted(tile_paths), open(os.path.join(OUT, "tiles-manifest.json"), "w"))

    meta = {
        "version": "v32", "built": os.environ.get("BUILD_DATE", "2026-07-01"),
        "dem": "AWS terrarium z12 (~30 m, SRTM-derived)", "lidar": False,
        "weights": WEIGHTS, "npiFloor": NPI_FLOOR,
        "regions": [{"name": r[0], "bbox": [r[1], r[2], r[3], r[4]]} for r in REGIONS],
        "minNativeZoom": 10, "maxNativeZoom": 12,
        "grid": {"zoom": 8, "x0": g8x0, "y0": g8y0, "cols": gcols, "rows": grows,
                 "planes": "top RGBA=[npi0-100, distReefScore*255, workingsCount, mask255]; "
                           "bottom RGBA=[drainageScore*255, slopeDeg, bedrockScore*255, mask255]"},
        "limitations": [
            "NPI is a heuristic, not a prediction. Real-world success depends on terrain, "
            "ground conditions, equipment and technique.",
            "Elevation is SRTM-derived ~30 m terrain (no Victorian public LiDAR tile service "
            "exists yet) — slope, drainage and bedrock terms are coarse.",
            "Future versions will retrain on your confirmed gold events for personal calibration."],
        "spots": spot_vals,
    }
    json.dump(meta, open(os.path.join(OUT, "npi-meta.json"), "w"), indent=0)

    print("\n========== SUMMARY ==========")
    print(f"tiles: {tiles_written}  bytes: {total_bytes/1e6:.2f} MB  grid.png: {gsize/1024:.0f} KB")
    print(f"grid: {gcols}x{grows} cells @ z8 (~490 m)")
    print("NPI at the 12 trip spots (max within ~200 m):")
    for num in sorted(spot_vals):
        name, v = spot_vals[num]
        print(f"  {num:2d}. {name:28s} {v}")

if __name__ == "__main__":
    main()
