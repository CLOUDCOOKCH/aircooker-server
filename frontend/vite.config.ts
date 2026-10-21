import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  base: '/app/',
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8080' } },
  build: { target: 'es2023', sourcemap: false },
});
