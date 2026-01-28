import { defineConfig } from 'vite';

export default defineConfig({
  base: '/salish-sea-dreaming/',
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    assetsInlineLimit: 0
  },
  server: {
    host: true,
    port: 3000
  }
});
