#!/usr/bin/env python3
"""AuraGold NPI v37 — stream micro-feature hotspots (placer-science sharpener).

Real placer gold is 90% about WHERE on a stream, not which stream. v36's VLF branch
treated every channel cell as equally hot; v37 post-processes the drainage network into
six placer signals and folds a composite into the model so the *inside of the meander*
and the *slope-break drop* out-score the straight reaches on the same creek.

The six signals (item 6 = bar-head is deferred — too fine for 30 m SRTM):

  1. inside-bend / point-bar  (w 0.30)  — sagitta of the vectorised channel points to
     the INSIDE (deposition side) of a high-curvature bend; gold drops where velocity is
     lowest. Stamped on the inside-adjacent cell + the channel vertex.
  2. slope-break              (w 0.25)  — along-stream d(slope)/ds; steep-above / flat-below
     = the drop point where the current can no longer carry heavies.
  3. confluence               (w 0.15)  — network nodes with in-degree >=2, buffered
     ~50-220 m downstream with distance decay (the junction bar / riffle).
  4. bench / paleochannel     (w 0.20)  — cells within ~200 m of an active stream, 5-30 m
     ABOVE local drainage, low local slope: old high terraces where ancient gold sits.
  5. pressure-shadow / pool   (w 0.10)  — the cell immediately downstream of a >30% slope
     drop, where a drop-pool forms and heavies settle out.

All geometry runs on the flow-routed DOWNSAMPLED grid (~120 m at factor 4 — the same route
the `drain` term uses, so we pay for one flood), then upsamples to the full ~30 m grid.
30 m SRTM limits how fine a feature we can resolve, but placer hotspots are usually 100 m+
features, so the sharpening is real (see README "Resolution").
"""
import math
import numpy as np
from scipy import ndimage

# --- tuning constants (all in metres / dimensionless) ---
STREAM_MIN_KM2 = 0.25   # channel-initiation upstream-area threshold
CURV_WIN = 2            # along-stream window (cells) for curvature + slope-break (smooths staircase)
CURV_MIN = 0.22         # sagitta/window below this = a straight reach (no bend)
BEND_OFFSET = 1.5       # cells to step off-channel toward the inside bank for the point bar
SB_SCALE = 0.14         # along-stream slope DROP (rise/run) that saturates the slope-break signal
PS_REL_DROP = 0.30      # spec ">30% slope change": along-stream slope must fall by >30% (relative)
PS_MIN_UPSLOPE = 0.03   # ...on a real flowing gradient (>3%), so dead-flat noise can't seed a pool
CONF_SCALE = 130.0      # confluence downstream decay length
CONF_BUFMAX = 220.0     # confluence downstream buffer
BENCH_DIST_MAX = 200.0  # horizontal reach of a bench from the active channel
BENCH_HAND_PK = 17.5    # height-above-drainage peak (band 5..30 m)
BENCH_HAND_HW = 12.5
BENCH_SLOPE_MAX = 8.0   # terraces are flat; steeper than this is a hillslope, not a bench

# composite weights (spec) — inside-bend dominant, bench second
W_COMPOSITE = dict(bend=0.30, slopebreak=0.25, confl=0.15, bench=0.20, pshadow=0.10)


def _walk(idx_flat, start, k):
    """Follow a receiver/upstream index map k steps; stay put at a -1 terminus."""
    cur = start.copy()
    for _ in range(k):
        nxt = idx_flat[cur]
        cur = np.where(nxt < 0, cur, nxt)
    return cur


