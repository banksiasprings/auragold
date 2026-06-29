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
const SHELL_VERSION = 'v26';
// Build revision — bumped on every deploy so already-installed clients re-fetch the shell.
// v26: on-device ML classifier for detector-audio events. Feature extraction (meyda MFCCs +
// spectral stats) runs in a Blob worker at save time; a tf.js dense classifier trains in-browser
// on labelled clips (4 classes: gold / junk / hot-rock / nothing) and scores every new + historical
// event. New 🏠 Home calibration mode + 🧠 Smart classifier in Settings, GUANO GPS metadata embedded
// in every WAV, and ML-enriched ZIP export (events.csv + features_v1.json + model_v1.json). tf.js
// (~1MB) + meyda (~40KB) precached below for offline training/inference. IndexedDB bumped to v4
// (adds the `auragold_models` store + per-event features / label / source / mlConfidence fields).
const SHELL_REV = 'v26';
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
