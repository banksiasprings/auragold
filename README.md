# 🪙 AuraGold

**An offline-first gold prospecting field map for the central Victorian goldfields.**

AuraGold is a vanilla-JS Progressive Web App you install to your phone's home
screen and run like a native app — no signal required in the field. It bundles a
Leaflet map of 12 candidate prospecting spots, camping waypoints, sub-spots, a
16-day itinerary route line, and seven geological data overlays (gold
occurrences, 1+ Moz endowment zones, goldfield boundaries, active tenements,
bushfire scars, fossicking-permitted State Forest, restricted Crown land). Tap
**Save maps offline** once on wi-fi and the region's base imagery is cached for
use where there's no reception.

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

## Day 1 feature set (shipped)

- Full Leaflet map ported from the field-tested trip map — 12 candidate spots
  with popups, camps, sub-spots, itinerary route line, legend, layer toggles.
- 7 geological overlays: 5 embedded (always offline) + 2 live WMS layers from
  Resources Victoria (cached as viewed).
- Installable PWA: web manifest, gold nugget icon set (48–512 px + maskable +
  Apple touch icon + favicon), standalone display, theme color.
- Service worker with a cache-first strategy: app shell + Leaflet precached on
  install; map tiles and WMS overlays cached at runtime.
- One-tap **Save maps offline** to pre-cache the region's base imagery.

## Day 2+ roadmap

- Live GPS dot + breadcrumb trail (Geolocation API + Leaflet marker)
- Tap-to-drop waypoint with type tag (find / signal / camp / hole)
- Photo capture (`<input type="file" accept="image/*" capture>`)
- Voice memo via the MediaRecorder API
- IndexedDB persistence for waypoints, finds and photos
- "Got a hit" big button — one-tap log of GPS + timestamp + optional 10 s audio
- Itinerary day view — what's planned today, navigate to the next spot
- Trip log export to GPX + KML + JSON
- Settings (units, base-layer preference, theme)
- Background GPS recording (service-worker keepalive)
- Refactor the single-file `index.html` into the modular `css/ js/ data/` layout
  (kept single-file for Day 1 to ship without risking the working 495 KB map)

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
