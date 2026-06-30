# 🪙 AuraGold

**An offline-first gold prospecting field map for the central Victorian goldfields.**

AuraGold is a vanilla-JS Progressive Web App you install to your phone's home
screen and run like a native app — no signal required in the field. It bundles a
Leaflet map of 12 candidate prospecting spots, camping waypoints, sub-spots, an
editable **trip planner**, and geological data overlays (gold
occurrences, 1+ Moz endowment zones, goldfield boundaries, active tenements,
bushfire scars, fossicking-permitted State Forest, restricted Crown land, and a
**⚡ powerline EMI overlay**). Tap
**Save maps offline** once on wi-fi and the region's base imagery is cached for
use where there's no reception.

It also forecasts **when** to detect. The **🌙 Detection Window** scores every
hour of the next 24 h for detector efficiency — combining solar/geomagnetic and
grid EMI, atmosphere, ground coupling, moonlight and powerline proximity — and
highlights the best and worst 3-hour windows (yes, that can mean a night shift).
Astronomy is computed on-device so it works with no signal; live space-weather,
weather and grid-demand inputs are cached for offline use. Scores are honest
heuristic estimates, with tunable weights in Settings.

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

## Recording detector audio (v24)

AuraGold can record your **detector's audio** while you swing and GPS-tag every
hit — building a dataset of *“what the ground sounded like where the gold was.”*
Everything runs **on the phone, fully offline**, and stays on the phone.

### Hardware — getting detector audio into the phone

The phone hears the detector as a microphone. The wiring (Path A):

```
 Detector 3.5 mm headphone out
        │
        ▼
 3.5 mm Y-splitter ──► your headphones (you still hear the detector)
        │
        └──► 3.5 mm → TRRS adapter ──► USB-C audio adapter ──► phone USB-C port
```

- The **Y-splitter** lets you keep listening on headphones while the phone also
  receives the signal.
- The **TRRS adapter** presents the detector's output on the mic ring so the
  USB-C audio adapter treats it as a microphone input.
- In **Settings → 🎵 Audio capture → Audio input device**, select that **USB-C
  audio adapter** — *not* the built-in phone mic.

> ⚠️ **Test the chain before you rely on it.** Many phones don't pass USB-C
> line-in audio cleanly. After plugging in, open **Settings → 🎵 Audio capture →
> Test capture**, swing over a known target, and confirm you hear the detector in
> the 5-second playback (the readout also shows a peak %). If the peak is near
> zero, your phone/adapter isn't receiving line-in — fall back to a Bluetooth
> lavalier mic clipped near the detector's speaker.

### Field workflow

1. Plug in the adapter chain and pick the device in Settings (once).
2. Tap the **● REC** chip (top-left) — or just tap **🎯 Got a hit!** — to grant
   the mic and start capture. A pulsing red **REC** chip shows while recording.
3. Swing. When you get a signal, tap **🎯 Got a hit!** — the **last 10 seconds**
   of audio is saved with your GPS position as a 🎵 marker.
4. *(Optional)* set an **auto-flag threshold** so loud responses are captured
   automatically. Watch the live level meter to pick a sensible level; start
   around **0.3** and adjust.
5. Dig. Back at the marker (tap it, or **Menu → 🎵 Audio events**), play the clip
   and mark **🏆 Confirm gold** or **✗ False alarm**, and add notes.
6. Export everything from **🎵 Audio events → Export ZIP** — `.wav` clips plus a
   GPS-stamped CSV — for training a signal classifier later.

### Things to know

- **Foreground only.** A phone can't keep the microphone open in the background,
  so capture pauses if you switch apps or lock the screen. Keep AuraGold on screen
  while prospecting.
- **Battery.** Continuous audio + GPS draws noticeably more power — carry a power
  bank for a full day.
- **Storage.** Each clip is lossless ~320 KB (10 s @ 16 kHz). A 200-hit day is
  ~64 MB. The **storage readout**, a **3-second auto-flag debounce**, and a
  **500-events-per-day cap** keep it in check; **Clear all audio events** wipes it.
- **Why WAV, not Opus.** Lossless 16 kHz preserves the 200–1500 Hz tonal detail
  that distinguishes target responses — the exact signal a classifier needs.
- **iOS.** PWA microphone access on iOS Safari is unreliable; this feature is
  built and tested for **Android Chrome**. On iPhone, run it in a Chrome/Safari
  tab rather than the installed app if the mic prompt doesn't appear.

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

**Phase 4 — detector audio capture (this round, v24)**

- Continuous foreground microphone capture into a rolling **30-second PCM ring
  buffer** (Web Audio API). Tonal-preserving constraints (no echo-cancel, no
  noise-suppression, no auto-gain, 16 kHz mono).
- **🎯 Got a hit!** and an optional **auto-flag** (smoothed-RMS threshold, 3 s
  debounce) each snapshot the **last 10 seconds** as a lossless **16 kHz mono
  WAV** + the interpolated GPS fix, saved to IndexedDB (`auragold_audio_events`,
  DB bumped to **v3**).
- Saved hits render as **🎵 markers** (🏆 once you confirm gold) in their own map
  pane and a **"🎵 My signal hits"** layer in the unified Layers panel. Tap a
  marker to play the clip back, add notes, and mark **Confirm gold / False alarm**.
- New **☰ Menu → 🎵 Audio events** panel: filterable list (manual / auto / gold /
  unmarked), inline playback, and **Export ZIP** (every clip as `.wav` + a
  GPS-stamped `audio_events.csv`) for later ML training.
- **Settings → 🎵 Audio capture:** pick the USB-C audio adapter, set the auto-flag
  threshold against a **live level meter**, run a **Test capture** (5 s record +
  playback to verify the detector→phone chain), and see event count / storage used.

See **[Recording detector audio](#recording-detector-audio-v24)** below for the
hardware wiring and field workflow.

## Roadmap

- Per-day photo galleries attached to waypoints
- Background GPS recording (service-worker keepalive)
- On-device signal classifier trained on the exported audio + GPS dataset
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
