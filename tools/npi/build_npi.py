#!/usr/bin/env python3
"""AuraGold NPI build (v35) — per-detector Nugget Potential Index heatmaps.

A reproducible, end-to-end pipeline: every derived input is computed here by a real
function (no orphan / cache-only branches). Heavy per-region compute is cached to
cache_<region>.npz purely for fast re-tiling; deleting the cache reruns the same code.

MODEL (v35) — prior x evidence x interaction, not a linear distance sum:

    evidence   = sum of detector-specific terms, each 0..1 (neutral 0.5 if missing)
    interact   = detector-specific multiplicative confluence bonus (item 7)
    prior_mod  = 0.15 + 0.85 * goldfield_prior   (soft Bayesian-style prior, item 12)
    burn_mult  = 1 + 0.10 * fresh_exposure       (recent fire scars, item 6)
    NPI        = 100 * GAIN * evidence * (1 + K_INT*interact) * prior_mod * burn_mult

Inputs (all free / Australia-licensed; see the fetch_*.py siblings + README):
  DEM        AWS terrarium z12 (~30 m, SRTM-derived). No public Vic 5 m DEM service
             is openly fetchable + full-region 5 m is infeasible here (multi-GB +
             billion-cell pure-Python flow + 60 MB tile budget) — documented call.
  workings   VicMine gold occurrences -> 2D Gaussian KDE (item 1), not a 500 m count.
  geophysics GA magnetics (TMI-RTP + analytic signal) + radiometrics (%K, Th ppm),
             GLOBALLY normalised across regions (item 9). Mag is POSITIVE for PI,
             NEGATIVE for VLF; analytic signal = structure for PI/ZVT (items 2,3).
  geology    Vic 1:250k surface geology -> lithology favourability (item 5).
  fire       Vic DELWP fire_history perimeters -> recency-weighted fresh exposure
             (item 6; perimeter proxy, not per-pixel NBR — no rasterio here).
  prior      Official goldfield + endowment polygons -> soft prior (item 12).
"""
import json, math, os, sys, heapq, datetime
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import regions as R
import stream_hotspots as SH

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TERRAIN = os.path.join(HERE, "terrain_z12")
OUT = os.path.join(REPO, "data", "npi")
Z = 12
R_EARTH = 6378137.0
WORLD = 2 * math.pi * R_EARTH
CUR_YEAR = 2026
GAIN = 1.18          # global gain so headline ground lands in the high band
K_INT = 0.80         # interaction confluence bonus weight
GEO_PRIOR_W = 0.45   # how much geological favourability (litho x K) lifts the goldfield prior
NPI_FLOOR = 8        # below this -> transparent (negligible potential)
REGIONS = R.BUILD

# v35: THREE detector-class variants. slope=(peak_deg, half_width) triangular band.
# Evidence weights per variant sum to 1.0; each term is 0..1. The variants are decorrelated
# by their DIVERGENT terms: VLF is drainage-heavy + rewards LOW magnetics (clean ground);
# PI is magnetics-heavy + structural (analytic signal) + drainage-blind; ZVT is hammered +
# structural. The shared workings backbone keeps the headline goldfields strong.
# v37: a `stream` micro-feature hotspot term (see stream_hotspots.py) SHARPENS the drainage.
# VLF steals 0.18 from its uniform `drain` (drain becomes the permissive layer, the hotspot the
# sharpener) so the inside-of-the-bend / slope-break out-scores the straight reaches on the same
# creek; PI/ZVT take a small 0.05 (benches still matter for the GPZ/GPX). VLF's interaction bonus
# is now hotspot-weighted too, so the confluence lift lands ON the micro-feature, not the whole run.
VARIANTS = {
    "vlf": dict(label="VLF (Gold Monster)", slope=(10.0, 10.0),   # gentle clean creek/eluvial
        w=dict(drain=0.12, stream=0.20, lowmag=0.22, slope=0.13, workkde=0.10, litho=0.09, bedrock=0.08, k=0.06)),
    "pi":  dict(label="PI (GPX 6000)", slope=(22.5, 12.5),        # steeper mineralised hot ground
        w=dict(mag=0.26, asig=0.18, slope=0.14, workkde=0.12, litho=0.10, th=0.10, bedrock=0.04, drain=0.01, stream=0.05)),
    "zvt": dict(label="ZVT (GPZ 7000)", slope=(17.5, 15.0),       # hammered premium ground
        w=dict(hammered=0.26, asig=0.18, workkde=0.14, mag=0.14, slope=0.10, litho=0.10, drain=0.03, stream=0.05)),
}
VKEYS = ["vlf", "pi", "zvt"]
# VLF interaction: how much of the confluence bonus follows the stream hotspot vs raw drainage.
# 0.85 = mostly hotspot-driven (the sharpener) but keeps 15% raw drainage so headline eluvial/hillslope
# spots off the modern channel don't crater. Tuned against the 5-creek + region-wide sharpening eval.
VLF_INT_STREAM = 0.85

# 12 known trip spots (report sanity-check) + ~10 negative controls (item 11).
SPOTS = [
    (1, "Mount Cole / Bayindeen", -37.2670, 143.2920), (2, "Avoca / Pyrenees", -37.0900, 143.5000),
    (3, "Tarnagulla / Waanyarra", -36.7300, 143.8230), (4, "Talbot / Daisy Hill", -37.1850, 143.7050),
    (5, "Heathcote / McIvor", -36.9270, 144.7050), (6, "Whroo / Rushworth", -36.8600, 145.0080),
    (7, "Inglewood / Kingower", -36.5670, 143.8740), (8, "Hepburn / Sailors Ck", -37.3550, 144.1500),
    (9, "Maldon / Muckleford", -37.0010, 144.0700), (10, "WEDDERBURN (HEADLINE)", -36.4170, 143.6200),
    (11, "Wombat / Bullarook", -37.4500, 144.1000), (12, "Chiltern / Eldorado", -36.2000, 146.5170),
]
NEG = [   # (name, lat, lon) — genuinely NON-gold ground (basalt / urban / sedimentary basin);
          # must score LOW on all three variants. (Reservoirs flooding gold-bearing valleys —
          # Cairn Curran, Eppalock — are deliberately NOT here: they sit on real gold ground so a
          # moderate score there is correct, not a false positive; see the build report.)
    ("Melbourne CBD (urban)", -37.8136, 144.9631),
    ("Werribee basalt plain", -37.8800, 144.6200),
    ("Skipton volcanic plain", -37.6900, 143.3600),
    ("Murray Basin plains (Boort N)", -36.1200, 143.4500),
    ("Bacchus Marsh sediments", -37.6700, 144.4400),
    ("Wimmera cropland (Donald)", -36.3600, 143.0000),
    ("Charlton Avon floodplain", -36.2500, 143.3500),
    ("Bendigo Murray-basin edge N", -36.3000, 144.3000),
    ("Ballan farmland", -37.6000, 144.2300),
    ("Lake Bolac plains W", -37.7100, 142.9700),
]

