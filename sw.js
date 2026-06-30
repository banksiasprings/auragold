/* AuraGold service worker — offline-first field map.
 *
 * Strategy:
 *   - App shell (same-origin HTML/manifest/icons + Leaflet from CDN) is
 *     precached on install so the app boots with no network.
 *   - Map tiles + WMS overlays + any cross-origin asset are cache-first at
 *     runtime: served from cache when present, otherwise fetched and stored.
 *     This means anything you view online — or pre-fetch via "Save maps
 *     offline" in the app — is available in the field with no signal.
 *
 * Bump SHELL_VERSION on every deploy so returning clients re-fetch the app
 * shell. TILE_CACHE is deliberately NOT versioned with it — the user's saved
 * offline maps survive app updates (only bump it if the tile strategy changes).
 */
// Keep this in lockstep with APP_VERSION in index.html (the on-screen version badge).
const SHELL_VERSION = 'v32';
// Build revision — bumped on every deploy so already-installed clients re-fetch the shell.
// v30: audio recording UX overhaul. Capture no longer auto-starts on app open (opt-in toggle,
// default OFF); the mic is fully released when the app is backgrounded so other apps (e.g. Dispatch)
// can use it; the REC button moved to the bottom-right and is now an always-visible OFF/ON toggle
// with a live MM:SS timer + green/orange/red level tint; added a ☰-menu REC toggle, a Settings
// "Capture controls" group (auto-start / auto-resume / button position / volume-key toggle), and
// honest, explicit toast copy. "Got a hit" with REC off no longer silently grabs the mic.
// v29.1: pre-detection EMI/setup checklist (Minelab GPX-class accuracy killers) with best-effort
// auto-checks (detection score, battery, powerline proximity, ambient mic), long-press dismiss,
// and a geofence auto-trigger near trip spots. Plus a "Start detecting" button + detecting footer.
// v29: Detection Window forecaster + Powerline EMI overlay. Powerline GeoJSON (8,367 Vic lines,
// 2.56 MB / ~0.37 MB gzip) precached below so the overlay AND the forecaster's nearest-powerline
// EMI term work offline. Live forecast inputs — NOAA Kp, Open-Meteo weather, AEMO VIC demand — are
// served NETWORK-FIRST (fresh when online) with cache fallback (last fetch survives offline 6–12 h).
// v28.0.1: EL/ML tenement popups now use correct, lease-type-specific fossicking guidance.
// Active ELs no longer falsely say "NO PROSPECTING" — a Miner's Right still covers Crown/SF
// fossicking within an EL (the holder's exclusivity is for drilling/major workings, not detector
// work). MLs keep the restricted framing. Legend labels corrected to match. (Rides on in-progress
// v27 work — find outcomes, delete-confirm modal, multi-photo — that was already in the tree.)
// v26: on-device ML classifier for detector-audio events. Feature extraction (meyda MFCCs +
// spectral stats) runs in a Blob worker at save time; a tf.js dense classifier trains in-browser
// on labelled clips (4 classes: gold / junk / hot-rock / nothing) and scores every new + historical
// event. New 🏠 Home calibration mode + 🧠 Smart classifier in Settings, GUANO GPS metadata embedded
// in every WAV, and ML-enriched ZIP export (events.csv + features_v1.json + model_v1.json). tf.js
// (~1MB) + meyda (~40KB) precached below for offline training/inference. IndexedDB bumped to v4
// (adds the `auragold_models` store + per-event features / label / source / mlConfidence fields).
// v32: 🎯 Nugget Potential Index (NPI) heatmap + dual-detector tagging + per-(detector,coil)
// classifier. The NPI heatmap tiles (palettised PNG, z10-12, ~9.5 MB) + the packed component
// grid (npi-grid.png) + metadata are precached below — the grid/meta via SHELL_ASSETS and the
// tile pyramid from data/npi/tiles-manifest.json — so the heatmap and tap-to-explain work
// offline in the field. Audio events now carry a detector + coil tag (Gold Monster 1000 / GPX
// 6000 + coil); a separate classifier model is trained per combo.
const SHELL_REV = 'v32';
const SHELL_CACHE = 'auragold-shell-' + SHELL_REV;
const TILE_CACHE = 'auragold-tiles-v1';