def compute_stream_signals(route, gres, H, W, verbose=True):
    """route = dict(recv,acc,dem,filled,factor) at (h,w). Returns full-res (H,W) float32:
    stream_hotspot (composite) + the 5 sub-signals + a stream-cell mask (for eval)."""
    f = int(route["factor"])
    recv = np.asarray(route["recv"], np.int64)
    acc = np.asarray(route["acc"], np.float64)
    dem = np.asarray(route["dem"], np.float64)
    h, w = recv.shape
    csize = float(gres) * f                     # metres per downsampled cell
    cell_area = csize * csize

    recv_flat = recv.ravel()
    acc_flat = acc.ravel()
    dem_flat = dem.ravel()
    N = h * w
    rr_all = np.arange(N) // w
    cc_all = np.arange(N) % w

    # --- channel network + main-stem graph ---
    strm_flat = (acc_flat * cell_area) >= (STREAM_MIN_KM2 * 1e6)
    contrib = np.flatnonzero(strm_flat & (recv_flat >= 0))       # stream cells that flow onward
    indeg = np.zeros(N, np.int32)
    np.add.at(indeg, recv_flat[contrib], 1)
    # main upstream = highest-accumulation contributor per target (stable argsort, last write wins)
    order = np.argsort(acc_flat[contrib], kind="stable")
    cs = contrib[order]
    mainup_flat = np.full(N, -1, np.int64)
    mainup_flat[recv_flat[cs]] = cs

    # triplet cells: interior stream cells with both an upstream main stem and a downstream
    tri = np.flatnonzero(strm_flat & (recv_flat >= 0) & (mainup_flat >= 0))
    up = _walk(mainup_flat, tri, CURV_WIN)
    dn = _walk(recv_flat, tri, CURV_WIN)
    moved = (up != tri) & (dn != tri)
    tri, up, dn = tri[moved], up[moved], dn[moved]
    qr, qc = rr_all[tri], cc_all[tri]
    pr, pc = rr_all[up], cc_all[up]
    dr, dc = rr_all[dn], cc_all[dn]

    # ---- 1. inside-bend / point-bar (sagitta) ----
    bend = np.zeros(N, np.float32)
    Mx = (pc + dc) / 2.0 - qc                 # x=col
    My = (pr + dr) / 2.0 - qr                 # y=row  (vector points to the inside bank)
    sag = np.hypot(Mx, My)
    curv = np.clip(sag / CURV_WIN, 0.0, 1.0)
    is_bend = (curv >= CURV_MIN) & (sag > 1e-6)
    if is_bend.any():
        dxu = np.where(sag > 1e-6, Mx / np.maximum(sag, 1e-9), 0.0)
        dyu = np.where(sag > 1e-6, My / np.maximum(sag, 1e-9), 0.0)
        tri_b, cb = tri[is_bend], curv[is_bend].astype(np.float32)
        tinr = np.clip(np.round(qr[is_bend] + dyu[is_bend] * BEND_OFFSET), 0, h - 1).astype(np.int64)
        tinc = np.clip(np.round(qc[is_bend] + dxu[is_bend] * BEND_OFFSET), 0, w - 1).astype(np.int64)
        np.maximum.at(bend, tinr * w + tinc, cb)          # inside bank = the point bar
        np.maximum.at(bend, tri_b, 0.6 * cb)              # channel vertex (weaker)

    # ---- 2. slope-break  +  5. pressure-shadow ----
    slopebreak = np.zeros(N, np.float32)
    pshadow = np.zeros(N, np.float32)
    dist_up = np.maximum(np.hypot(qr - pr, qc - pc) * csize, csize)
    dist_dn = np.maximum(np.hypot(dr - qr, dc - qc) * csize, csize)
    up_slope = (dem_flat[up] - dem_flat[tri]) / dist_up      # +ve: upstream is higher
    dn_slope = (dem_flat[tri] - dem_flat[dn]) / dist_dn      # +ve: keeps dropping
    flattening = up_slope - dn_slope                          # steep-above / flat-below
    sb = np.clip(flattening / SB_SCALE, 0.0, 1.0).astype(np.float32)
    slopebreak[tri] = sb
    # pressure-shadow / drop-pool: immediately DOWNSTREAM of a >30% slope drop on a real gradient.
    rel_drop = 1.0 - dn_slope / np.maximum(up_slope, 1e-6)
    strong = (up_slope > PS_MIN_UPSLOPE) & (rel_drop > PS_REL_DROP)
    if strong.any():
        seed = tri[strong]
        # pool strength: how hard it flattens x how energetic the feeder was
        sv = (np.clip(rel_drop[strong], 0, 1) * np.clip(up_slope[strong] / 0.10, 0, 1)).astype(np.float32)
        step = recv_flat[seed]
        for decay in (0.95, 0.70):                           # 1-2 cells downstream = the drop-pool
            ok = step >= 0
            if not ok.any():
                break
            np.maximum.at(pshadow, step[ok], (sv[ok] * decay).astype(np.float32))
            sv = sv[ok]
            step = recv_flat[step[ok]]

    # ---- 3. confluence (in-degree >=2, buffered downstream with decay) ----
    confl = np.zeros(N, np.float32)
    cur = np.flatnonzero((indeg >= 2) & strm_flat)
    dist = 0.0
    while cur.size and dist <= CONF_BUFMAX:
        np.maximum.at(confl, cur, np.float32(math.exp(-dist / CONF_SCALE)))
        nxt = recv_flat[cur]
        cur = nxt[nxt >= 0]
        dist += csize

    # ---- 4. bench / paleochannel (off-stream terrace) ----
    bench = np.zeros((h, w), np.float32)
    strm2d = strm_flat.reshape(h, w)
    if strm2d.any():
        dist_px, idx2 = ndimage.distance_transform_edt(~strm2d, return_distances=True, return_indices=True)
        dist_m = dist_px * csize
        near_elev = dem[idx2[0], idx2[1]]
        hand = dem - near_elev
        gy, gx = np.gradient(dem)
        slope_deg = np.degrees(np.arctan(np.hypot(gx, gy) / csize))
        hand_band = np.clip(1.0 - np.abs(hand - BENCH_HAND_PK) / BENCH_HAND_HW, 0.0, 1.0)
        dist_decay = np.clip(1.0 - dist_m / BENCH_DIST_MAX, 0.0, 1.0)
        flatness = np.clip(1.0 - slope_deg / BENCH_SLOPE_MAX, 0.0, 1.0)
        bench = (hand_band * dist_decay * flatness).astype(np.float32)
        bench[strm2d] = 0.0                                  # the channel itself is not a bench

    # ---- composite ----
    wc = W_COMPOSITE
    comp = np.clip(wc["bend"] * bend.reshape(h, w) + wc["slopebreak"] * slopebreak.reshape(h, w) +
                   wc["confl"] * confl.reshape(h, w) + wc["bench"] * bench +
                   wc["pshadow"] * pshadow.reshape(h, w), 0.0, 1.0).astype(np.float32)

    def up2full(a2d, smooth=False):
        big = np.kron(a2d, np.ones((f, f), np.float32))[:H, :W]
        if smooth:
            big = ndimage.gaussian_filter(big, f * 0.6)
        return big.astype(np.float32)

    out = dict(
        stream_hotspot=up2full(comp, smooth=True),
        sh_bend=up2full(bend.reshape(h, w)),
        sh_slopebreak=up2full(slopebreak.reshape(h, w)),
        sh_confl=up2full(confl.reshape(h, w)),
        sh_bench=up2full(bench),
        sh_pshadow=up2full(pshadow.reshape(h, w)),
        sh_streammask=up2full(strm2d.astype(np.float32)) > 0.5,
    )
    if verbose:
        ns = int(strm_flat.sum())
        nb = int((bend > 0).sum())
        nc = int(((indeg >= 2) & strm_flat).sum())
        print(f"  [stream] csize~{csize:.0f} m  stream cells {ns}  bends {nb}  confluences {nc}", flush=True)
    return out
