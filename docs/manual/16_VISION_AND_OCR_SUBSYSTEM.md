# Chapter 16: Vision & OCR Subsystem

## Overview
ADA's Vision Subsystem (`backend/vision/`) grants the assistant visual awareness of the user's desktop environment and video input feeds.

## Screen Capture & OCR
- **Real-Time Frame Grabbing**: Captures high-resolution desktop frames.
- **Text & Element Detection**: Uses Gemini Multimodal Vision and OCR to locate buttons, text boxes, and status badges on screen.
- **Visual Grounding**: Maps visual coordinates to UI elements for precise mouse automation on non-standard UIs.

## MediaPipe Hand Gestures
The frontend includes MediaPipe hand tracking (`useHandGestures.ts`) allowing users to rotate, scale, and manipulate the 3D Neural Brain via webcam hand gestures.
