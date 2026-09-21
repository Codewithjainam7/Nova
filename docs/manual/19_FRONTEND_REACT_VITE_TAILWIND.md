# Chapter 19: Frontend Architecture with React, Vite & Tailwind

## Overview
The frontend (`frontend/`) is built with React 18, Vite 5, Tailwind CSS, and Framer Motion, delivering a futuristic, glassmorphic sci-fi operating interface.

## Project Structure
- `src/components/Brain/`: Three.js WebGL canvas, 3D Neural Network, and SystemHUD.
- `src/components/Chat/`: Message stream, markdown syntax highlighter, and ChatInput.
- `src/components/HUD/`: Holographic workspace overlay, metrics cards, and telemetry.
- `src/components/DynamicIsland.tsx`: macOS/iOS-inspired compact status indicator.
- `src/store/useNovaStore.ts`: Global Zustand state store managing WebSocket states, telemetry, and messages.

## Build Optimization
Configured with Vite and Rolldown for sub-second Fast Refresh (HMR) and optimized production bundles.
