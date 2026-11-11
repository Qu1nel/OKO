import { defineConfig } from 'vite';

export default defineConfig({
  // Keep CSS asset URLs relative to the built files served by Django
  base: './',
  build: {
    manifest: true,
    modulePreload: false,
    rolldownOptions: {
      input: 'frontend/main.ts',
    },
  },
});
