/**
 * Offline queue for kiosk-guestbook.
 *
 * Intercepts the guestbook form submit via fetch. On network failure,
 * stores the submission in IndexedDB and shows an offline thank-you.
 * Replays queued entries on the `online` event and on each page load.
 *
 * Works on both the form page (/) and the thank-you page (/thank-you).
 * Background Sync is not used — it is unsupported in iOS Safari.
 */

const OQ_DB_NAME  = 'guestbook-offline-queue';
const OQ_STORE    = 'entries';
const OQ_VERSION  = 1;

// ---------------------------------------------------------------------------
// IndexedDB helpers
// ---------------------------------------------------------------------------

function oqOpenDb() {
    return new Promise(function (resolve, reject) {
        var req = indexedDB.open(OQ_DB_NAME, OQ_VERSION);
        req.onupgradeneeded = function (e) {
            e.target.result.createObjectStore(OQ_STORE, { keyPath: 'id', autoIncrement: true });
        };
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror   = function (e) { reject(e.target.error); };
    });
}

function oqEnqueue(fields) {
    return oqOpenDb().then(function (db) {
        return new Promise(function (resolve, reject) {
            var tx    = db.transaction(OQ_STORE, 'readwrite');
            var store = tx.objectStore(OQ_STORE);
            store.add({ fields: fields, queued_at: new Date().toISOString() });
            tx.oncomplete = resolve;
            tx.onerror    = function (e) { reject(e.target.error); };
        });
    });
}

function oqDequeue(id) {
    return oqOpenDb().then(function (db) {
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(OQ_STORE, 'readwrite');
            tx.objectStore(OQ_STORE).delete(id);
            tx.oncomplete = resolve;
            tx.onerror    = function (e) { reject(e.target.error); };
        });
    });
}

function oqGetAll() {
    return oqOpenDb().then(function (db) {
        return new Promise(function (resolve, reject) {
            var tx  = db.transaction(OQ_STORE, 'readonly');
            var req = tx.objectStore(OQ_STORE).getAll();
            req.onsuccess = function (e) { resolve(e.target.result); };
            req.onerror   = function (e) { reject(e.target.error); };
        });
    });
}

// ---------------------------------------------------------------------------
// Collect form fields into a plain object (excludes csrf_token)
// ---------------------------------------------------------------------------

function oqCollectFields(form) {
    var fields = {};
    var fd = new FormData(form);
    fd.forEach(function (value, key) {
        if (key !== 'csrf_token') fields[key] = value;
    });
    // Explicitly record the newsletter checkbox so a missing key means opt-out
    var checkbox = form.querySelector('[name="newsletter_opt_in"]');
    if (checkbox && !checkbox.checked) {
        delete fields['newsletter_opt_in'];
    }
    return fields;
}

// ---------------------------------------------------------------------------
// Queue replay
// ---------------------------------------------------------------------------

var oqReplaying = false;

async function oqReplayQueue() {
    if (oqReplaying) return;
    oqReplaying = true;

    var items;
    try {
        items = await oqGetAll();
    } catch (e) {
        oqReplaying = false;
        return;
    }
    if (!items.length) {
        oqReplaying = false;
        return;
    }

    // Fetch a fresh CSRF token once for the whole batch
    var token;
    try {
        var csrfRes = await fetch('/api/csrf');
        var csrfJson = await csrfRes.json();
        token = csrfJson.csrf_token;
    } catch (e) {
        // Still offline
        oqReplaying = false;
        return;
    }

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        try {
            var fd = new FormData();
            fd.append('csrf_token', token);
            Object.keys(item.fields).forEach(function (k) {
                fd.append(k, item.fields[k]);
            });

            var res = await fetch('/', { method: 'POST', body: fd });

            if (res.ok) {
                await oqDequeue(item.id);
            } else if (res.status === 429) {
                // Rate-limited — leave remaining entries, try again later
                break;
            } else {
                // Server rejected (validation error etc.) — discard to unblock queue
                console.warn('oq: discarding entry', item.id, 'server returned', res.status);
                await oqDequeue(item.id);
            }
        } catch (e) {
            // Network error again — stop, leave entries for next online event
            break;
        }
    }

    oqReplaying = false;

    // Update offline indicator if we're now fully synced
    var remaining;
    try { remaining = await oqGetAll(); } catch (e) { remaining = []; }
    if (!remaining.length) {
        oqSetIndicator(false);
    }
}

// ---------------------------------------------------------------------------
// Offline indicator (form page only)
// ---------------------------------------------------------------------------

function oqSetIndicator(offline) {
    var el = document.getElementById('offline-indicator');
    if (!el) return;
    if (offline) {
        el.classList.remove('d-none');
    } else {
        el.classList.add('d-none');
    }
}

// ---------------------------------------------------------------------------
// Form submit intercept (form page only)
// ---------------------------------------------------------------------------

async function oqHandleSubmit(e) {
    e.preventDefault();
    var form = e.target;
    var fields = oqCollectFields(form);

    try {
        var res = await fetch('/', { method: 'POST', body: new FormData(form) });
        // fetch follows redirects; res.url is the final URL (thank-you page on success)
        window.location.href = res.url;
    } catch (err) {
        // Network failure — queue and show offline thank-you
        try {
            await oqEnqueue(fields);
        } catch (dbErr) {
            console.error('oq: failed to enqueue', dbErr);
        }
        var name = fields['first_name'] || '';
        window.location.href = '/thank-you?name=' + encodeURIComponent(name) + '&offline=1';
    }
}

// ---------------------------------------------------------------------------
// Bootstrap on DOMContentLoaded
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
    // Intercept form submit (form page only)
    var form = document.querySelector('form[action="/"]');
    if (form) {
        form.addEventListener('submit', oqHandleSubmit);
    }

    // Sync indicator with current state
    if (!navigator.onLine) {
        oqSetIndicator(true);
    }

    // Replay queue on reconnect
    window.addEventListener('online', function () {
        oqSetIndicator(false);
        oqReplayQueue();
    });

    window.addEventListener('offline', function () {
        oqSetIndicator(true);
    });

    // Replay any previously queued items on page load
    if (navigator.onLine) {
        oqReplayQueue();
    }
});