# v37 verification: 5 known VLF hotspots on Vic goldfield creeks. For each, the build compares the
# VLF score at the best stream MICRO-FEATURE (highest stream_hotspot channel cell nearby) against a
# nearby STRAIGHT REACH (a low-hotspot channel cell on the same drainage) — before (v36 uniform
# drainage) vs after (v37 sharpener). Sharpening works iff the micro-feature out-scores the straight
# reach AND the gap widens vs v36. (Town-scale coords; the sampler finds the real channel nearby.)
VERIFY = [
    ("Wombat Ck / Daylesford", -37.3400, 144.1400),
    ("Creswick Ck confluence", -37.4200, 143.8950),
    ("Loddon at Tarnagulla",   -36.7750, 143.8050),
    ("Avoca R at Amherst",     -37.1900, 143.6600),
    ("Yankee Ck / Dunolly",    -36.8480, 143.7350),
]

# ---------- web-mercator helpers ----------
def lon2px(lon, z): return (lon + 180.0) / 360.0 * 256.0 * (1 << z)
def lat2px(lat, z):
    s = math.sin(math.radians(lat)); s = min(max(s, -0.9999), 0.9999)
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * 256.0 * (1 << z)
def lon2tile(lon, z): return int(math.floor(lon2px(lon, z) / 256.0))
def lat2tile(lat, z): return int(math.floor(lat2px(lat, z) / 256.0))
def px2lat(py, z):
    n = math.pi - 2 * math.pi * py / (256.0 * (1 << z))
    return math.degrees(math.atan(math.sinh(n)))
def px2lon(px, z): return px / (256.0 * (1 << z)) * 360.0 - 180.0

# ---------- 1. terrarium tiles -> elevation mosaic ----------
def load_mosaic(w, s, e, n):
    xmin, xmax = lon2tile(w, Z), lon2tile(e, Z)
    ymin, ymax = lat2tile(n, Z), lat2tile(s, Z)
    W = (xmax - xmin + 1) * 256; H = (ymax - ymin + 1) * 256
    elev = np.full((H, W), np.nan, np.float32); miss = 0
    for ty in range(ymin, ymax + 1):
        for tx in range(xmin, xmax + 1):
            p = os.path.join(TERRAIN, f"{tx}_{ty}.png")
            if not os.path.exists(p): miss += 1; continue
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
            z = im[:, :, 0] * 256.0 + im[:, :, 1] + im[:, :, 2] / 256.0 - 32768.0
            elev[(ty - ymin) * 256:(ty - ymin + 1) * 256, (tx - xmin) * 256:(tx - xmin + 1) * 256] = z
    if np.isnan(elev).any():
        idx = ndimage.distance_transform_edt(np.isnan(elev), return_distances=False, return_indices=True)
        elev = elev[tuple(idx)]
    if miss: print(f"  [mosaic] {miss} missing terrain tiles (gap-filled)", flush=True)
    return elev, xmin, ymin, xmax, ymax

# ---------- terrain derivatives (slope, convex-curvature bedrock proxy) ----------
def slope_curv(elev, ymin):
    H, W = elev.shape
    rows_lat = np.array([px2lat(ymin * 256 + r + 0.5, Z) for r in range(H)])
    gres = (WORLD / (256.0 * (1 << Z))) * np.cos(np.radians(rows_lat))   # m/px per row
    gres = gres[:, None]
    gy, gx = np.gradient(elev.astype(np.float64))
    slope_deg = np.degrees(np.arctan(np.hypot(gx / gres, gy / gres)))
    lap = ndimage.laplace(elev.astype(np.float64))
    convex = np.clip(-lap, 0, None)
    p95 = np.percentile(convex, 95) or 1.0
    convex_score = np.clip(convex / p95, 0, 1)
    return slope_deg.astype(np.float32), convex_score.astype(np.float32), float(gres.mean())

def slope_band(slope_deg, peak, halfwidth):
    return np.clip(1.0 - np.abs((slope_deg - peak) / halfwidth), 0, 1).astype(np.float32)

# ---------- D8 priority-flood flow routing (computed downsampled) ----------
# route_flow returns the depression-filled DEM, the D8 receiver graph and flow accumulation on
# the downsampled grid. `drain` (the permissive drainage term) AND the v37 stream micro-feature
# hotspots (stream_hotspots.py) both consume this SAME route, so we pay for one flood.
def route_flow(elev, factor=4):
    H, W = elev.shape; h, w = H // factor, W // factor
    dem = elev[:h * factor, :w * factor].reshape(h, factor, w, factor).mean(axis=(1, 3)).astype(np.float64)
    EPS = 1e-3
    filled = np.full((h, w), np.inf); visited = np.zeros((h, w), bool); heap = []
    for i in range(h):
        for j in (range(w) if i in (0, h - 1) else (0, w - 1)):
            filled[i, j] = dem[i, j]; visited[i, j] = True
            heapq.heappush(heap, (dem[i, j], i * w + j))
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while heap:
        e, idx = heapq.heappop(heap); ci, cj = divmod(idx, w)
        for di, dj in nb:
            ni, nj = ci + di, cj + dj
            if 0 <= ni < h and 0 <= nj < w and not visited[ni, nj]:
                visited[ni, nj] = True
                fv = dem[ni, nj] if dem[ni, nj] > e else e + EPS
                filled[ni, nj] = fv; heapq.heappush(heap, (fv, ni * w + nj))
    inf = filled; best_drop = np.zeros((h, w)); recv = np.full((h, w), -1, np.int64)
    for di, dj in nb:
        d = math.hypot(di, dj)
        shifted = np.full((h, w), np.inf)
        si0, si1 = max(0, di), h + min(0, di); sj0, sj1 = max(0, dj), w + min(0, dj)
        ti0, ti1 = max(0, -di), h + min(0, -di); tj0, tj1 = max(0, -dj), w + min(0, -dj)
        shifted[ti0:ti1, tj0:tj1] = inf[si0:si1, sj0:sj1]
        drop = (inf - shifted) / d
        ii, jj = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        ni = ii + di; nj = jj + dj
        valid = (ni >= 0) & (ni < h) & (nj >= 0) & (nj < w)
        nidx = np.full((h, w), -1, np.int64); nidx[valid] = (ni[valid] * w + nj[valid])
        take = (drop > best_drop) & valid
        best_drop[take] = drop[take]; recv[take] = nidx[take]
    acc = np.ones(h * w, np.float64); order = np.argsort(filled.ravel())[::-1]; rflat = recv.ravel()
    for idx in order:
        r = rflat[idx]
        if r >= 0: acc[r] += acc[idx]
    return dict(recv=recv.astype(np.int64), acc=acc.reshape(h, w).astype(np.float32),
                dem=dem.astype(np.float32), filled=filled.astype(np.float32), factor=factor)

