# NPI build pipeline (v32 — Nugget Potential Index heatmap)

Offline, reproducible build of the `data/npi/` heatmap tiles + tap-to-explain grid.
All inputs are free / Australia-licensed; no API keys.

## Run (on a Mac with python3)

```sh
pip install --user numpy scipy pillow      # only deps
python3 fetch_dem.py            # AWS terrarium z12 terrain tiles (~30 m, SRTM-derived) -> terrain_z12/
python3 fetch_workings.py       # VicMine gold occurrence points (same WFS the app uses) -> workings.json
python3 build_npi.py            # -> ../../data/npi/{z}/{x}/{y}.png + npi-grid.png + npi-meta.json + tiles-manifest.json
```

`build_npi.py` caches the heavy per-region compute to `cache_*.npz`, so re-running to
re-tile (e.g. tweak `NLEV`, the colormap, or the popup-grid packing) is near-instant.

## What it computes (per 100 m–ish cell, heuristic v0)

```
NPI = 0.35*dist_to_reef + 0.25*workings_density + 0.15*drainage_convergence
    + 0.15*favourable_slope + 0.10*bedrock_exposure          (scaled 0–100)
```

- **DEM** — AWS terrarium terrain tiles (z12). SRTM-derived; no public Victorian LiDAR
  tile service exists yet, so the whole region is SRTM-grade (surfaced honestly in the UI).
- **dist_to_reef** — distance transform from the app's goldfield + endowment polygons.
- **workings_density** — count of VicMine gold occurrences within 500 m (`min(1, n/5)`).
- **drainage** — D8 priority-flood flow accumulation (`log(1+acc)/log(100)`).
- **slope** — peaks at 17.5°, falls to 0 at 0° and 35°.
- **bedrock** — favourable-slope × convex-curvature proxy.

## Outputs

| File | What |
|------|------|
| `data/npi/{z}/{x}/{y}.png` | palettised RdYlGn heatmap tiles, z10–12 native (browser upsamples 13–14) |
| `data/npi/npi-grid.png` | packed component grid (z8 ~490 m cells) for tap-to-explain; alpha = validity mask only (canvas premultiplies alpha — never store data there) |
| `data/npi/npi-meta.json` | bbox, grid geo-referencing, weights, limitations, sample spot scores |
| `data/npi/tiles-manifest.json` | every tile path, so the service worker can precache the region for offline use |

Regenerate whenever the reef polygons, occurrence data, or weights change — or to retrain
on Steven's confirmed gold events for personal calibration (a future version).
