# AuraGold v41 — 3D terrain view (Vic goldfields, online-only)

**Approved by Steven 2026-07-01 — fires AFTER v40 (legality audit + green overlay) ships.**

## Scope

Add a **fullscreen 3D terrain view** toggle that lets Steven tilt/pitch/rotate the map in Google Earth style. Coverage restricted to the existing NPI-heatmap bounding box (Victorian Golden Triangle + Chiltern) — NOT Australia-wide. That's a future scope.

## Explicit constraints

- **3D mode is ONLINE-ONLY.** When user is offline, a friendly toast: "3D view needs data — reconnect to load terrain." No pre-caching of DEM tiles. Storage stays lean.
- **2D mode stays fully offline-capable**, unchanged. All existing v39 layers keep working.
- **Coverage bbox**: same as `tools/npi/build_npi.py` bounding boxes — Western goldfields region + Chiltern. Don't attempt to load terrain outside that. If user pans outside → grey out or clip cleanly.
- **Future roadmap**: Australia-wide is a "another day" project. Do NOT design for it now. Simple bounded region only.

## Architecture

Do NOT rebuild the primary 2D map on top of MapLibre. Instead:
- **Keep Leaflet as the 2D primary** (all existing layers, popups, offline behaviour)
- Add a **new fullscreen 3D view overlay** rendered with **MapLibre GL JS**, opened by a `🌍 3D View` toggle button on the map
- Round-trip back to 2D via a close button on the 3D view
- Both views share the same map centre and zoom so switching preserves context

## Tech stack

- **MapLibre GL JS** (open source, WebGL, actively maintained). Bundle via CDN import or ship inline.
- **DEM elevation tiles**: AWS Terrain Tiles (Terrarium encoding) — `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`. Free, no auth. That's what MapLibre expects. Alternative: Mapbox Terrain-RGB if AWS unreachable.
- **Basemap drape**: Esri World Imagery (satellite) as the raster on top of terrain
- **NPI heatmap drape**: the same tile pyramid we already generate for 2D. MapLibre can drape raster tiles over 3D terrain trivially.
- **Pins**: render Steven's KML placemarks (12 main + 12 sub + 6 camps + 3 top-10 lists) as 3D markers/billboards at their actual elevation

## Feature checklist

- [ ] `🌍 3D View` button on 2D map (top-right, near Layers button)
- [ ] Tap → fullscreen MapLibre view opens, centred on current 2D position
- [ ] Terrain rendered at good visual quality (exaggeration 1.5-2× is usually good for prospecting terrain — flat coastal plains look boring at 1× but ridges pop at 2×)
- [ ] Esri satellite draped by default; toggle to switch to NPI heatmap drape
- [ ] Detector-variant selector (VLF / PI / ZVT) — same as 2D — drives which heatmap drapes
- [ ] Steven's KML pins (12+12+6) render as 3D markers with popup on tap
- [ ] Top-10 detector layers (from v38, refreshed by v40) toggleable in 3D too
- [ ] Compass/tilt/rotate controls (MapLibre defaults are fine)
- [ ] Close button → back to 2D preserving position and zoom
- [ ] Loading state while terrain tiles fetch
- [ ] Offline detection → friendly "reconnect for 3D" toast
- [ ] Out-of-bbox detection → grey-out with "3D coverage is Vic goldfields only" note

## Performance guardrails

- **Load test on Motorola Edge 50 Neo** before shipping. If FPS drops below 30, reduce terrain resolution.
- Set MapLibre `maxZoom` sensibly (terrain gets grainy above z14). Don't let user zoom beyond usable resolution.
- Lazy-load MapLibre bundle — only fetch when user first taps 3D toggle. Don't tax the 2D-only user.

## What NOT to do

- **No offline caching of DEM tiles.** Explicit Steven ask — keep storage lean.
- **No Australia-wide coverage** — Vic goldfields bbox only.
- **No rebuild of the 2D map.** MapLibre is a sidecar, not a replacement.
- **No 3D-only features that break the 2D workflow.** Everything Steven does in 3D must have a 2D equivalent since 3D goes dark offline.

## Report on ship

- Screenshot of Wedderburn area in 3D with NPI heatmap draped and terrain exaggeration at 2×
- Load-test result on Steven's phone (FPS, memory, startup time)
- Storage footprint (should be <1MB added for the MapLibre bundle since DEM is online-only)
- One-line: "Steven can now tap `🌍 3D View` and Google-Earth the Vic goldfields, tilted and shaded, with heatmap or satellite draped over the real terrain."

## Bonus if there's room

- **Cross-section profile tool** — tap two points on 2D map, see slope profile / creek gradient as a side-elevation SVG chart. Prospecting-useful for "how steep is that walk-in" reads. Small effort (~2 hours). Can bundle into v41 or ship as v41.5.
- **Aspect-arrow overlay** — 2D but overlays little compass arrows showing which way slopes face (matters for morning shade timing, especially in winter).

Both bonuses go on the wishlist, not the must-do.
