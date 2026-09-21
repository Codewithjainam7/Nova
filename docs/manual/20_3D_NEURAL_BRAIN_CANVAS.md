# Chapter 20: 3D Neural Brain WebGL Visualization

## Overview
The central visual element of ADA is an interactive 3D Neural Brain (`NeuralNetwork.tsx` & `BrainScene.tsx`) rendered using Three.js and `@react-three/fiber`.

## Mathematical Geometry
- **500 Core Neural Nodes**: Distributed evenly across a spherical brain envelope using spherical Fibonacci distribution.
- **1,200 Dynamic Synaptic Lines**: Computed using distance-thresholded line segments with additive blending.
- **1,000 Floating Outer Particles**: Rotating counter-directionally to create depth perception.

## Reactive Audio Pulse
The 3D canvas samples microphone amplitude in real time, expanding and pulsing the node geometry and altering synaptic colors (Cyan for Listening, Purple for Thinking, Blue for Idle).
