# AuraGold Night Log

Autonomous overnight session — Steven asleep, work until morning, make it "super aura".
Live: https://banksiasprings.github.io/auragold/ · repo banksiasprings/auragold
Env notes: git push works directly via Bash (no osascript needed). Verify via preview MCP + headless Chrome (`/Applications/Google Chrome.app/.../Google Chrome --headless=new --screenshot`). Bump `SHELL_VERSION` in sw.js every round.

Priorities (Steven): (1) relocate 12 spot pins onto geofence-verified legal ground; (2) mag-RTP + LiDAR/DEM overlays; (3) mark/save waypoints on phone; (4) field-grade polish.

---

## Round 1 — Spot relocation — 2026-06-28 (overnight)

### Completed
- v5 (`3295a1d`): Relocated all 12 spot pins from town centroids onto geofence-verified legal ground (State Forest / Crown), 0.7–5.6 km moves. All 12 now resolve green (sf/crown) via offline point-in-polygon. Added `land` field per spot → popup shows "✓ Pin on permitted ground: <land>". Verified ✓ (preview, spot-10 popup screenshot, all-12 geofence pass, no console errors).
  - Spot 6 (Whroo) deliberately moved OFF Puckapunyal military land → Crown land nr Whroo.
  - 3 & 6 landed on Crown land (legal/green) rather than SF; others on named State Forests.

### Observations (not acted on)
- Spots 3 & 6 are on uncategorised Crown land; could be nudged onto Dunolly SF / Rushworth SF respectively for "nicer" labels, but Crown is legally permitted — left as-is.
- subSpots layer still uses original coords (fine — they're supplementary, not the headline pins).

---

## Round 2 — Geophysics / terrain overlays — 2026-06-28 (overnight)

### Completed
- v6 (`f963984`): Added two ☰-menu toggle overlays. 🧲 Magnetic RTP = GA `geophys:magmap_v7_2019_RTP` WMS (services.ga.gov.au/gis/geophysical-grids/wms) — TMI variable-reduction-to-pole, reads basement structure/fault & reef trends. ⛰️ Hillshade = Esri World_Hillshade XYZ. Both default off, 0.6 opacity, maxNativeZoom caps, legend entries, attribution. Verified ✓ (both render over Wedderburn, no console errors; SW caches on view for offline).

### Observations
- Mag RTP is greyscale (classic structural image). GA also has an HSI colour TMI (`geophys:tmi_hsi_v2_white`) if a colour version is preferred later.
- "LiDAR" delivered as Esri global hillshade (reliable). True Vic high-res LiDAR-DEM hillshade (Vicmap Elevation) could be swapped in later for finer old-workings detail.

---
