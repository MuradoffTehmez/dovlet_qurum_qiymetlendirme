// Service Worker for Q360 PWA
const CACHE_NAME = 'q360-v1.0.0';
const STATIC_CACHE = 'q360-static-v1.0.0';
const DYNAMIC_CACHE = 'q360-dynamic-v1.0.0';

// Static resources to cache
const STATIC_RESOURCES = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/v1/dashboard/stats/',
  '/api/v1/notifications/',
  '/api/v1/users/profile/'
];

// Install event
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => {
        console.log('[SW] Static resources cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Error caching static resources:', error);
      })
  );
});

// Activate event  
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Skip Chrome extensions
  if (requestUrl.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle static resources
  if (isStaticResource(event.request.url)) {
    event.respondWith(cacheFirst(event.request, STATIC_CACHE));
    return;
  }
  
  // Handle API requests
  if (isApiRequest(event.request.url)) {
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
    return;
  }
  
  // Handle page requests
  if (isPageRequest(event.request)) {
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
    return;
  }
  
  // Default: try network first, fallback to cache
  event.respondWith(
    fetch(event.request)
      .catch(() => caches.match(event.request))
  );
});

// Cache strategies
async function cacheFirst(request, cacheName) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    const cache = await caches.open(cacheName);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first strategy failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(cacheName);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for page requests
    if (isPageRequest(request)) {
      return caches.match('/offline/');
    }
    
    return new Response('Offline', { status: 503 });
  }
}

// Helper functions
function isStaticResource(url) {
  return url.includes('/static/') || 
         url.includes('cdn.jsdelivr.net') ||
         url.includes('cdnjs.cloudflare.com');
}

function isApiRequest(url) {
  return url.includes('/api/');
}

function isPageRequest(request) {
  return request.headers.get('Accept').includes('text/html');
}

// Background sync for form submissions
self.addEventListener('sync', event => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync-evaluation') {
    event.waitUntil(syncEvaluationData());
  }
  
  if (event.tag === 'background-sync-feedback') {
    event.waitUntil(syncFeedbackData());
  }
});

async function syncEvaluationData() {
  try {
    // Get pending evaluation data from IndexedDB
    const pendingData = await getPendingEvaluations();
    
    for (const data of pendingData) {
      try {
        const response = await fetch('/api/v1/evaluations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${data.token}`
          },
          body: JSON.stringify(data.evaluation)
        });
        
        if (response.ok) {
          await removePendingEvaluation(data.id);
          console.log('[SW] Evaluation synced successfully');
        }
      } catch (error) {
        console.error('[SW] Error syncing evaluation:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Error in background sync:', error);
  }
}

async function syncFeedbackData() {
  try {
    // Get pending feedback data from IndexedDB
    const pendingData = await getPendingFeedback();
    
    for (const data of pendingData) {
      try {
        const response = await fetch('/api/v1/quick-feedback/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${data.token}`
          },
          body: JSON.stringify(data.feedback)
        });
        
        if (response.ok) {
          await removePendingFeedback(data.id);
          console.log('[SW] Feedback synced successfully');
        }
      } catch (error) {
        console.error('[SW] Error syncing feedback:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Error in background sync:', error);
  }
}

// IndexedDB helper functions (simplified)
async function getPendingEvaluations() {
  // Implementation would use IndexedDB to store/retrieve pending data
  return [];
}

async function removePendingEvaluation(id) {
  // Implementation would remove from IndexedDB
}

async function getPendingFeedback() {
  // Implementation would use IndexedDB to store/retrieve pending data
  return [];
}

async function removePendingFeedback(id) {
  // Implementation would remove from IndexedDB
}

// Push notification handling
self.addEventListener('push', event => {
  console.log('[SW] Push message received');
  
  const options = {
    body: 'Yeni bildirişiniz var',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    tag: 'q360-notification',
    renotify: true,
    requireInteraction: false,
    actions: [
      {
        action: 'view',
        title: 'Görüntülə',
        icon: '/static/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: 'Rədd et',
        icon: '/static/icons/dismiss-icon.png'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.message || options.body;
    options.data = data;
  }
  
  event.waitUntil(
    self.registration.showNotification('Q360 Sistem', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/notifications/')
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.matchAll().then(clientList => {
        if (clientList.length > 0) {
          return clientList[0].focus();
        }
        return clients.openWindow('/');
      })
    );
  }
});

// Skip waiting message
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});