def drain_from_route(route, H, W):
    """log-scaled flow-accumulation score, upsampled to full res (== v35 flow_accum output)."""
    f = int(route["factor"])
    score = np.clip(np.log1p(route["acc"].astype(np.float64)) / math.log(100.0), 0, 1)
    return np.kron(score, np.ones((f, f))).astype(np.float32)[:H, :W]

# ---------- workings KDE (item 1) — replaces the 94.7%-zero 500 m count ----------
def workings_kde(pts, xmin, ymin, H, W, gres, sigma_m):
    cnt = np.zeros((H, W), np.float32)
    for lon, lat in pts:
        px = lon2px(lon, Z) - xmin * 256; py = lat2px(lat, Z) - ymin * 256
        if 0 <= px < W and 0 <= py < H: cnt[int(py), int(px)] += 1
    sig = max(1.0, sigma_m / gres)
    kde = ndimage.gaussian_filter(cnt, sig, mode="constant")
    pos = kde[kde > 0]
    scale = np.percentile(pos, 80) if pos.size else 1.0
    score = 1.0 - np.exp(-kde / max(scale, 1e-9))        # smooth saturating 0..1
    return score.astype(np.float32), cnt

# ---------- goldfield prior (item 12) — soft, replaces the hardcoded distance term ----------
def _rasterise(geojson_files, xmin, ymin, H, W):
    mask = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(mask); nfeat = 0
    for fn in geojson_files:
        path = os.path.join(HERE, fn)
        if not os.path.exists(path): continue
        gj = json.load(open(path))
        for ft in gj.get("features", []):
            g = ft.get("geometry") or {}; t = g.get("type"); cs = g.get("coordinates")
            if not cs: continue
            polys = [cs] if t == "Polygon" else (cs if t == "MultiPolygon" else [])
            for poly in polys:
                ring = poly[0]
                pts = [(lon2px(x, Z) - xmin * 256, lat2px(y, Z) - ymin * 256) for x, y in ring]
                if len(pts) >= 3: dr.polygon(pts, fill=255); nfeat += 1
    return (np.asarray(mask) > 0), nfeat

def goldfield_prior(xmin, ymin, H, W, gres):
    mgf, n1 = _rasterise(["dataGoldfields.geojson"], xmin, ymin, H, W)
    men, n2 = _rasterise(["dataEndowment.geojson"], xmin, ymin, H, W)
    dist_gf = ndimage.distance_transform_edt(~mgf) * gres if mgf.any() else np.full((H, W), 1e7)
    dist_en = ndimage.distance_transform_edt(~men) * gres if men.any() else np.full((H, W), 1e7)
    prior = np.maximum(np.exp(-dist_gf / 3000.0), 0.55 * np.exp(-dist_en / 5000.0))
    return prior.astype(np.float32), dist_gf.astype(np.float32), n1 + n2

# ---------- lithology favourability (item 5) ----------
def litho_favour(subtype, ageoldno):
    sub = (subtype or "").strip().lower()
    if sub == "intrusive": return 0.85               # granite/granodiorite -> contact gold
    try: age = float(ageoldno)
    except (TypeError, ValueError): age = None
    if age is None or age < 0: return 0.5            # unknown -> neutral (item 8)
    if age >= 541: return 0.60                        # Precambrian basement
    if age >= 485: return 0.85                        # Cambrian greenstone (Heathcote belt)
    if age >= 444: return 0.90                        # Ordovician turbidite host (Bendigo/Castlemaine)
    if age >= 419: return 0.85                        # Silurian metasediment
    if age >= 359: return 0.80                        # Devonian
    if age >= 299: return 0.55                        # Carboniferous
    if age >= 252: return 0.40                        # Permian glacials
    if age >= 66:  return 0.45                        # Mesozoic
    if age >= 2.6: return 0.30                        # Cenozoic Tertiary cover / Newer Volcanics basalt
    return 0.50                                       # Quaternary alluvium (drainage handles placer)

def lithology_raster(slug, xmin, ymin, H, W, factor=4):
    path = os.path.join(HERE, "geology_" + slug + ".geojson")
    h, w = H // factor, W // factor
    if not os.path.exists(path):
        return np.full((H, W), 0.5, np.float32)       # neutral if missing (item 8)
    img = Image.new("L", (w, h), 128)                 # default 128/255 ~ 0.5 neutral (item 8)
    dr = ImageDraw.Draw(img)
    feats = json.load(open(path)).get("features", [])
    feats.sort(key=lambda f: litho_favour(f["properties"].get("subtype"), f["properties"].get("ageoldno")))
    for ft in feats:                                  # ascending favour -> high drawn last (wins)
        val = int(round(litho_favour(ft["properties"].get("subtype"), ft["properties"].get("ageoldno")) * 255))
        g = ft.get("geometry") or {}; t = g.get("type"); cs = g.get("coordinates")
        if not cs: continue
        polys = [cs] if t == "Polygon" else (cs if t == "MultiPolygon" else [])
        for poly in polys:
            ring = poly[0]
            pts = [((lon2px(x, Z) - xmin * 256) / factor, (lat2px(y, Z) - ymin * 256) / factor) for x, y in ring]
            if len(pts) >= 3: dr.polygon(pts, fill=val)
    litho = np.asarray(img).astype(np.float32) / 255.0
    return np.kron(litho, np.ones((factor, factor), np.float32))[:H, :W]

# ---------- fire fresh-exposure (item 6) — recency-weighted perimeter proxy ----------
def fire_raster(slug, xmin, ymin, H, W, factor=4):
    path = os.path.join(HERE, "fire_" + slug + ".geojson")
    h, w = H // factor, W // factor
    img = Image.new("L", (w, h), 0)
    if not os.path.exists(path):
        return np.zeros((H, W), np.float32)
    dr = ImageDraw.Draw(img)
    def boost(p):
        season = p.get("season")
        if not season: return 0.0
        recency = max(0.0, 1.0 - (CUR_YEAR - int(season)) / 12.0)     # decay over 12 yrs
        typew = 1.0 if (p.get("firetype") or "").lower() == "bushfire" else 0.6
        return recency * typew
    feats = json.load(open(path)).get("features", [])
    feats.sort(key=lambda f: boost(f["properties"]))                  # ascending -> most recent wins
    for ft in feats:
        b = boost(ft["properties"])
        if b <= 0: continue
        val = int(round(b * 255)); g = ft.get("geometry") or {}; t = g.get("type"); cs = g.get("coordinates")
        if not cs: continue
        polys = [cs] if t == "Polygon" else (cs if t == "MultiPolygon" else [])
        for poly in polys:
            ring = poly[0]
            pts = [((lon2px(x, Z) - xmin * 256) / factor, (lat2px(y, Z) - ymin * 256) / factor) for x, y in ring]
            if len(pts) >= 3: dr.polygon(pts, fill=val)
    burn = np.asarray(img).astype(np.float32) / 255.0
    return np.kron(burn, np.ones((factor, factor), np.float32))[:H, :W]

