import React, { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useHandGestures } from '../../hooks/useHandGestures';
import * as THREE from 'three';

export const GestureController: React.FC = () => {
  const gestureStateRef = useHandGestures();
  const { camera } = useThree();
  const targetCameraPos = useRef(new THREE.Vector3(0, 0, 7));

  useFrame(() => {
    const state = gestureStateRef.current;
    if (state.isActive) {
      // Calculate target position based on rotation and zoom
      // Base distance is 7, apply zoom factor (smaller zoom value = closer)
      const distance = 7 * state.zoom;
      
      // Calculate spherical coordinates for Orbit
      // rotX controls longitude (azimuthal angle), rotY controls latitude (polar angle)
      // rotX/Y are -1 to 1. Let's map to roughly -PI/2 to PI/2
      const phi = Math.PI / 2 + state.rotationY * (Math.PI / 3);
      const theta = state.rotationX * (Math.PI / 2);
      
      // Convert spherical to cartesian
      const targetX = distance * Math.sin(phi) * Math.sin(theta);
      const targetY = distance * Math.cos(phi);
      const targetZ = distance * Math.sin(phi) * Math.cos(theta);
      
      targetCameraPos.current.set(targetX, targetY, targetZ);
      
      // Smoothly interpolate current camera position to target
      camera.position.lerp(targetCameraPos.current, 0.1);
      camera.lookAt(0, 0, 0);
    }
  });

  return null;
};
