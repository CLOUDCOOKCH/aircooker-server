/* Notifications always show visible, generic content. No API/session/media access here. */
function reminderURL(raw) {
  try {
    const url = new URL(raw, self.location.origin);
    if (url.origin === self.location.origin && url.pathname === '/app/') {
      const tab = url.searchParams.get('tab');
      const day = url.searchParams.get('day');
      if (tab === 'settings') return self.location.origin + '/app/?tab=settings';
      if (tab === 'calendar' && /^\d{4}-\d{2}-\d{2}$/.test(day || ''))
        return self.location.origin + '/app/?tab=calendar&day=' + day;
    }
  } catch {
    /* Fall back to the application, never an external destination. */
  }
  return self.location.origin + '/app/';
}
self.addEventListener('push', (event) => {
  event.waitUntil(
    (async () => {
      let value = {};
      try {
        value = event.data?.json() || {};
      } catch {
        /* Visible fallback required by Web Push. */
      }
      const body = typeof value.body === 'string' ? value.body.slice(0, 240) : 'mealf';
      await self.registration.showNotification('mealf', {
        body,
        icon: '/app/icon-192.png',
        tag:
          typeof value.tag === 'string' && /^[A-Za-z0-9:.\-]{1,180}$/.test(value.tag)
            ? value.tag
            : 'mealf-reminder',
        renotify: false,
        data: { url: reminderURL(value.url) },
      });
    })(),
  );
});
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = reminderURL(event.notification.data?.url);
  event.waitUntil(
    (async () => {
      const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      const open = windows.find((client) => new URL(client.url).pathname.startsWith('/app/'));
      if (open) {
        await open.focus();
        // The application protects an active recipe editor before acting on this message.
        open.postMessage({ type: 'MEAL_REMINDER', url });
      } else {
        await self.clients.openWindow(url);
      }
    })(),
  );
});