# ---------- geophysics resample onto grid (raw values; global norm applied later) ----------
def sample_geophys(arr, bbox, xmin, ymin, H, W, factor=4):
    mw, ms, me, mn = bbox; mh, mwid = arr.shape
    a = np.where(arr <= -9999.0, np.nan, arr)                          # K/Th nodata sentinel (item 8)
    fill = float(np.nanmedian(a[np.isfinite(a)])) if np.isfinite(a).any() else 0.0
    a_filled = np.nan_to_num(a, nan=fill)
    h, w = H // factor, W // factor
    cols = np.arange(w); rows = np.arange(h)
    lon = px2lon(xmin * 256 + cols * factor + factor / 2.0, Z)
    lat = np.array([px2lat(ymin * 256 + r * factor + factor / 2.0, Z) for r in rows])
    mc = (lon - mw) / (me - mw) * mwid - 0.5
    mr = (mn - lat) / (mn - ms) * mh - 0.5
    MR, MC = np.broadcast_arrays(mr[:, None], mc[None, :])
    samp = ndimage.map_coordinates(a_filled, [MR, MC], order=1, mode="nearest").astype(np.float32)
    valid = ndimage.map_coordinates(np.isfinite(a).astype(np.float32), [MR, MC], order=1, mode="nearest")
    samp = np.where(valid > 0.5, samp, np.nan).astype(np.float32)      # keep nodata as NaN -> neutral later
    up = np.kron(samp, np.ones((factor, factor), np.float32))[:H, :W]
    return up

def norm01(raw, lo, hi):
    """Global p2..p98 -> 0..1; NaN (missing) -> 0.5 neutral (item 8)."""
    out = (raw - lo) / max(1e-6, (hi - lo))
    out = np.clip(out, 0.0, 1.0)
    return np.where(np.isfinite(raw), out, 0.5).astype(np.float32)

# ---------- colormap (palettised RdYlGn) ----------
_STOPS = [(0.0, (26, 152, 80)), (0.25, (145, 207, 96)), (0.5, (255, 255, 191)),
          (0.75, (253, 174, 97)), (1.0, (215, 48, 39))]
def _ramp(t):
    for k in range(len(_STOPS) - 1):
        a, ca = _STOPS[k]; b, cb = _STOPS[k + 1]
        if a <= t <= b:
            f = (t - a) / (b - a)
            return tuple(int(round(ca[c] + (cb[c] - ca[c]) * f)) for c in range(3))
    return _STOPS[-1][1]
NLEV = 20
PAL_FLAT, TRNS = [], [0]
for _i in range(NLEV):
    _npi = NPI_FLOOR + (100 - NPI_FLOOR) * _i / (NLEV - 1); _t = _npi / 100.0
    PAL_FLAT += list(_ramp(_t)); TRNS.append(int(min(210, 60 + _t * 150)))
PAL_FLAT = [0, 0, 0] + PAL_FLAT; PAL_FLAT += [0] * (768 - len(PAL_FLAT))
TRNS = bytes(TRNS + [255] * (256 - len(TRNS)))
def quantize(npi):
    idx = np.zeros(npi.shape, np.uint8); m = npi >= NPI_FLOOR
    lev = np.clip(np.round((npi - NPI_FLOOR) / (100 - NPI_FLOOR) * (NLEV - 1)), 0, NLEV - 1).astype(np.uint8)
    idx[m] = 1 + lev[m]; return idx
def save_palette_tile(idx_tile, path):
    im = Image.fromarray(idx_tile, "P"); im.putpalette(PAL_FLAT); im.info["transparency"] = TRNS
    im.save(path, optimize=False, compress_level=9, transparency=TRNS)

def block_mean(a, f):
    H, W = a.shape; h, w = H // f, W // f
    return a[:h * f, :w * f].reshape(h, f, w, f).mean(axis=(1, 3))

# ---------- the scoring model (item 7,8,12) ----------
def compute_variants(F):
    """F = dict of named input arrays (all 0..1, NaN-free). Returns {vk: npi 0..100}."""
    out = {}
    prior_mod = 0.15 + 0.85 * F["prior"]
    burn_mult = 1.0 + 0.10 * F["burn"]
    lowmag = 1.0 - F["mag"]
    for vk, cfg in VARIANTS.items():
        wt = cfg["w"]; pk, hw = cfg["slope"]; sb = slope_band(F["slope_deg"], pk, hw)
        terms = dict(drain=F["drain"], stream=F["stream"], workkde=F["workkde"], hammered=F["hammered"], slope=sb,
                     bedrock=F["bedrock"], mag=F["mag"], lowmag=lowmag, asig=F["asig"],
                     k=F["k"], th=F["th"], litho=F["litho"])
        evidence = sum(wt[t] * terms[t] for t in wt) / sum(wt.values())
        # v37: VLF's confluence bonus now follows the stream hotspot (blended with raw drainage),
        # so the interaction lift lands ON the point-bar / slope-break, not the whole straight run.
        if vk == "vlf":   interact = (VLF_INT_STREAM * F["stream"] + (1 - VLF_INT_STREAM) * F["drain"]) * F["prior"] * sb
        elif vk == "pi":  interact = F["workkde"] * F["mag"] * F["prior"]
        else:             interact = F["hammered"] * F["asig"] * F["prior"]
        npi = 100.0 * GAIN * evidence * (1.0 + K_INT * interact) * prior_mod * burn_mult
        out[vk] = np.clip(ndimage.gaussian_filter(npi, 1.0), 0, 100).astype(np.float32)
    return out

def compute_vlf_v36(F):
    """Reproduce the PRE-v37 VLF (uniform drain=0.30, no stream term, drain-driven interaction)
    for the honest before/after report — every cell as hot as any other on the same creek."""
    prior_mod = 0.15 + 0.85 * F["prior"]; burn_mult = 1.0 + 0.10 * F["burn"]; lowmag = 1.0 - F["mag"]
    sb = slope_band(F["slope_deg"], 10.0, 10.0)
    w = dict(drain=0.30, lowmag=0.20, slope=0.14, workkde=0.12, litho=0.10, bedrock=0.08, k=0.06)
    terms = dict(drain=F["drain"], lowmag=lowmag, slope=sb, workkde=F["workkde"], litho=F["litho"], bedrock=F["bedrock"], k=F["k"])
    evidence = sum(w[t] * terms[t] for t in w) / sum(w.values())
    interact = F["drain"] * F["prior"] * sb
    npi = 100.0 * GAIN * evidence * (1.0 + K_INT * interact) * prior_mod * burn_mult
    return np.clip(ndimage.gaussian_filter(npi, 1.0), 0, 100).astype(np.float32)

# ---------- per-region base inputs (the real pipeline; cached for fast re-tiling) ----------
RAW_KEYS = ["slope_deg", "bedrock", "drain", "workkde", "hammered", "prior", "dist_gf",
            "litho", "burn", "tmi_raw", "as_raw", "k_raw", "th_raw"]
