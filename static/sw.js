const CACHE_NAME = 'guestbook-v1';
const STATIC_ASSETS = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/@popperjs/core@2.10.2/dist/umd/popper.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.min.js',
    'https://fonts.googleapis.com/css2?family=Vollkorn:wght@700&family=Open+Sans&display=swap',
    '/static/images/logo.png',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Cache-first for CDN and local static assets
    const isStatic = STATIC_ASSETS.includes(event.request.url) ||
                     (url.origin === self.location.origin && url.pathname.startsWith('/static/'));

    if (isStatic) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                if (cached) return cached;
                return fetch(event.request).then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return response;
                });
            })
        );
        return;
    }

    // Network-only for all app routes (/, /admin/*, /api/*, /manifest.webmanifest)
    // No caching of authenticated or dynamic content
});
