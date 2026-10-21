import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
// The console and bundled PWA styles derive from the same source palette.
await writeFile('dist/theme.css', await readFile('src/tokens.css'));
const files = [];
async function collect(path) {
  for (const item of await readdir('dist/' + path, { withFileTypes: true })) {
    const name = path + item.name;
    if (item.isDirectory()) await collect(name + '/');
    else if (name !== 'sw.js') files.push(name);
  }
}
await collect('');
const digest = createHash('sha256');
for (const name of files.sort()) digest.update(await readFile('dist/' + name));
const version = digest.digest('hex').slice(0, 16);
// Images are public original demo art. Household photos stay in the identity-scoped IDB.
const assets = ['/app/', ...files.map((name) => '/app/' + name)];
await writeFile(
  'dist/sw.js',
  `importScripts('/app/push-handler.js');
const CACHE='aircooker-shell-${version}';
const ASSETS=${JSON.stringify(assets)};
self.addEventListener('install',event=>event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(ASSETS);})()));
self.addEventListener('message',event=>{if(event.data?.type==='ACTIVATE')self.skipWaiting();});
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys())if(key.startsWith('aircooker-shell-')&&key!==CACHE)await caches.delete(key);await self.clients.claim();})()));
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin||!url.pathname.startsWith('/app/'))return;
if(event.request.mode==='navigate'){event.respondWith((async()=>{try{return await fetch(event.request);}catch{return (await caches.open(CACHE)).match('/app/');}})());return;}
if(!ASSETS.includes(url.pathname))return;event.respondWith((async()=>{const cache=await caches.open(CACHE);return (await cache.match(event.request))||fetch(event.request);})());});
`,
);
