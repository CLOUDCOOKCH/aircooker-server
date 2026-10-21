let reloadRequested = false;
export function activateUpdate(worker: ServiceWorker): void {
  reloadRequested = true;
  worker.postMessage({ type: 'ACTIVATE' });
}
/** Public application shell only. API/auth/media requests never enter the worker cache. */
export async function installWorker(): Promise<void> {
  if (!('serviceWorker' in navigator) || !isSecureContext) return;
  try {
    const registration = await navigator.serviceWorker.register('/app/sw.js', {
      scope: '/app/',
      updateViaCache: 'none',
    });
    const announce = () => {
      if (registration.waiting)
        window.dispatchEvent(new CustomEvent('aircooker:update', { detail: registration.waiting }));
    };
    registration.addEventListener('updatefound', () => {
      registration.installing?.addEventListener('statechange', announce);
    });
    // App subscribes after its persistent store opens, so check again on foreground.
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        announce();
        void registration.update();
      }
    });
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing || !reloadRequested) return;
      refreshing = true;
      location.reload();
    });
    setTimeout(announce, 1500);
  } catch {
    /* Installing is optional; local edits still use IndexedDB and an explicit sync queue. */
  }
}
