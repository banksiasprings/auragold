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

## Round 9 — Today / Trip itinerary view — 2026-06-28 (overnight)

### Success criterion
A new ☰-menu "🗺 Trip itinerary" item opens an `ag-panel` listing the 9 main spots in `routeOrder` driving sequence, each showing its `day` label + name; tapping a row closes the panel, jumps the map to that spot and opens its popup. Surfaces the day grouping already in the data. Additive — no existing behaviour changed.

### Completed
- **v13 (`507e47f`)**: 🗺 Trip itinerary stepper.
  - New ☰-menu **"🗺 Trip itinerary"** button (Tools section, between My finds and Settings) → new `<aside id="itineraryPanel">` (same `.ag-panel` + header + `.ag-body` template as Settings/Finds).
  - Panel renders the 9 `routeOrder` spots `[12,5,6,2,1,4,3,7,10]` **in driving order** (Day 4 → Days 14–15). Each row = a **status-coloured number badge** (green/orange/red from `statusColors`), the gold **day label** on its own line, and the **spot name** below, with a `›` chevron. New `.itin-row/.itin-num/.itin-body/.itin-day/.itin-name/.itin-go` CSS, gold theme.
  - **Tap a row** → closes the panel, `map.setView([lat,lng], max(zoom,12), {animate:false})`, then `marker.openPopup()` (60 ms later). Surfaces the full spot popup (day, desc, permitted-ground label, Navigate button).
  - Minimal enabler: captured the 12 spot markers into a new global `spotMarkersById{n→marker}` during the existing `spots.forEach` (the only change to existing code — one `const m =` + one assignment). Self-contained new `<script>` IIFE for the rest. Exposes `window.AuraGold.openItinerary()`.
  - A footnote in the panel notes side-trips (rainy-day / detour / optional — spots 8, 9, 11) sit outside the main run and aren't in this ordered list, but remain on the map as numbered pins. Did NOT touch geofence math, permitted_land data, or the waypoint format.

### Implementation note (the one thing I changed mid-round)
- First cut used `map.flyTo(..., {duration:0.8})`. The **flyTo/animated-setView zoom animation does not complete in the headless preview** (rAF-throttled) — center crept toward the target but zoom stayed put, so verification couldn't confirm the jump. Switched to `setView(..., {animate:false})`: instant, deterministic, verifies cleanly here AND is snappier UX in the field (tap → you're there, no 0.8 s zoom-out-zoom-in). Popup-open delay trimmed 850 ms → 60 ms to match.

### Verified ✓ (preview MCP, fresh SW bust each edit, mobile 375px)
- 9 itinerary rows built from `routeOrder`, correct driving order Day 4 → Days 14–15; badge colours match each spot's status; `spotMarkersById` has all 12 markers.
- Real-user path: ☰ menu button opens menu → "🗺 Trip itinerary" button **closes the menu and opens the itinerary panel** (no overlap).
- Tap row #7 (Inglewood): panel closed, **map centre moved to -36.559,143.874 (= target), zoom 12**, popup opened ("7. Inglewood / Kingower / Wehla SF" — screenshot shows DAY 13, desc, ✓ Inglewood State Forest, Navigate button). Tap row #12 (Chiltern) jumped correctly too.
- Day/name spacing fixed (`.itin-body` flex-column) — screenshot shows gold day label above bold name on every row.
- **No regressions**: menu / finds / settings panels all still open+close, menu-close-on-other-panel still works, spots render, `map.hasLayer(spotGroup)` true, 12 markers intact. **No console errors.** No test data created (read-only feature) — slate already clean.

### Observations (not acted on)
- Side-trip spots (8 Hepburn rainy-day, 9 Maldon detour, 11 Wombat optional) are intentionally excluded from the ordered list since they have no fixed day slot in `routeOrder`; they're noted in the panel footnote and still tappable as map pins. If Steven wants them, they could append as an "Optional side-trips" sub-section — logged, not built.

---

## Round 10 — True Vic LiDAR hillshade — DEFERRED — 2026-06-28 (overnight)

### Outcome: DEFERRED (no code change, no SW bump, no commit)
Per the brief: "If you cannot confirm a reliable tile endpoint, DEFER this item with a note of what you tried — do not wire a dead layer." I could **not** confirm a public, directly-tileable Victorian LiDAR hillshade endpoint, so I left the existing Esri global hillshade in place (untouched) and did not wire anything dead. Zero regression risk.

