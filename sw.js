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
const SHELL_VERSION = 'v17';
const SHELL_CACHE = 'auragold-shell-' + SHELL_VERSION;
const TILE_CACHE = 'auragold-tiles-v1';

// Relative paths so it works under the /auragold/ GitHub Pages subpath.
const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './data/permitted_land.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.ico',
  // Leaflet from CDN — cross-origin but CORS-enabled, so cacheable.
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
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