# v37: the downsampled flow-route graph is cached too, so the stream-hotspot signals can be
# recomputed / re-tuned in the scoring phase WITHOUT re-running the expensive flood.
ROUTE_KEYS = ["rcv", "racc", "rdem"]

def build_base(rname, w, s, e, n, pts):
    cache = os.path.join(HERE, "cache_" + R.slug(rname) + ".npz")
    if os.path.exists(cache) and "rcv" in np.load(cache).files:
        z = np.load(cache)
        print(f"  [cache] {os.path.basename(cache)}", flush=True)
        d = {k: z[k] for k in RAW_KEYS}
        d["route"] = dict(recv=z["rcv"], acc=z["racc"], dem=z["rdem"], factor=int(z["rfactor"]))
        d.update(xmin=int(z["xmin"]), ymin=int(z["ymin"]), H=int(z["H"]), W=int(z["W"]), gres=float(z["gres"]))
        return d
    slug = R.slug(rname)
    elev, xmin, ymin, xmax, ymax = load_mosaic(w, s, e, n); H, W = elev.shape
    print(f"  mosaic {W}x{H}", flush=True)
    slope_deg, bedrock, gres = slope_curv(elev, ymin)
    route = route_flow(elev)
    drain = drain_from_route(route, H, W)
    workkde, _cnt = workings_kde(pts, xmin, ymin, H, W, gres, sigma_m=600.0)
    hammered, _ = workings_kde(pts, xmin, ymin, H, W, gres, sigma_m=2000.0)
    prior, dist_gf, npri = goldfield_prior(xmin, ymin, H, W, gres)
    litho = lithology_raster(slug, xmin, ymin, H, W)
    burn = fire_raster(slug, xmin, ymin, H, W)
    gp = np.load(os.path.join(HERE, "geophys_" + slug + ".npz"))
    bbox = gp["bbox"]
    tmi_raw = sample_geophys(gp["tmi"], bbox, xmin, ymin, H, W)
    as_raw = sample_geophys(gp["as"], bbox, xmin, ymin, H, W)
    k_raw = sample_geophys(gp["k"], bbox, xmin, ymin, H, W)
    th_raw = sample_geophys(gp["th"], bbox, xmin, ymin, H, W)
    print(f"  derived: slope/bedrock/drain/kde/prior({npri} polys)/litho/fire/geophys  gres~{gres:.1f}", flush=True)
    d = dict(slope_deg=slope_deg, bedrock=bedrock, drain=drain, workkde=workkde, hammered=hammered,
             prior=prior, dist_gf=dist_gf, litho=litho, burn=burn,
             tmi_raw=tmi_raw, as_raw=as_raw, k_raw=k_raw, th_raw=th_raw,
             route=route, gres=gres, xmin=xmin, ymin=ymin, H=H, W=W)
    np.savez_compressed(cache, **{k: d[k] for k in RAW_KEYS},
                        rcv=route["recv"], racc=route["acc"], rdem=route["dem"],
                        rfactor=route["factor"], gres=gres, xmin=xmin, ymin=ymin, H=H, W=W)
    return d

# ---------- global geophysics normalisation (item 9) ----------
def global_norm(bases):
    stats = {}
    for raw_key, nm in [("tmi_raw", "tmi"), ("as_raw", "asig"), ("k_raw", "k"), ("th_raw", "th")]:
        vals = np.concatenate([b[raw_key][np.isfinite(b[raw_key])].ravel() for b in bases.values()])
        stats[nm] = (float(np.percentile(vals, 2)), float(np.percentile(vals, 98)))
    return stats

def assemble(base, stats):
    """Normalise + neutral-fill into the 0..1 input dict the model consumes. The prior
    (item 12) is a noisy-OR of the goldfield-polygon prior and geological favourability
    (lithology x K) — so contact-hosted ground (granite + K anomaly) outside the mapped
    historical goldfields still registers, while basalt/water (low litho) does not.
    v37 also derives the stream micro-feature hotspots from the cached flow route."""
    F = dict(slope_deg=base["slope_deg"], bedrock=base["bedrock"], drain=base["drain"],
             workkde=base["workkde"], hammered=base["hammered"], litho=base["litho"], burn=base["burn"])
    F["mag"] = norm01(base["tmi_raw"], *stats["tmi"])
    F["asig"] = norm01(base["as_raw"], *stats["asig"])
    F["k"] = norm01(base["k_raw"], *stats["k"])
    F["th"] = norm01(base["th_raw"], *stats["th"])
    gf = base["prior"]                                   # goldfield-polygon prior
    geo_favour = np.clip(F["litho"] * (0.4 + 0.6 * F["k"]), 0, 1)
    F["prior"] = (1.0 - (1.0 - gf) * (1.0 - GEO_PRIOR_W * geo_favour)).astype(np.float32)
    sh = SH.compute_stream_signals(base["route"], base["gres"], base["H"], base["W"])
    F["stream"] = sh["stream_hotspot"]
    for k in ["sh_bend", "sh_slopebreak", "sh_confl", "sh_bench", "sh_pshadow", "sh_streammask"]:
        F[k] = sh[k]
    return F

# ---------- eval: importance, correlation, spot/negative-control sampling ----------
def variant_importance(F, npis):
    """Per variant: |corr(input, npi)| over visible cells, normalised to shares (%)."""
    inputs = ["prior", "workkde", "hammered", "drain", "stream", "bedrock", "mag", "asig", "k", "th", "litho", "burn"]
    res = {}
    for vk in VKEYS:
        npi = npis[vk]; vis = npi >= NPI_FLOOR
        if vis.sum() < 50: res[vk] = {}; continue
        y = npi[vis].astype(np.float64); ys = y.std() or 1.0
        cors = {}
        for nm in inputs:
            x = F[nm][vis].astype(np.float64); xs = x.std()
            if xs < 1e-9: cors[nm] = 0.0; continue
            cors[nm] = abs(float(np.mean((x - x.mean()) * (y - y.mean())) / (xs * ys)))
        tot = sum(cors.values()) or 1.0
        res[vk] = {nm: round(100.0 * c / tot, 1) for nm, c in sorted(cors.items(), key=lambda kv: -kv[1])}
    return res

