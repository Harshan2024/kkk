/**
 * sw.js — CarbonTracker AI Service Worker
 * =========================================
 * Phase 15: Progressive Web App (PWA)
 *
 * Implements:
 * - Cache-first strategy for static assets (CSS, JS, fonts)
 * - Network-first strategy for API calls
 * - Offline fallback page for navigation requests
 * - Background sync stub for activity logging when offline
 */

const CACHE_VERSION = 'v1.1.0';
const STATIC_CACHE  = `carbontracker-static-${CACHE_VERSION}`;
const API_CACHE     = `carbontracker-api-${CACHE_VERSION}`;

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
];

// API routes to cache with network-first strategy
const API_ROUTES = [
  '/api/system/status',
  '/api/v1/feature-flags',
];

// ─── Install Event ────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  console.log(`[SW] Installing ${CACHE_VERSION}`);

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        return cache.addAll(PRECACHE_ASSETS).catch((err) => {
          console.warn('[SW] Pre-cache failed for some assets:', err);
        });
      })
      .then(() => self.skipWaiting())
  );
});


// ─── Activate Event ───────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  console.log(`[SW] Activating ${CACHE_VERSION}`);

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith('carbontracker-') && name !== STATIC_CACHE && name !== API_CACHE)
          .map((name) => {
            console.log(`[SW] Deleting old cache: ${name}`);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});


// ─── Fetch Event ─────────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip browser extension requests
  if (!url.protocol.startsWith('http')) return;

  // ── API Routes: Network-first with cache fallback ─────────────────────────
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request, API_CACHE, 5000));
    return;
  }

  // ── Next.js Static Assets: Cache-first ───────────────────────────────────
  if (
    url.pathname.startsWith('/_next/static/') ||
    url.pathname.startsWith('/icons/') ||
    url.pathname.match(/\.(css|js|woff2?|png|jpg|jpeg|svg|ico)$/)
  ) {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
    return;
  }

  // ── Navigation Requests (HTML): Network-first with offline fallback ───────
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match('/offline.html').then(r => r || new Response('Offline', { status: 503 })))
    );
    return;
  }

  // ── Default: Network only ─────────────────────────────────────────────────
  event.respondWith(fetch(request));
});


// ─── Cache Strategies ─────────────────────────────────────────────────────────

/**
 * Cache-first: Return from cache if available, otherwise fetch and cache.
 */
async function cacheFirstStrategy(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('Asset unavailable offline', { status: 503 });
  }
}

/**
 * Network-first: Try network, fall back to cache within timeout.
 */
async function networkFirstStrategy(request, cacheName, timeoutMs = 4000) {
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('timeout')), timeoutMs)
  );

  try {
    const response = await Promise.race([fetch(request), timeoutPromise]);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ success: false, error: 'Offline', message: 'No network and no cached response available.' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}


// ─── Background Sync (stub) ───────────────────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-activities') {
    event.waitUntil(syncOfflineActivities());
  }
});

async function syncOfflineActivities() {
  /**
   * Background sync stub.
   * When implemented, this reads queued activities from IndexedDB
   * and POSTs them to /api/v1/activities once network is restored.
   */
  console.log('[SW] Background sync triggered: sync-offline-activities');
  // TODO: Read from IndexedDB queue and POST to backend
}


// ─── Push Notifications (stub) ────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body || 'CarbonTracker update',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    data: { url: data.url || '/' },
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'CarbonTracker AI', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.openWindow(url));
});
