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

## ✅ CHECKPOINT 2 — Rounds 6–8 complete

**Live & verified:** https://banksiasprings.github.io/auragold/ — **SW now v12**, commits `d42eeca`→`5f13637` (next commit uses **v13**).
**Shipped this session:** (6) photo per waypoint (IndexedDB blob + thumbnail in popup & finds list + fullscreen viewer); (7) navigate-to-target (line + live distance/bearing banner from GPS to any spot/find); (8) Settings panel (overlay opacity sliders, default base map, km/mi units, persisted).

**Env reminder for the continuing agent (unchanged):** git push via plain Bash (`cd /Users/openclaw/Documents/auragold && git add -A && git commit -m "..." && git push origin main`; end commit msgs with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`). Verify via preview MCP: `preview_start` name `auragold` (app at `http://localhost:8087/auragold/`); to bust the cache-first SW in `preview_eval`: unregister SWs + delete any cache whose name contains "shell" + `location.reload(true)`, wait ~4s. Test hooks on `window.AuraGold`: `simulateGPS(lat,lng,acc)`, `navigateTo(lat,lng,label)`, `fmtDist(km)`, `addWaypoint`, `geofenceAt`, `lastFix`. **Bump `SHELL_VERSION` in sw.js EVERY commit.** Surgical edits only; DEFER anything touching geofence math / permitted_land data / the waypoint save format, or needing >50 interconnected lines. Reset any test data (localStorage `auragold_waypoints`/`auragold_settings`, IndexedDB `auragold_photos`) before finishing so Steven gets a clean slate.

**Remaining backlog (priority order):**
4. **Today/itinerary view** — use the existing `routeOrder` array + each spot's `day` field to show "today's / next spot" and let the user step through the itinerary. (Check: `grep -n "routeOrder\|\.day\b" index.html`.)
5. **True Vic LiDAR hillshade** — research a working Vicmap Elevation / DELWP hillshade WMS (try `opendata.maps.vic.gov.au` geoserver or `services.land.vic.gov.au`); if reliable, add/swap alongside the Esri global hillshade. **Verify tiles actually return imagery** before wiring. (Needs WebFetch/WebSearch — load via ToolSearch.)
6. **Nudge spots 3 & 6** from Crown land onto State Forest proper (Dunolly SF / Rushworth SF) — re-run the geofence (`data/permitted_land.json` + the point-in-polygon) to pick a green State-Forest coord near each; update spot lat/lng + land label. Cosmetic. ⚠️ This one DOES touch the geofence/data — only do it if confident; the brief explicitly allows it as a careful one-off, but defer if shaky.
7. **QA pass** — cache the app, verify via the caches API that shell + tiles + permitted_land are cached; confirm all features work; test mobile 320px and tablet widths. Log a QA summary. Then write the final "## MORNING SUMMARY" (everything shipped overnight with commit hashes + live URL) and stop.

---

## Round 6 — Photo per waypoint — 2026-06-28 (overnight)

### Success criterion
Attach a camera/gallery photo to any saved waypoint; thumbnail shows in both the marker popup and the finds-list row; tap to view fullscreen; localStorage waypoint model unchanged; deleting a waypoint removes its photo.

### Completed
- **v10 (`d42eeca`)**: Photo per waypoint, fully on-device & offline.
  - `<input type=file accept="image/*" capture="environment">` (one hidden input, reused). 📷 button in every finds-list row AND in the waypoint popup ("📷 Add photo" / "📷 Replace photo").
  - Blobs stored in **IndexedDB** (`db auragold_photos`, store `photos`) keyed by waypoint id. localStorage model untouched — just a `wp.photo` boolean flags presence (so existing waypoints & GPX/JSON export are unaffected).
  - Thumbnails (38px in list, ≤140px in popup) + **fullscreen viewer** on tap (dark overlay, × to close).
  - Delete a waypoint or clear-all → its blob is removed from IndexedDB (verified **no orphans**).

### Key implementation note (the bug I hit & fixed)
- First attempt appended the thumbnail to a `[data-ph]` slot **asynchronously after `popupopen`**. It worked for the finds-list but **silently failed in the map popup**: Leaflet **re-parents the popup content node ~300 ms after `popupopen`** (animation/positioning reflow), so the slot reference the handler captured becomes detached (`isConnected → false`) and the async append landed on an orphan. Verified directly: `connectedAtOpen:true → connectedLater:false`, `sameNodeInDom:false`.
- Fix: **pre-cache object URLs** (`purls{id→blobURL}`, populated by `preloadPhotos()` on load and on each attach) and **embed `<img src=blobURL>` inline in the render() HTML** — fully synchronous, zero post-open DOM surgery. Robust for both surfaces.
- Also hardened `idb()` to **queue** waiters instead of overwriting `_dbReq.onsuccess` (the old code dropped all-but-the-last concurrent caller).

### Verified ✓ (preview MCP, fresh SW bust each time)
- Real production path (constructed File → dispatched `change` on the hidden input): blob stored, `wp.photo:true`, thumbnail rendered in list (`thumbsInList:1`).
- Popup thumbnail renders (`thumbInPopup:1`, `complete:true`, `naturalWidth:80`, `src:blob:`) — screenshot confirms gold "Au" test image inline with Replace/Delete buttons.
- Fullscreen viewer opens on thumbnail tap (dark overlay screenshot) and closes cleanly (img src cleared).
- Delete via list Del → waypoint gone, thumbnail gone, **IDB blob cleaned** (`result:"cleaned"`).
- **No console errors** at any point. Map/spots/overlays/markers all still render. Test data wiped — clean slate left for Steven.

### Observations (not acted on)
- Photos are NOT yet included in GPX/JSON export (GPX has no native image field; JSON could embed base64 but would bloat localStorage exports). Left out deliberately — log only.
- The fullscreen viewer has no swipe/zoom; fine for a quick "what did I photograph here" check.

---

## Round 7 — Navigate to target — 2026-06-28 (overnight)

### Success criterion
From a spot popup (and waypoint popup), a "Navigate" action draws a line + shows live distance & bearing from the GPS dot to that target, updating on each fix.

### Completed
- **v11 (`b18618d`)**: "🧭 Navigate here" on every **spot** popup and **waypoint** popup.
  - Tapping it draws a **green dashed polyline** from the live GPS dot to the target and shows a **green banner** (top-center, below the status pill): `🧭 <dist> <compass> / to <label> · <bearing>°`.
  - **Live**: updates on every GPS fix via a one-line `navUpdate` hook added to `onPos` (mirrors the existing `recordTrail` hook). Haversine distance (km/m auto), true great-circle bearing + 8-point compass.
  - On start, fits both points in view (or flies to target if no recent fix). Banner's **×** stops nav (removes line + banner).
  - If there's no recent fix (>5 min), the banner prompts "tap 📍 Locate for live distance" and hides the line until a fix arrives.
  - Self-contained new `<script>` IIFE. **Did NOT touch** the geofence math, permitted_land data, or the waypoint save format. Click handling is event-delegated via `map.on('popupopen')` reading `[data-nav]`/`[data-navlabel]`.

### Verified ✓ (preview MCP, fresh SW bust)
- `simulateGPS(-36.45,143.55)` + `navigateTo(-36.42,143.50,'#10 Wedderburn')` → banner "🧭 5.58 km NW to #10 Wedderburn · 307°", green line with 2 points (GPS→target).
- Moved GPS closer (`simulateGPS(-36.43,143.51)`) → banner live-updated to "1.43 km NW · 321°", line **start** moved to new GPS pos, **end** stayed at target. Live update confirmed.
- Real popup path: opened a spot popup, **clicked** the "🧭 Navigate here" button → nav started (35.6 km SE · 114°), popup closed. Event delegation works.
- Stop **×** → banner hidden, line removed.
- Banner positioned at top:142px, status pill bottom 125px → **no overlap** (was 80px, fixed). Screenshot (mobile 375px) shows both stacked cleanly + the green dashed line GPS→target.
- **No console errors.** Map/spots/overlays/markers/photos all still render.

### Observations (not acted on)
- The line is a straight rhumb-ish great-circle chord, not road-routed (intentional — offline field nav with no routing engine; matches the dispatcher/heading style).
- A live compass-heading arrow on the GPS dot (device orientation) could be a nice future polish — deferred.

---

## Round 8 — Settings panel — 2026-06-28 (overnight)

### Success criterion
New ☰-menu "⚙ Settings" item → panel with opacity sliders for 🧲 Magnetic RTP & ⛰️ Hillshade, default-base-map choice, km/mi units. Persist to localStorage.

### Completed
- **v12 (`5f13637`)**: ⚙ Settings (localStorage key `auragold_settings`, defaults `{opMag:60,opHill:60,base:'sat',units:'km'}`).
  - **Opacity sliders** (10–100%, step 5) for mag & hillshade — live `setOpacity()` on the layer + persisted + value readout.
  - **Default base map** radio (Satellite / Topographic / Street) — applied on next load (the map script's default Satellite is overridden by the persisted choice), persisted. The ☰-menu base radios and the settings default-base radios stay **bidirectionally in sync**.
  - **Distance units** km/mi radio. Drives a new shared `window.AuraGold.fmtDist(km)` used by the **navigate banner** (Round 7) and the **nearest-spot status readout** (both fall back to a km formatter when settings haven't loaded). Switching units re-fires `navUpdate` so the banner reformats instantly.
  - Matches the gold theme (gold accent-color sliders/outputs, green radios). Opening Settings closes the ☰ menu (no panel overlap).

### Verified ✓ (preview MCP, fresh SW bust)
- Panel opens; defaults correct (60%/60%/sat/km); `fmtDist(5.58)→"5.58 km"`, `fmtDist(0.43)→"430 m"`. Screenshot confirms layout.
- Mag opacity slider → 30%: live layer opacity `0.3`, output "30%", persisted `opMag:30`.
- Units → miles: nav banner live-reformatted **"5.58 km NW" → "3.47 mi NW"** (5.58×0.621371=3.47 ✓), persisted `units:'mi'`.
- Default base → Topographic: topo becomes the only active base, ☰-menu radio synced to "Topographic", persisted `base:'topo'`.
- **Reload test**: app re-opened on **OpenTopoMap** (not Satellite), mag slider restored to 30, units restored to miles — all persisted settings applied on load (screenshot confirms topo base + © OpenTopoMap attribution).
- **No console errors.** Spots/camps/route/overlays still render. Settings wiped — clean default slate left for Steven.

### Observations (not acted on)
- Opacity only applies to the two geophysics/terrain overlays (the ones with a meaningful 0–1 opacity); the WMS data overlays keep their tuned opacities. Intentional.
- A "reset to defaults" button could be added; trivial, deferred (clearing the key in devtools or reinstall resets it).

---