// Relative paths so it works under the /auragold/ GitHub Pages subpath.
const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './data/permitted_land.json',
  // v25: camping overlays — small region-clipped GeoJSON (~0.6MB total), precached so the
  // Camping layers work offline immediately. (Forest-track GeoJSON stays runtime-cached only —
  // it's ~6.8MB and grabbed on demand / via "Save maps offline".)
  './data/camping_free.geojson',
  './data/camping_caravan_parks.geojson',
  './data/camping_paid.geojson',
  './data/rest_areas_vic.geojson',
  './data/parks_vic_campsites.geojson',
  // v29: Victoria powerline EMI overlay — 8,367 lines, 2.56 MB but ~0.37 MB gzipped. Precached so
  // both the ⚡ Powerlines layer and the Detection Window's nearest-powerline term work offline.
  './data/powerlines_vic.geojson',
  // v31: smoke-test clip pack (48 synthetic GUANO-tagged WAVs, ~14.7 MB store-only ZIP).
  // Precached so the ML-pipeline wiring-check ("📦 Load smoke-test clips") works offline.
  './data/smoke-test-clips-v31.zip',
  // v32: NPI tap-to-explain data — the packed component grid + metadata (small). The heatmap
  // TILE pyramid is precached separately from data/npi/tiles-manifest.json (see install below).
  './data/npi/npi-grid.png',
  './data/npi/npi-meta.json',
  './data/npi/tiles-manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.ico',
  // Gold-nugget mineral-occurrence marker (client-side vector layer, v22).
  './icons/nugget-marker.png',
  './icons/nugget-marker@2x.png',
  // Leaflet from CDN — cross-origin but CORS-enabled, so cacheable.
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  // Leaflet.markercluster — clusters the gold-nugget mineral layer; precached for offline.
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js',
  // SortableJS — drag-reorder for the trip planner; precached so reordering works offline.
  'https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js',
  // v26: TensorFlow.js (~1MB) + Meyda (~40KB) — on-device audio classifier. Precached so feature
  // extraction, training, and inference all work in the field with no signal.
  'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.17.0/dist/tf.min.js',
  'https://cdn.jsdelivr.net/npm/meyda@5.6.0/dist/web/meyda.min.js',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/layers.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/layers-2x.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    // Add each asset individually so one flaky CDN response can't fail install.
    await Promise.all(SHELL_ASSETS.map(async (url) => {
      try {
        await cache.add(new Request(url, { cache: 'reload' }));
      } catch (err) {
        // Best-effort: a missing asset will be retried at runtime via fetch.
        console.warn('[sw] precache miss:', url, err);
      }
    }));
    // v32: precache the NPI heatmap tile pyramid from its manifest (~9.5 MB, ~845 tiles) so the
    // 🎯 Nugget Potential layer works offline. Best-effort + chunked so it can't fail install;
    // any miss is filled at runtime by the same-origin cache-first handler when the tile is viewed.
    try {
      const mani = await fetch('./data/npi/tiles-manifest.json', { cache: 'reload' });
      if (mani && mani.ok) {
        const tiles = await mani.json();
        for (let i = 0; i < tiles.length; i += 24) {
          await Promise.all(tiles.slice(i, i + 24).map(async (u) => {
            try { await cache.add(new Request(u, { cache: 'reload' })); } catch (e) {}
          }));
        }
      }
    } catch (e) { console.warn('[sw] NPI tile precache skipped:', e); }
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      // Purge only stale SHELL caches; keep TILE_CACHE (the saved offline maps).
      keys.filter((k) => k.startsWith('auragold-shell-') && k !== SHELL_CACHE)
          .map((k) => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;

  // v29: live forecast inputs — fresh when online, last-good when offline (network-first).
  const LIVE_API_HOSTS = ['services.swpc.noaa.gov', 'api.open-meteo.com', 'visualisations.aemo.com.au'];
  if (!sameOrigin && LIVE_API_HOSTS.indexOf(url.hostname) !== -1) {
    event.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res && res.ok) { const cache = await caches.open(TILE_CACHE); cache.put(req, res.clone()); }
        return res;
      } catch (err) {
        const cached = await caches.match(req);
        if (cached) return cached;
        return Response.error();
      }
    })());
    return;
  }

  if (sameOrigin) {
    // App shell: cache-first, network fallback, index.html fallback for navigations.
    event.respondWith((async () => {
      const cached = await caches.match(req);
      if (cached) return cached;
      try {
        const res = await fetch(req);
        if (res && res.ok) {
          const cache = await caches.open(SHELL_CACHE);
          cache.put(req, res.clone());
        }
        return res;
      } catch (err) {
        if (req.mode === 'navigate') {
          const fallback = await caches.match('./index.html');
          if (fallback) return fallback;
        }
        throw err;
      }
    })());
    return;
  }

  // Cross-origin: map tiles, WMS overlays, Leaflet CDN — cache-first.
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;
    try {
      const res = await fetch(req);
      // Cache successful and opaque (no-cors) tile responses alike.
      if (res && (res.ok || res.type === 'opaque')) {
        const cache = await caches.open(TILE_CACHE);
        cache.put(req, res.clone());
      }
      return res;
    } catch (err) {
      // Offline and not cached — let the map show its empty tile.
      return Response.error();
    }
  })());
});

// Let the page report how many tiles are cached (used by the offline UI/tests).
self.addEventListener('message', (event) => {
  if (event.data === 'TILE_COUNT') {
    event.waitUntil((async () => {
      let count = 0;
      try {
        const cache = await caches.open(TILE_CACHE);
        count = (await cache.keys()).length;
      } catch (e) {}
      const clients = await self.clients.matchAll();
      clients.forEach((c) => c.postMessage({ type: 'TILE_COUNT', count }));
    })());
  }
});
