# 🪙 AuraGold

**An offline-first gold prospecting field map for the central Victorian goldfields.**

AuraGold is a vanilla-JS Progressive Web App you install to your phone's home
screen and run like a native app — no signal required in the field. It bundles a
Leaflet map of 12 candidate prospecting spots, camping waypoints, sub-spots, an
editable **trip planner**, and seven geological data overlays (gold
occurrences, 1+ Moz endowment zones, goldfield boundaries, active tenements,
bushfire scars, fossicking-permitted State Forest, restricted Crown land). Tap
**Save maps offline** once on wi-fi and the region's base imagery is cached for
use where there's no reception.

You run the whole trip from inside the app — reorder days, add your own waypoints
by GPS or by pasting a Google/Apple Maps link, share a place straight from Google
Maps on Android, and export the lot to GPX / KML / JSON. Nothing leaves the
phone; all trip data is stored locally in IndexedDB.

**Live app:** https://banksiasprings.github.io/auragold/

---

## Install on your phone

### iOS — Safari
1. Open **https://banksiasprings.github.io/auragold/** in **Safari**
   (must be Safari — Chrome on iOS can't install PWAs).
2. Tap the **Share** button (the square with the up-arrow).
3. Scroll down and tap **Add to Home Screen**.
4. Tap **Add**. The gold-nugget icon appears on your home screen — open it and it
   runs full-screen, no address bar.

### Android — Chrome
1. Open **https://banksiasprings.github.io/auragold/** in **Chrome**.
2. Tap the **⋮** menu (top-right).
3. Tap **Install app** (or **Add to Home screen**).
4. Confirm. The icon lands on your home screen and launches standalone.

### Before you leave reception
Open the app on wi-fi and tap **⤓ Save maps offline** (bottom-right). It
downloads the base satellite tiles for the whole trip region so the map still
draws when you're off-grid. Anything you pan over while online is also cached
automatically. All overlay data (spots, route, geology) is embedded in the app,
so it's always available offline.

---

## Trip planner

Open **☰ Menu → 🗺 Trip planner**. The app ships with a pre-built **Suggested
Plan v1** (the field-tested 16-day itinerary) so you start with something to
edit, not a blank screen.

- **Reorder days** — drag the **⠿** handle on the right of any day. The dashed
  orange route line on the map re-draws to follow your new day order. (Devices
  without drag support get **▲ / ▼** buttons instead, and every day editor has
  *Move up / Move down* as a fallback.)
- **Edit a day** — tap it to set a label and date, add stops, and write notes.
- **Add stops** — from the day editor: **⛏ Spots** and **⛺ Camps** pick from the
  built-in library; **📍 Custom** drops your own point (GPS, manual lat/lng, or a
  pasted map link).
- **Trip actions** (**⋯**) — rename, duplicate, switch between trips, reset to the
  suggested plan, or **export to GPX / KML / JSON**.
- **🧭 Navigate to next stop** jumps the navigate banner to the first stop in your
  plan. Everything **auto-saves** on this phone — no save button.

### Adding a place by pasting a link

In the **📍 Custom** screen, paste into *“Paste a map link”* and tap **Detect**.
Supported: Google Maps long links (`/@lat,lng…` and the `!3d…!4d…` pin), Google
`?q=lat,lng`, Apple Maps (`?ll=…&q=…`), `geo:lat,lng` links, and plain
`lat, lng` text. The detected name and coordinates fill in for you to confirm.

> **Short links** (`maps.app.goo.gl/…`, `goo.gl/maps/…`) can't be expanded
> offline — a browser request to them is blocked by CORS. Open the short link in
> your browser first, then copy the full URL from the address bar and paste
> *that* instead.

### Share from Google Maps (Android)

AuraGold registers as a **Web Share Target**, so on **Android Chrome** (with the
app installed) it appears in the system share sheet:

1. In **Google Maps**, open any place and tap **Share**.
2. Pick **AuraGold** from the share sheet.
3. AuraGold opens with an **Add shared place** card pre-filled with the name and
   coordinates — choose a type and which day to add it to, then save.

> **iPhone / iPad:** iOS Safari does **not** support Web Share Target for
> installed PWAs (still true as of mid-2026), so AuraGold will **not** appear in
> the iOS share sheet. This is an Apple limitation, not a bug. On iOS, copy the
> place's address/link in Maps and use **📍 Custom → Paste a map link** instead.

---

## Shipped

**Day 1 — base map**

- Full Leaflet map ported from the field-tested trip map — 12 candidate spots
  with popups, camps, sub-spots, itinerary route line, legend, layer toggles.
- 7 geological overlays: 5 embedded (always offline) + 2 live WMS layers from
  Resources Victoria (cached as viewed).
- Installable PWA: web manifest, gold nugget icon set (48–512 px + maskable +
  Apple touch icon + favicon), standalone display, theme color.
- Service worker with a cache-first strategy: app shell + Leaflet precached on
  install; map tiles and WMS overlays cached at runtime.
- One-tap **Save maps offline** to pre-cache the region's base imagery.

**Field tools**

- Live GPS dot + permitted-area geofence + breadcrumb walked-track.
- Tap-to-drop / long-press waypoints (find / signal / hole / camp / note),
  **🎯 Got a hit!** one-tap log, photo capture, GPX / JSON export of finds.
- On-screen version badge + Settings **Force fresh download**.

**Phase 2 — trip planner (this round, v19)**

- Editable trip document in IndexedDB (`auragold_trips` +
  `auragold_user_waypoints`, DB bumped to v2), pre-seeded with the 16-day
  Suggested Plan v1.
- Day list with drag-reorder (SortableJS, precached for offline) + arrow
  fallback; inline day editor; spots/camps library pickers; custom waypoints by
  GPS, manual lat/lng, or pasted map link.
- The dashed route line follows the active trip's day order live.
- Multiple trips: rename, duplicate, switch, reset, delete; export GPX / KML /
  JSON.
- **Web Share Target** (Android) + universal **paste-URL** parser (Google /
  Apple Maps, `geo:`, plain `lat,lng`).

## Roadmap

- Voice memo via the MediaRecorder API
- Per-day photo galleries attached to waypoints
- Background GPS recording (service-worker keepalive)
- Refactor the single-file `index.html` into the modular `css/ js/ data/` layout
  (kept single-file so far to ship without risking the working map)

---

## Tech

Plain HTML + CSS + JS. [Leaflet](https://leafletjs.com/) 1.9.4 from unpkg. No
build step, no framework, no backend. Hosted on GitHub Pages from `main` root.

## Data attribution

Geological data layers — gold occurrences, mineral endowment, goldfield
boundaries, exploration/mining licences, public land and restricted Crown land —
are sourced from the **Geological Survey of Victoria** / **Resources Victoria**
open-data platform (`opendata.maps.vic.gov.au`). Base imagery © Esri (World
Imagery), © OpenTopoMap, © OpenStreetMap contributors.

## License

[MIT](LICENSE) © 2026 Steven McNichol / Banksia Springs Farm.
