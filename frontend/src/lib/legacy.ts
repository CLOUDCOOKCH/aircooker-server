/** Read compatibility for durable state made by already installed previews. */
export const legacy = {
  prefix: 'aircooker',
  kitchen: 'aircooker:last-kitchen',
  csrf: 'aircooker_pwa_csrf',
  refreshLock: 'aircooker-auth-refresh',
};

export async function databaseExists(name: string): Promise<boolean> {
  if (typeof indexedDB.databases === 'function')
    return (await indexedDB.databases()).some((database) => database.name === name);
  // Probe without creating a database on browsers lacking enumeration.
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name);
    let created = false;
    request.onupgradeneeded = () => {
      created = true;
      request.transaction!.abort();
    };
    request.onsuccess = () => {
      request.result.close();
      resolve(true);
    };
    request.onerror = () => {
      if (created) resolve(false);
      else reject(request.error);
    };
  });
}