### What I researched (all dead-ends for a wire-in-ready hillshade tile URL)
1. **`opendata.maps.vic.gov.au/geoserver` WMS** (the modern Vicmap open-data GeoServer) — fetched GetCapabilities. It lists hundreds of layers (admin boundaries, addresses, minerals, hydro, fire, buildings, tenure) but **no elevation / hillshade / relief / DEM / DTM / terrain / LiDAR layer at all**. Not served here.
2. **`services.land.vic.gov.au/.../dv_geoserver/wms`** (the legacy DELWP WMS often cited for this) — **connection refused / unreachable** from the fetcher (ECONNREFUSED on https, the http variant the docs give wouldn't resolve). Could not enumerate or sample it. Even if reachable it's the deprecated pre-migration endpoint.
3. **Vicmap Basemaps WMTS `base.maps.vic.gov.au/service`** — fetched GetCapabilities. Real, live, image/png, has a Web-Mercator `EPSG:3857:256` (GoogleMapsCompatible) tile matrix — **but the only layers are `CARTO_*` (cartographic) and `AERIAL_*` (aerial). No hillshade/relief/terrain layer.** So the official Vic basemap WMTS can't supply it either.
4. **ELVIS (`elevation.fsdf.org.au`) / Geoscience Australia** — ELVIS hosts the Digital-Twin-Victoria LiDAR DEM and *renders* hillshade in its own TerriaJS viewer, but exposes it for **discovery + download**, not as a stable public hillshade tile/WMS URL I could find. The GA elevation WMS service paths I tried (`gaservices.ga.gov.au/site_9/.../DEM_SRTM_1Second...`, `services.ga.gov.au/`) returned 404 / 403 to the fetcher, and the candidate national hillshade is SRTM-30m (DEM-S) — i.e. **not** the fine LiDAR detail this item is about, so even if wired it wouldn't deliver the "finer old-workings detail" goal.

### Why not just guess a layer name and wire it
The brief mandates verifying a sample GetMap/tile actually returns non-blank imagery **before** wiring, and WebFetch can't retrieve binary tile responses to confirm that. Wiring an unverified WMS layer risks a silent blank/error layer in the field — exactly the "dead layer" the brief says to avoid. The existing Esri `World_Hillshade` (Round 2) already gives reliable global relief; nothing is lost by deferring.

### Recommendation for Steven / a future session (HITL)
A working Vic-LiDAR hillshade almost certainly exists behind one of: (a) the migrated DEECA GeoServer under a non-obvious workspace (the helpdesk `gis.helpdesk@delwp.vic.gov.au` / `vicmap@transport.vic.gov.au` can name the exact layer), or (b) an ELVIS/ICSM raster tile service whose URL is in the live viewer's TerriaJS catalog JSON (inspect `elevation.fsdf.org.au` network traffic in a real browser to capture the tile URL, then verify a tile loads). Both need a real browser network-trace or a helpdesk reply — out of scope for an offline autonomous round. Captured here so it isn't re-litigated blind.

---

## Round 11 — Nudge spots 3 & 6 onto State Forest — 2026-06-28 (overnight)

### Success criterion
Move spots 3 (Tarnagulla/Waanyarra, was Crown nr Dunolly) and 6 (Whroo, was Crown nr Rushworth) onto State-Forest-proper coordinates that resolve **green** via the in-app point-in-polygon geofence; update each spot's lat/lng + land label. Cosmetic. ⚠️ Touches the spots data → only proceed where confident; defer if shaky.

### Completed — SPOT 3 only (`a7ecdd9`, SW v14)
- Re-ran the **exact in-app geofence** (`pip` ray-cast + `geofenceAt` over `data/permitted_land.json`, reproduced in a node script) to search a grid around spot 3 for a point that sits **solidly inside** Waanyarra-Dunolly SF (not on an edge that a GPS wobble could flip to Crown).
- **Spot 3: `-36.7450,143.8305` (Crown "Uncategorised Public Land") → `-36.7750,143.8401`** — resolves `sf` **"Waanyarra - Dunolly State Forest"**; the full ~120–240 m surround is also SF (1.0 solid). 3.4 km move, stays within the spot's own Tarnagulla/Waanyarra/Dunolly cluster. Land label updated `"Crown land nr Waanyarra / Dunolly SF" → "Waanyarra - Dunolly State Forest"`. Only the lat/lng + land string changed; desc/status/day untouched.

### DEFERRED — SPOT 6 (Whroo) — deliberate, logged not done
- Searched outward from Whroo (`-36.8450,145.0680`) for the nearest State Forest of **any** name: **Rushworth SF ≈ 10.3 km, Redcastle-Greytown SF ≈ 10.0 km.** There is **no State Forest within ~10 km** of the Whroo coordinate. Moving spot 6 onto SF would drag it right off the Whroo ghost-town goldfield it's named for and described around (Balaclava Hill, the 1850s field) — that's a relocation, not a cosmetic nudge.
- Whroo's current Crown land (`"Adj Major Ck Frontage"`) already resolves **green/legal**. So nothing is gained and the spot's meaning is lost. Per the brief's explicit "if shaky, DEFER", spot 6 is **left as Crown** — correct and legal.

### Verified ✓ (node geofence replica + preview MCP, fresh SW bust)
- New spot-3 coord `geofenceAt(-36.7750,143.8401) = {cls:'sf', name:'Waanyarra - Dunolly State Forest'}`; old coord was `{cls:'crown',...}` (confirming the move was needed).
- In the live app after reload: **all 12 spots still resolve green** (11 `sf` + spot 6 `crown`); spot-3 popup shows new coords + green "✓ Pin on permitted ground: Waanyarra - Dunolly State Forest" (screenshot — green pin now sits on the forest). **No console errors.**
- **Itinerary route line auto-updated**: `routeLatLngs[6]` (spot 3's slot in `routeOrder`) now reads `[-36.7750,143.8401]` — it's derived from the spots array, so no stale reference. Round-9 itinerary stepper, all panels, markers unaffected.

### Observations (not acted on)
- The Llanelly SF sits ~2.9 km from spot 3 (slightly closer than Waanyarra-Dunolly) but the brief named **Dunolly SF** specifically, and Waanyarra-Dunolly is the SF the spot's own description references (the camp + "surrounding Dunolly SF") — so Dunolly was the right target.
- subSpots layer still uses original coords (supplementary, unchanged — same note as Round 1).

---

## Round 12 — QA pass (offline cache + features + responsive) — 2026-06-28 (overnight)

### Scope
Verification-only round (no code change → no SW bump, no code commit). Cache the app, confirm via the **caches API** that shell + tiles + `permitted_land.json` are cached, confirm every feature works, test mobile **320px** and tablet **768px**.

### Offline cache — VERIFIED ✓ (caches API)
- Cleared all caches + SWs, reloaded → SW **v14 installed and took control** (`navigator.serviceWorker.controller` truthy).
- **`auragold-shell-v14`** holds all 15 shell entries: `/`, `index.html`, `manifest.webmanifest`, the 4 icons, **`data/permitted_land.json`**, and Leaflet css/js + 5 marker/layer images. `cache.match()` on permitted_land returns valid JSON with **2386 features** → the offline geofence works with no network.
- Panned/zoomed the map → **`auragold-tiles-v1`** populated with **32 base tiles** (Esri World_Imagery), cache-first. Tiles are cross-origin **opaque** (read as status 0 / 0 bytes to JS — *expected*), but a plain `<img>` load of a cached tile decodes to a real **256×256** image and **16 tiles render on the map** → tiles are genuinely cached & usable offline.

### Features — VERIFIED ✓ (all green, no console errors anywhere in the session)
Map loads · 12 spot markers · spotGroup on map · geofence ready (spot 3 = `sf`) · **add-waypoint** increments count · **navigate** banner shows + stops · **trail** hook present · **fmtDist** = "5.58 km" · **itinerary** `openItinerary()` present · all 5 panels (menu/finds/settings/itinerary/checklist) exist · all 3 FABs (got-a-hit/menu/gps) present.

### Responsive — VERIFIED ✓
- **320px (smallest phone):** header trims to "🪙 AuraGold" (`.hfull` display:none); FABs + Menu all within the viewport (`withinX:true`); **no real horizontal scroll** (`body.scrollWidth === clientWidth`, window can't scroll right — the only DOM "overflow" is Leaflet's own tiles, which its container clips with `overflow:hidden`). Itinerary panel = 93vw (~298px), fits, scrolls, names wrap cleanly (screenshot).
- **768px (tablet):** full header "🪙 AuraGold — Victoria Gold Prospecting" shows (`.hfull` inline); side panels cap at **400px** (don't stretch); no horizontal scroll; all 12 pins + route line + camps + SF polygons render over satellite imagery (screenshot — spot 3's green pin now sits inside the Dunolly SF outline).

### Clean slate left for Steven
- Wiped `auragold_waypoints` / `auragold_settings` / `auragold_trail` (all null) and IndexedDB `auragold_photos` (DB list empty). Offline shell + tile caches **intentionally kept** (those are the saved maps, not test data).

### QA verdict: SHIP-READY ✓
Offline-first PWA fully functional; all overnight features work; no regressions; no console errors; clean on 320px → 768px. Live at https://banksiasprings.github.io/auragold/ (SW v14).

---

## ✅ MORNING SUMMARY — 2026-06-28

**Live & verified:** https://banksiasprings.github.io/auragold/ · repo `banksiasprings/auragold` (branch `main`) · **service worker v14** · QA ship-ready, no console errors, clean 320px→768px.

Vanilla-JS offline-first Leaflet PWA. Everything below works with no signal (shell + permitted-land polygons precached; map tiles cache-first / "Save maps offline").

### Everything shipped overnight (rounds 1–12)
| Round | What shipped | SW | Commit |
|---|---|---|---|
| 1 | **12 spot pins relocated** onto geofence-verified legal ground (State Forest / Crown), each with a "✓ Pin on permitted ground" label | v5 | `3295a1d` |
| 2 | **🧲 Magnetic-RTP** (GA WMS) + **⛰️ Hillshade** (Esri) ☰-menu overlays for reading basement structure / relief | v6 | `f963984` |
| 3 | **Mark & save waypoints** offline — 🎯 "Got a hit!" one-tap, long-press 5-type chooser, finds panel, GPX/JSON export | v7 | `3b53625` |
| 4 | **Field polish** — screen wake-lock while tracking, nearest-spot readout, online/offline badge, trimmed mobile header | v8 | `c8bf457` |
| 5 | **Breadcrumb walked-track** — downsampled blue dashed trail, persisted, GPX `<trk>`, toggleable | v9 | `9827cc1` |
| 6 | **Photo per waypoint** — IndexedDB blob, thumbnail in popup + finds list, fullscreen viewer, orphan-free delete | v10 | `d42eeca` |
| 7 | **Navigate to target** — green line + live distance/bearing banner from GPS to any spot/find, updates each fix | v11 | `b18618d` |
| 8 | **⚙ Settings panel** — overlay-opacity sliders, default base map, km/mi units, all persisted | v12 | `5f13637` |
| 9 | **🗺 Trip itinerary** — steps the 9 main spots in driving order (Day 4→15) by day; tap → map jumps + popup opens | v13 | `507e47f` |
| 10 | True Vic LiDAR hillshade — **DEFERRED** (no verifiable public Vic hillshade tile endpoint; Esri hillshade kept) | — | `d7c1464` |
| 11 | **Spot 3 → Waanyarra-Dunolly State Forest** (was Crown); spot 6 (Whroo) **deferred** (nearest SF 10+ km, would leave its goldfield) | v14 | `a7ecdd9` |
| 12 | **QA pass** — caches API (shell+tiles+permitted_land), all features, 320px + 768px — ship-ready (no code change) | — | this entry |

### Deferred / needs Steven (HITL)
- **True Vic LiDAR hillshade (item 5):** no public Vicmap/DEECA/ELVIS hillshade *tile* endpoint could be confirmed without a real-browser network trace or a DEECA helpdesk reply (full trail in the Round 10 entry above). The reliable Esri global hillshade remains. Pick this up with a browser network-trace of `elevation.fsdf.org.au` or by asking `gis.helpdesk@delwp.vic.gov.au` for the exact layer.
- **Spot 6 / Whroo (item 6):** left on legal Crown land deliberately — the nearest State Forest is 10+ km away, so "nudging" it onto SF would relocate it off the Whroo goldfield. No action recommended.
- **Repo → org move:** still needs an org-owner action (unchanged from earlier checkpoints).

### State for any future session
git push works via plain Bash. Verify via the preview MCP (`preview_start` name `auragold`, app at `http://localhost:8087/auragold/`; bust the cache-first SW by unregistering SWs + deleting any "shell" cache + `location.reload(true)`, wait ~4 s). **Bump `SHELL_VERSION` in sw.js every code commit.** Test hooks on `window.AuraGold`: `simulateGPS`, `navigateTo`, `addWaypoint`, `geofenceAt`, `openItinerary`, `fmtDist`, `lastFix`, etc. `index.html` is ~one big self-contained file — `grep -n` then read ranges; never read it whole. Surgical edits only; defer anything touching the geofence math / permitted_land format / waypoint save format unless confident.

**Backlog items 4–7 are all resolved** (4 & 6-partial shipped; 5 & 6-Whroo deferred with full rationale; 7 QA done). Nothing left in the queue — stopping here.

---