def main():
    os.makedirs(OUT, exist_ok=True)
    for vk in VKEYS:                                   # clear stale tiles (repo hygiene)
        d = os.path.join(OUT, vk)
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for fn in files:
                    if fn.endswith(".png"): os.remove(os.path.join(root, fn))
    pts = json.load(open(os.path.join(HERE, "workings.json")))

    # PHASE A — per-region base inputs
    bases = {}
    for (rname, w, s, e, n) in REGIONS:
        print(f"\n=== {rname} (base) ===", flush=True)
        bases[rname] = build_base(rname, w, s, e, n, pts)

    # PHASE B — global geophysics normalisation
    stats = global_norm(bases)
    print("\n[global norm p2..p98]  " + "  ".join(f"{k}:[{lo:.3f},{hi:.3f}]" for k, (lo, hi) in stats.items()), flush=True)

    # grid geo-ref (z8) spanning both regions
    g8x0 = min(int(lon2px(r[1], 8)) for r in REGIONS); g8x1 = max(int(lon2px(r[3], 8)) for r in REGIONS)
    g8y0 = min(int(lat2px(r[4], 8)) for r in REGIONS); g8y1 = max(int(lat2px(r[2], 8)) for r in REGIONS)
    gcols, grows = g8x1 - g8x0 + 1, g8y1 - g8y0 + 1
    NPLANES = 7   # v37: +2 planes for the stream hotspot composite + its 5 sub-signals
    grid = np.zeros((grows * NPLANES, gcols, 4), np.uint8)

    region_var = {}; vlf_before = {}; tiles_written = 0; total_bytes = 0; tile_paths = []
    var_bytes = {v: 0 for v in VKEYS}; imp_acc = {v: {} for v in VKEYS}
    corr_pairs = []   # (vlf_vec, pi_vec) samples for global Pearson

    # PHASE C/D — assemble, score, tile, grid
    for (rname, w, s, e, n) in REGIONS:
        print(f"\n=== {rname} (score+tile) ===", flush=True)
        base = bases[rname]; F = assemble(base, stats)
        xmin, ymin, H, W = base["xmin"], base["ymin"], base["H"], base["W"]
        npis = compute_variants(F)
        region_var[rname] = (npis, xmin, ymin, H, W, F)
        vlf_before[rname] = compute_vlf_v36(F)   # v37 before/after reference

        imp = variant_importance(F, npis)
        for vk in VKEYS: imp_acc[vk][rname] = imp.get(vk, {})
        vis = (npis["vlf"] >= NPI_FLOOR) | (npis["pi"] >= NPI_FLOOR)
        if vis.sum() > 200:
            samp = np.random.RandomState(0).choice(np.flatnonzero(vis), size=min(20000, int(vis.sum())), replace=False)
            corr_pairs.append((npis["vlf"].ravel()[samp], npis["pi"].ravel()[samp]))

        for vk in VKEYS:
            npi = npis[vk]
            for zl in (10, 11, 12):
                tx0, tx1 = lon2tile(w, zl), lon2tile(e, zl)
                ty0, ty1 = lat2tile(n, zl), lat2tile(s, zl)
                f = 1 << (Z - zl)
                idxmap = quantize(block_mean(npi, f).astype(np.float32) if f > 1 else npi)
                cH, cW = idxmap.shape; ox = (xmin * 256) // f; oy = (ymin * 256) // f
                for tx in range(tx0, tx1 + 1):
                    for ty in range(ty0, ty1 + 1):
                        sx = tx * 256 - ox; sy = ty * 256 - oy
                        tile = np.zeros((256, 256), np.uint8)
                        ax0, ax1 = max(0, sx), min(cW, sx + 256); ay0, ay1 = max(0, sy), min(cH, sy + 256)
                        if ax1 <= ax0 or ay1 <= ay0: continue
                        tile[ay0 - sy:ay1 - sy, ax0 - sx:ax1 - sx] = idxmap[ay0:ay1, ax0:ax1]
                        if tile.max() == 0: continue
                        d = os.path.join(OUT, vk, str(zl), str(tx)); os.makedirs(d, exist_ok=True)
                        p = os.path.join(d, f"{ty}.png"); save_palette_tile(tile, p)
                        b = os.path.getsize(p); tiles_written += 1; total_bytes += b; var_bytes[vk] += b
                        tile_paths.append(f"./data/npi/{vk}/{zl}/{tx}/{ty}.png")
            print(f"  tiles {vk} done", flush=True)

        # ---- 5-plane popup grid (z8) ----
        def to8(a): return block_mean(a.astype(np.float32), 16)
        def to8max(a):                                   # block-MAX: a sparse micro-feature would vanish
            b = a.astype(np.float32); hh, ww = b.shape[0] // 16, b.shape[1] // 16   # under a z8 (~490 m) block-mean
            return b[:hh * 16, :ww * 16].reshape(hh, 16, ww, 16).max(axis=(1, 3))
        gv = {vk: to8(npis[vk]) for vk in VKEYS}
        G = {k: to8(F[k]) for k in ["prior", "workkde", "drain", "slope_deg", "bedrock", "mag",
                                    "asig", "k", "th", "litho", "burn", "hammered"]}
        # stream planes F/G carry the block-MAX so a point-bar / drop-pool that occupies a few 30 m cells
        # still reads as a hotspot when tapped at z8 — mean would dilute it to noise (measured 0.11 vs 0.31).
        for k in ["stream", "sh_bend", "sh_slopebreak", "sh_confl", "sh_bench", "sh_pshadow"]:
            G[k] = to8max(F[k])
        gh, gw = G["prior"].shape
        rx0 = (xmin * 256) // 16 - g8x0; ry0 = (ymin * 256) // 16 - g8y0
        def u8(x, sc=255): return int(np.clip(x * sc, 0, 255))
        for r in range(gh):
            for c in range(gw):
                gr, gc = ry0 + r, rx0 + c
                if not (0 <= gr < grows and 0 <= gc < gcols): continue
                grid[gr, gc] = (u8(gv["vlf"][r, c], 1), u8(gv["pi"][r, c], 1), u8(gv["zvt"][r, c], 1), 255)        # A
                grid[grows + gr, gc] = (u8(G["prior"][r, c]), u8(G["workkde"][r, c]), u8(G["drain"][r, c]), 255)    # B
                grid[2 * grows + gr, gc] = (min(255, int(round(G["slope_deg"][r, c]))), u8(G["bedrock"][r, c]), u8(G["mag"][r, c]), 255)  # C
                grid[3 * grows + gr, gc] = (u8(G["asig"][r, c]), u8(G["k"][r, c]), u8(G["th"][r, c]), 255)          # D
                grid[4 * grows + gr, gc] = (u8(G["litho"][r, c]), u8(G["burn"][r, c]), u8(G["hammered"][r, c]), 255)  # E
                grid[5 * grows + gr, gc] = (u8(G["stream"][r, c]), u8(G["sh_bend"][r, c]), u8(G["sh_slopebreak"][r, c]), 255)  # F
                grid[6 * grows + gr, gc] = (u8(G["sh_confl"][r, c]), u8(G["sh_bench"][r, c]), u8(G["sh_pshadow"][r, c]), 255)  # G

    # ---- spot + negative-control sampling ----
    def sample(lat, lon, comps=False):
        for rname, (npis, xmin, ymin, H, W, F) in region_var.items():
            px = int(lon2px(lon, Z) - xmin * 256); py = int(lat2px(lat, Z) - ymin * 256)
            if 0 <= px < W and 0 <= py < H:
                sl = (slice(max(0, py - 6), py + 7), slice(max(0, px - 6), px + 7))
                rec = {vk: round(float(npis[vk][sl].max()), 1) for vk in VKEYS}
                if comps:
                    cy, cx = min(max(py, 0), H - 1), min(max(px, 0), W - 1)
                    rec["c"] = {k: round(float(F[k][cy, cx]), 2) for k in
                                ["prior", "workkde", "drain", "stream", "slope_deg", "bedrock", "mag", "asig", "k", "th", "litho", "burn",
                                 "sh_bend", "sh_slopebreak", "sh_confl", "sh_bench", "sh_pshadow"]}
                return rec
        return None

    spots = {}
    for num, nm, lat, lon in SPOTS:
        r = sample(lat, lon, comps=True) or {vk: None for vk in VKEYS}
        r["name"] = nm; spots[num] = r
    negs = []
    for nm, lat, lon in NEG:
        r = sample(lat, lon, comps=True) or {vk: 0.0 for vk in VKEYS}
        r["name"] = nm; negs.append(r)

    # ---- v37 verification: VLF at a stream micro-feature vs the ADJACENT straight reach on the SAME
    # creek (nearest low-hotspot channel cell, >=~100 m away). Spatially adjacent = same goldfield
    # ground / geology / flow, so the ONLY difference is the placer micro-feature — the honest
    # "sweep here or 100 m up the creek?" test. (A drainage-only match can wander onto a different,
    # richer creek; the region-wide lift below is the aggregate proof.) ----
    GRES_APPROX = 30.5   # m/px near lat -37 at z12 (search-window sizing only)
    def sample_creek(lat, lon, radius_m=2600):
        for rname, (npis, xmin, ymin, H, W, F) in region_var.items():
            px = int(lon2px(lon, Z) - xmin * 256); py = int(lat2px(lat, Z) - ymin * 256)
            if not (0 <= px < W and 0 <= py < H): continue
            rad = int(radius_m / GRES_APPROX)
            y0, y1 = max(0, py - rad), min(H, py + rad); x0, x1 = max(0, px - rad), min(W, px + rad)
            near = ndimage.binary_dilation(F["sh_streammask"][y0:y1, x0:x1], iterations=2)  # incl point bars/benches
            if not near.any(): return None
            sh = F["stream"][y0:y1, x0:x1]; dr = F["drain"][y0:y1, x0:x1]
            vlfA = npis["vlf"][y0:y1, x0:x1]; vlfB = vlf_before[rname][y0:y1, x0:x1]
            hi = np.unravel_index(np.argmax(np.where(near, sh, -1.0)), sh.shape)     # strongest micro-feature
            yy, xx = np.mgrid[0:sh.shape[0], 0:sh.shape[1]]
            d2 = (yy - hi[0]) ** 2 + (xx - hi[1]) ** 2
            straight = near & (sh < 0.10) & (d2 >= 9)                                # adjacent reach, >=~100 m off
            if not straight.any(): return None
            st = np.unravel_index(np.argmin(np.where(straight, d2, np.inf)), d2.shape)  # nearest straight reach
            return {"hotspot": {"after": round(float(vlfA[hi]), 1), "before": round(float(vlfB[hi]), 1), "sh": round(float(sh[hi]), 2)},
                    "straight": {"after": round(float(vlfA[st]), 1), "before": round(float(vlfB[st]), 1), "sh": round(float(sh[st]), 2)},
                    "distM": round(float(np.sqrt(d2[st]) * GRES_APPROX))}
        return None
    verify = []
    for nm, lat, lon in VERIFY:
        rc = sample_creek(lat, lon)
        if rc: rc["name"] = nm; verify.append(rc)

    # region-wide sharpening proof: mean VLF at strong hotspots vs straight reaches (near-stream cells)
    hot_all, str_all = [], []
    for rname, (npis, xmin, ymin, H, W, F) in region_var.items():
        near = ndimage.binary_dilation(F["sh_streammask"], iterations=2)
        v = npis["vlf"]; sh = F["stream"]; dr = F["drain"]
        hot_all.append(v[near & (sh > 0.30)]); str_all.append(v[near & (sh < 0.08) & (dr >= 0.4)])
    hot_all = np.concatenate(hot_all); str_all = np.concatenate(str_all)
    region_lift = {"hotspotMeanVLF": round(float(hot_all.mean()), 1), "straightMeanVLF": round(float(str_all.mean()), 1),
                   "lift": round(float(hot_all.mean() - str_all.mean()), 1),
                   "nHotspot": int(hot_all.size), "nStraight": int(str_all.size)}

    # ---- which sub-signal drives the hotspot layer (share of composite over active cells) ----
    SUB_W = {"sh_bend": 0.30, "sh_slopebreak": 0.25, "sh_confl": 0.15, "sh_bench": 0.20, "sh_pshadow": 0.10}
    sub_acc = {s: 0.0 for s in SUB_W}; sub_cells = 0
    for rname, (npis, xmin, ymin, H, W, F) in region_var.items():
        active = F["stream"] > 0.02
        if not active.any(): continue
        sub_cells += int(active.sum())
        for s in SUB_W: sub_acc[s] += float((SUB_W[s] * F[s][active]).sum())
    sub_tot = sum(sub_acc.values()) or 1.0
    sub_share = {s.replace("sh_", ""): round(100.0 * sub_acc[s] / sub_tot, 1)
                 for s in sorted(SUB_W, key=lambda k: -sub_acc[k])}

    # ---- Pearson VLF vs PI (pooled) ----
    if corr_pairs:
        av = np.concatenate([p[0] for p in corr_pairs]); bv = np.concatenate([p[1] for p in corr_pairs])
        pear = float(np.corrcoef(av, bv)[0, 1])
    else:
        pear = None

    # ---- importance: pool regions weighted by visible-cell count (approx via mean) ----
    importance = {}
    for vk in VKEYS:
        merged = {}
        for rname, d in imp_acc[vk].items():
            for nm, v in d.items(): merged[nm] = merged.get(nm, 0.0) + v
        n = max(1, len(imp_acc[vk]))
        importance[vk] = dict(sorted({k: round(v / n, 1) for k, v in merged.items()}.items(), key=lambda kv: -kv[1]))
    top_share = {vk: (next(iter(importance[vk].items())) if importance[vk] else (None, None)) for vk in VKEYS}

    Image.fromarray(grid, "RGBA").save(os.path.join(OUT, "npi-grid.png"), optimize=True)
    gsize = os.path.getsize(os.path.join(OUT, "npi-grid.png"))
    json.dump(sorted(tile_paths), open(os.path.join(OUT, "tiles-manifest.json"), "w"))

    built = os.environ.get("BUILD_DATE") or datetime.date.today().isoformat()
    meta = {
        "version": "v37", "built": built,
        "dem": "AWS terrarium z12 (~30 m, SRTM-derived)", "lidar": False,
        "model": "prior x evidence x interaction (v35); v37 adds a stream micro-feature hotspot term that sharpens the VLF drainage",
        "streamHotspot": "6 placer signals (inside-bend 0.30, slope-break 0.25, bench 0.20, confluence 0.15, pressure-shadow 0.10; bar-head deferred — 30 m SRTM too coarse)",
        "geophysics": "GA magnetics (TMI-RTP + analytic signal) + radiometrics (%K, Th ppm), globally normalised",
        "lithology": "Vic 1:250k surface geology (geol250_polygon)",
        "fire": "Vic DELWP fire_history perimeters >=2008, recency-weighted (perimeter proxy, not per-pixel NBR)",
        "variants": {vk: {"label": VARIANTS[vk]["label"], "weights": VARIANTS[vk]["w"], "slope": VARIANTS[vk]["slope"]} for vk in VKEYS},
        "gain": GAIN, "kInteraction": K_INT, "npiFloor": NPI_FLOOR,
        "geophysNorm": {k: [round(lo, 3), round(hi, 3)] for k, (lo, hi) in stats.items()},
        "regions": [{"name": r[0], "bbox": [r[1], r[2], r[3], r[4]]} for r in REGIONS],
        "minNativeZoom": 10, "maxNativeZoom": 12,
        "grid": {"zoom": 8, "x0": g8x0, "y0": g8y0, "cols": gcols, "rows": grows, "planes": NPLANES,
                 "layout": "A=[npiVLF,npiPI,npiZVT]; B=[prior*255,workkde*255,drain*255]; "
                           "C=[slopeDeg,bedrock*255,mag*255]; D=[asig*255,k*255,th*255]; "
                           "E=[litho*255,burn*255,hammered*255]; "
                           "F=[stream*255,bend*255,slopebreak*255]; G=[confl*255,bench*255,pshadow*255]; alpha=mask"},
        "limitations": [
            "NPI is a heuristic prior, not a prediction. Success depends on terrain, ground conditions, equipment and technique.",
            "Elevation is SRTM-derived ~30 m terrain (no open Vic 5 m DEM service + full-region 5 m is infeasible in this build) — slope/drainage/bedrock are coarse and weighted low.",
            "Detector variants weight the same real inputs differently: VLF favours clean low-magnetic alluvial ground, PI favours mineralised (magnetic + structural) hot ground, ZVT favours hammered premium ground.",
            "Fire term is a recency-weighted perimeter proxy from Vic fire_history, not per-pixel Sentinel-2 NBR severity.",
            "Stream hotspots (v37) sharpen VLF onto point-bars / slope-breaks / benches, but are computed on the ~30 m SRTM route (~120 m flow grid). Bar-head scale is deferred (needs 5 m LiDAR); the resolved features are 100 m+.",
            "Future versions will retrain on your confirmed gold events for personal calibration."],
        "spots": spots,
        "eval": {
            "pearson_vlf_pi": round(pear, 3) if pear is not None else None,
            "importance": importance, "topShare": {vk: {"input": top_share[vk][0], "pct": top_share[vk][1]} for vk in VKEYS},
            "negativeControls": negs,
            "streamHotspots": {"subSignalShare": sub_share, "verify": verify, "regionLift": region_lift},
        },
    }
    json.dump(meta, open(os.path.join(OUT, "npi-meta.json"), "w"), indent=0)
    # also write a compact eval card the app's Settings reads
    json.dump({"version": "v37", "built": built, "pearson_vlf_pi": meta["eval"]["pearson_vlf_pi"],
               "topShare": meta["eval"]["topShare"], "importance": importance,
               "spots": {spots[k]["name"]: {vk: spots[k][vk] for vk in VKEYS} for k in sorted(spots)},
               "negativeControls": [{"name": x["name"], **{vk: x[vk] for vk in VKEYS}} for x in negs],
               "streamHotspots": {"subSignalShare": sub_share, "verify": verify, "regionLift": region_lift}},
              open(os.path.join(OUT, "npi-eval.json"), "w"), indent=0)

    # ---- report ----
    print("\n========== v37 SUMMARY ==========")
    print(f"tiles: {tiles_written}  total: {total_bytes/1e6:.2f} MB  grid.png: {gsize/1024:.0f} KB ({NPLANES} planes)")
    for vk in VKEYS: print(f"  {vk}: {var_bytes[vk]/1e6:.2f} MB")

    print("\n--- v37 STREAM HOTSPOTS ---")
    print(f"REGION-WIDE sharpening: strong hotspots mean VLF {region_lift['hotspotMeanVLF']} (n={region_lift['nHotspot']}) "
          f"vs straight reaches {region_lift['straightMeanVLF']} (n={region_lift['nStraight']})  ->  +{region_lift['lift']} lift")
    print("sub-signal share of the hotspot layer (over active cells):")
    for s, pc in sub_share.items(): print(f"  {s:12s} {pc:5.1f}%")
    print("\nVLF at stream MICRO-FEATURE vs ADJACENT straight reach on the SAME creek  (before v36 -> after v37):")
    print(f"  {'creek':26s} {'hotspot b->a':>14s} {'straight b->a':>15s} {'gap b->a':>12s}  dist")
    for r in verify:
        hs, sr = r["hotspot"], r["straight"]
        gb = hs["before"] - sr["before"]; ga = hs["after"] - sr["after"]
        print(f"  {r['name']:26s} {hs['before']:5.1f}->{hs['after']:5.1f}   {sr['before']:5.1f}->{sr['after']:5.1f}    {gb:+5.1f}->{ga:+5.1f}  {r.get('distM','?')}m")
    print(f"\nPearson VLF vs PI (pooled visible cells): {pear:.3f}   (target < 0.85)")
    print("\nTop input share per variant (target: no input > 40%):")
    for vk in VKEYS:
        nm, pct = top_share[vk]; print(f"  {vk}: {nm} {pct}%   | " + ", ".join(f"{k} {v}%" for k, v in list(importance[vk].items())[:5]))
    print("\n12 known spots  (VLF / PI / ZVT, max within ~200 m):")
    for num in sorted(spots):
        r = spots[num]
        print(f"  {num:2d}. {r['name']:28s} {str(r['vlf']):>5} / {str(r['pi']):>5} / {str(r['zvt']):>5}")
    print("\nNegative controls (should be LOW; Melbourne CBD must be < 30):")
    worst = 0
    for r in negs:
        mx = max(v for v in (r['vlf'], r['pi'], r['zvt']) if v is not None) if any(r[v] is not None for v in VKEYS) else 0
        worst = max(worst, mx)
        flag = "  <-- FAIL" if mx > 30 else ""
        print(f"  {r['name']:32s} {str(r['vlf']):>5} / {str(r['pi']):>5} / {str(r['zvt']):>5}{flag}")
    print(f"\nworst negative-control score: {worst:.1f}  ({'PASS' if worst <= 30 else 'FAIL'} gate <=30)")

if __name__ == "__main__":
    main()
