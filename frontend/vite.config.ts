import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  base: '/app/',
  plugins: [react()],
  server: {
    fs: {
      allow: [
        fileURLToPath(new URL('.', import.meta.url)),
        fileURLToPath(new URL('../src/mealf/food_catalog.json', import.meta.url)),
      ],
    },
    proxy: { '/api': 'http://127.0.0.1:8080' },
  },
  build: { target: 'es2023', sourcemap: false },
});
