import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const approved = JSON.parse(await readFile('licenses/bundled.json', 'utf8'));
const app = JSON.parse(await readFile('package.json', 'utf8'));
const pending = Object.keys(app.dependencies),
  visited = new Set();
while (pending.length) {
  const name = pending.pop();
  if (visited.has(name)) continue;
  visited.add(name);
  const pkg = JSON.parse(await readFile('node_modules/' + name + '/package.json', 'utf8'));
  if (!approved[name]) throw new Error('Unreviewed browser dependency: ' + name);
  pending.push(
    ...Object.keys(pkg.dependencies ?? {}).filter((value) => !value.startsWith('@types/')),
  );
}
const records = [];
let notices =
  'aircooker browser dependency notices\n\nOriginal application code: Apache-2.0. The following code retains its own licences.\nVite is included for the generated module-preload helper. Type-only packages are not bundled.\n\n';
for (const [name, baseline] of Object.entries(approved)) {
  const directory = 'node_modules/' + name,
    pkg = JSON.parse(await readFile(directory + '/package.json', 'utf8'));
  if (pkg.version !== baseline.version || pkg.license !== baseline.license)
    throw new Error('Review browser licence/version drift: ' + name);
  const files = (await readdir(directory)).filter((file) => /^licen[cs]e/i.test(file));
  if (!files.length) throw new Error('Missing licence: ' + name);
  const attribution = [];
  for (const file of files) {
    const content = await readFile(directory + '/' + file, 'utf8');
    attribution.push({ file, sha256: createHash('sha256').update(content).digest('hex') });
    notices += `${name} ${pkg.version} — ${pkg.license}\n${content}\n\n`;
  }
  records.push({ name, version: pkg.version, license: pkg.license, attribution });
}
await writeFile('dist/THIRD_PARTY_NOTICES.txt', notices);
await writeFile(
  'dist/dependency-licenses.json',
  JSON.stringify({ version: 1, packages: records }, null, 2) + '\n',
);
