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

## Round 3 — Mark & save waypoints — 2026-06-28 (overnight)

### Completed
- v7 (`3b53625`): On-device, offline waypoint capture (localStorage key `auragold_waypoints`). 🎯 "Got a hit!" FAB = one-tap find at live GPS (fallback map centre). Long-press map → type chooser (find/signal/hole/camp/note), coloured teardrop markers w/ popup (note, time, ±acc, coords, delete). "🎯 My finds (N)" menu button → panel: list (tap→fly-to, delete), Export GPX (Garmin/Google Earth) + JSON + clear-all, confirmation toasts. Saved-finds layer toggleable. Verified ✓ (got-a-hit, long-press 5-type chooser, persistence, panel list, GPX+JSON export filenames, no console errors, screenshot).

### Observations
- Photos/voice memos (roadmap) would need IndexedDB (localStorage too small for blobs) — deferred, bigger lift.
- Browser `Date.now()`/`new Date()` used for timestamps/IDs — fine in page JS (the no-Date rule is Workflow-script-only).

---

## Round 4 — Field-grade polish — 2026-06-28 (overnight)

### Completed
- v8 (`c8bf457`): Screen **Wake Lock** while GPS tracking (re-acquired on visibility change, guarded). **Nearest-spot** readout in the status pill ("◎ #10 4.0km NW", great-circle bearing). **Online/offline badge** ("📴 Offline — using saved maps"). Mobile **header trimmed** to "🪙 AuraGold" (`.hfull` span hidden <560px). Verified ✓ (nearest in pill, header one line, no errors; wake-lock API present, offline toggle reads navigator.onLine).

## Round 5 — Breadcrumb walked-track — 2026-06-28 (overnight)

### Completed
- v9 (`9827cc1`): Records walked path while tracking — downsampled (>15 m) blue dashed polyline, persisted to localStorage (cap 5000, throttled + flush on background), toggleable "🥾 My walked track" layer, included as a GPX `<trk>`; "Clear points & track" resets both. Verified ✓ (6-pt polyline, GPX trkpt, menu toggle, no errors).

---

## ✅ CHECKPOINT — Rounds 1–5 complete (all 3 Steven priorities + 2 polish rounds)

**Live & verified:** https://banksiasprings.github.io/auragold/ — SW v9, commits fe671d5→9827cc1.
**Shipped:** (1) 12 spots relocated onto geofence-verified legal ground; (2) magnetic-RTP + hillshade overlays; (3) mark/save waypoints (got-a-hit, long-press, finds panel, GPX/JSON export); (4) wake-lock + nearest-spot + offline badge + mobile header; (5) breadcrumb track.

**Env for next agent:** git push works via plain Bash (no osascript). Verify via preview MCP (`preview_start` name `auragold`, serves `~/Documents` so app is at `/auragold/`; clear SW + `location.reload(true)` to bust cache-first) and/or headless Chrome screenshot (`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --screenshot=... --window-size=... <url>` — it hangs on exit but writes the PNG first). Bump `SHELL_VERSION` in sw.js EVERY round. Keep it surgical; defer risky/uncertain changes; log here; commit+push per round.

**Next-round backlog (priority order, all additive/low-risk unless noted):**
1. Photo per waypoint — `<input type=file accept=image/* capture>` → IndexedDB blob + thumbnail in the finds popup/list (MODERATE: IndexedDB + storage; keep behind the existing waypoint model). 
2. "Navigate to spot" — from the finds/spot popup, draw a line + live distance/bearing from GPS to a chosen target.
3. Settings panel — opacity sliders for 🧲 mag / ⛰️ hillshade, default base map, units. Low risk.
4. Today/itinerary view — surface routeOrder + the day field ("today's spot, next stop").
5. True Vic LiDAR hillshade — research a Vicmap Elevation hillshade WMS to swap for the Esri global one (finer old-workings detail).
6. Nudge spots 3 & 6 from Crown land onto State Forest proper (Dunolly SF / Rushworth SF) for nicer labels (cosmetic).
7. QA pass: go offline (DevTools) after caching, confirm map + overlays + waypoints all work; test 320px & tablet viewports.

**Still OPEN (needs Steven, not an agent):** repo lives at `banksiasprings/auragold`; moving to org `banksiaspringsfarm-rgb` needs an org-owner action (see Day-1 notes / memory `github-org-repo-permissions`).

---
