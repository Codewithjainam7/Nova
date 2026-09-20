import { useEffect, useRef, useCallback } from 'react';
import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

interface GestureState {
  isActive: boolean;
  rotationX: number; // -1 to 1
  rotationY: number; // -1 to 1
  zoom: number; // relative scale
}

export const useHandGestures = () => {
  const gestureStateRef = useRef<GestureState>({
    isActive: false,
    rotationX: 0,
    rotationY: 0,
    zoom: 1
  });
  
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const landmarkerRef = useRef<HandLandmarker | null>(null);
  const isRunningRef = useRef(false);
  const lastVideoTimeRef = useRef(-1);

  const initVision = useCallback(async () => {
    try {
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
      );
      const landmarker = await HandLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
          delegate: "GPU"
        },
        runningMode: "VIDEO",
        numHands: 1,
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5
      });
      landmarkerRef.current = landmarker;
      
      // Start webcam
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480, facingMode: "user" } 
      });
      
      const video = document.createElement('video');
      video.srcObject = stream;
      video.playsInline = true;
      video.play();
      videoRef.current = video;
      
      video.addEventListener('loadeddata', () => {
        isRunningRef.current = true;
        predict();
      });
      
    } catch (err) {
      console.error("Error initializing hand gestures:", err);
    }
  }, []);

  const predict = useCallback(() => {
    const video = videoRef.current;
    const landmarker = landmarkerRef.current;
    
    if (!video || !landmarker || !isRunningRef.current) return;
    
    if (video.currentTime !== lastVideoTimeRef.current) {
      lastVideoTimeRef.current = video.currentTime;
      const results = landmarker.detectForVideo(video, performance.now());
      
      if (results.landmarks && results.landmarks.length > 0) {
        const hand = results.landmarks[0];
        
        // Index Finger Tip is 8, Thumb Tip is 4, Wrist is 0
        const indexTip = hand[8];
        const thumbTip = hand[4];
        const wrist = hand[0];
        
        // Calculate X/Y rotation based on hand position relative to center of screen (0.5, 0.5)
        // Mediapipe coordinates are 0-1 (top-left to bottom-right)
        const rotX = (wrist.x - 0.5) * 2; // -1 to 1
        const rotY = (wrist.y - 0.5) * 2; // -1 to 1
        
        // Calculate pinch distance (3D Euclidean distance)
        const dx = indexTip.x - thumbTip.x;
        const dy = indexTip.y - thumbTip.y;
        const dz = indexTip.z - thumbTip.z;
        const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
        
        // Map distance (roughly 0.02 to 0.2) to zoom level
        // Pinching (small distance) -> Zoom out
        // Spreading (large distance) -> Zoom in
        const rawZoom = Math.min(Math.max(distance * 5, 0.2), 2.0);
        
        gestureStateRef.current = {
          isActive: true,
          rotationX: -rotX, // Flip for mirroring
          rotationY: -rotY,
          zoom: rawZoom
        };
      } else {
        gestureStateRef.current.isActive = false;
      }
    }
    
    if (isRunningRef.current) {
      requestAnimationFrame(predict);
    }
  }, []);

  useEffect(() => {
    initVision();
    return () => {
      isRunningRef.current = false;
      if (videoRef.current && videoRef.current.srcObject) {
        (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
      }
      if (landmarkerRef.current) {
        landmarkerRef.current.close();
      }
    };
  }, [initVision]);

  return gestureStateRef;
};
