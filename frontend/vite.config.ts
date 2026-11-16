import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    dedupe: ['react', 'react-dom'],
  },
  server: {
    port: 5173,
    strictPort: true,
    host: '0.0.0.0',
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-dev-runtime',
      'react-dom/client',
      'three',
      '@react-three/fiber',
      '@react-three/drei',
      'framer-motion',
      'lucide-react',
      'clsx',
      'zustand',
      'react-markdown',
      'react-router-dom',
      'tailwind-merge',
    ],
  },
});
