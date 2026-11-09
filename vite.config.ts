import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    manifest: true,
    modulePreload: false,
    rolldownOptions: {
      input: 'frontend/main.ts',
    },
  },
});
