import { cp, mkdir, rm, stat } from 'node:fs/promises';
import { resolve, join } from 'node:path';

// Copy only public web assets. Never copy secrets, .env, Supabase configuration,
// GitHub workflows, backend, tests or Android source into the packaged frontend.
const root = resolve(import.meta.dirname, '../..');
const out = resolve(import.meta.dirname, '../www');
const assets = [
  'index.html', 'app-config.js', 'halal-shopping-records.js', 'icon.svg',
  'languages.js', 'locale-pack.js', 'manifest.webmanifest',
  'manufacturer-records.js', 'product-data.js', 'store-records.js', 'sw.js'
];
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
for (const file of assets) {
  await stat(join(root, file));
  await cp(join(root, file), join(out, file));
}
console.log('Prepared offline-capable web assets for Capacitor in mobile-wrapper/www');
