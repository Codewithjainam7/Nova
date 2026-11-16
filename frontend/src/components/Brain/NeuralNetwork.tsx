import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface NeuralNetworkProps {
  isListening: boolean;
  isProcessing: boolean;
  amplitude: number;
}

export const NeuralNetwork: React.FC<NeuralNetworkProps> = ({ isListening, isProcessing, amplitude }) => {
  const nodesRef = useRef<THREE.Points>(null!);
  const microNodesRef = useRef<THREE.Points>(null!);
  const linesRef = useRef<THREE.LineSegments>(null!);
  const outerCloudRef = useRef<THREE.Points>(null!);
  const pulsesRef = useRef<THREE.Points>(null!);
  const gyroRing1Ref = useRef<THREE.Mesh>(null!);
  const gyroRing2Ref = useRef<THREE.Mesh>(null!);
  const gyroRing3Ref = useRef<THREE.Mesh>(null!);
  const gyroRing4Ref = useRef<THREE.Mesh>(null!);
  const brainGroupRef = useRef<THREE.Group>(null!);

  // Generate Advanced Multi-Layered Cybernetic Dual-Hemisphere Brain
  const { 
    nodePositions, 
    microNodePositions,
    linePositions, 
    outerPositions, 
    pulsePaths, 
    initialPulsePositions
  } = useMemo(() => {
    const nodeCount = 1100;
    const microCount = 650;
    const outerCount = 1800;

    const positions = new Float32Array(nodeCount * 3);
    const microPositions = new Float32Array(microCount * 3);
    const outerPositions = new Float32Array(outerCount * 3);

    // 1. Generate Anatomical Cortex Nodes with Deep Folding & True Fissure
    for (let i = 0; i < nodeCount; i++) {
      const isLeft = i % 2 === 0;
      const hemisphereSign = isLeft ? -1 : 1;
      
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);

      // Multi-frequency cerebral gyri and sulci ridges (rich brain folding)
      const gyriRipple = 
        Math.sin(theta * 7.0) * Math.cos(phi * 8.0) * 0.15 + 
        Math.sin(theta * 14.0) * Math.cos(phi * 4.0) * 0.06 +
        Math.sin(phi * 12.0) * 0.04;

      const r = 1.88 + gyriRipple + (Math.random() - 0.5) * 0.18;
      const xCenter = hemisphereSign * 0.46;

      let x = xCenter + (r * 0.74 * Math.sin(phi) * Math.cos(theta) * (isLeft ? -1 : 1));
      
      // Preserve sharp longitudinal cerebral fissure
      if (isLeft && x > -0.07) x = -0.07 - Math.random() * 0.08;
      if (!isLeft && x < 0.07) x = 0.07 + Math.random() * 0.08;

      let y = r * 0.84 * Math.sin(phi) * Math.sin(theta);
      let z = r * 1.18 * Math.cos(phi);

      // Cerebellum & Brainstem cluster at base
      if (i > nodeCount - 140) {
        x = (Math.random() - 0.5) * 0.85;
        y = -1.15 - Math.random() * 0.8;
        z = -0.45 - Math.random() * 0.65;
      }

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
    }

    // 2. Micro-Interneurons (deep synaptic density layer)
    for (let i = 0; i < microCount; i++) {
      const parentIdx = Math.floor(Math.random() * nodeCount);
      const px = positions[parentIdx * 3];
      const py = positions[parentIdx * 3 + 1];
      const pz = positions[parentIdx * 3 + 2];

      microPositions[i * 3] = px + (Math.random() - 0.5) * 0.22;
      microPositions[i * 3 + 1] = py + (Math.random() - 0.5) * 0.22;
      microPositions[i * 3 + 2] = pz + (Math.random() - 0.5) * 0.22;
    }

    // 3. Generate Outer Quantum Particle Cloud
    for (let i = 0; i < outerCount; i++) {
      const phi = Math.acos(2.0 * Math.random() - 1.0);
      const theta = 2.0 * Math.PI * Math.random();
      const r = 2.3 + Math.random() * 1.8;

      outerPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta) * 0.88;
      outerPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.78;
      outerPositions[i * 3 + 2] = r * Math.cos(phi) * 1.10;
    }

    // 4. Dense Axon Synaptic Web & Action Potential Paths
    const maxConnections = 2600;
    const linePositions = new Float32Array(maxConnections * 6);
    const pulsePaths: { from: [number, number, number]; to: [number, number, number]; speed: number; offset: number }[] = [];
    let lineIdx = 0;

    for (let i = 0; i < nodeCount; i += 2) {
      const p1: [number, number, number] = [positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]];

      for (let j = i + 1; j < nodeCount; j += 2) {
        const p2: [number, number, number] = [positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]];
        const dx = p1[0] - p2[0];
        const dy = p1[1] - p2[1];
        const dz = p1[2] - p2[2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        const sameHemisphere = (p1[0] > 0 && p2[0] > 0) || (p1[0] < 0 && p2[0] < 0);
        const isCorpusCallosum = !sameHemisphere && Math.abs(p1[0]) < 0.45 && Math.abs(p2[0]) < 0.45 && dist < 0.90;

        if (((sameHemisphere && dist < 0.52) || isCorpusCallosum) && lineIdx < maxConnections) {
          linePositions[lineIdx * 6] = p1[0];
          linePositions[lineIdx * 6 + 1] = p1[1];
          linePositions[lineIdx * 6 + 2] = p1[2];
          linePositions[lineIdx * 6 + 3] = p2[0];
          linePositions[lineIdx * 6 + 4] = p2[1];
          linePositions[lineIdx * 6 + 5] = p2[2];

          if (pulsePaths.length < 75 && Math.random() < 0.18) {
            pulsePaths.push({
              from: p1,
              to: p2,
              speed: 0.9 + Math.random() * 1.5,
              offset: Math.random() * Math.PI * 2
            });
          }

          lineIdx++;
        }
      }
    }

    const initialPulsePositions = new Float32Array(pulsePaths.length * 3);
    pulsePaths.forEach((path, idx) => {
      initialPulsePositions[idx * 3] = path.from[0];
      initialPulsePositions[idx * 3 + 1] = path.from[1];
      initialPulsePositions[idx * 3 + 2] = path.from[2];
    });

    return {
      nodePositions: positions,
      microNodePositions: microPositions,
      linePositions: linePositions.slice(0, lineIdx * 6),
      outerPositions,
      pulsePaths,
      initialPulsePositions
    };
  }, []);

  // Frame Animation: Rotation, Synaptic Wave Resonance & Gyro Rings
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    const basePulse = 1.0 + amplitude * 0.45;
    const respiration = Math.sin(t * 1.5) * 0.035;
    const scale = basePulse + respiration;

    // 1. Rotate whole Brain Group smoothly
    if (brainGroupRef.current) {
      brainGroupRef.current.rotation.y = t * 0.09;
      brainGroupRef.current.rotation.x = Math.sin(t * 0.06) * 0.08;
      brainGroupRef.current.scale.set(scale, scale, scale);
    }

    // 2. Animate Traveling Action Potential Impulses along Axons
    if (pulsesRef.current && pulsePaths.length > 0) {
      const posAttr = pulsesRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const array = posAttr.array as Float32Array;
      const speedMultiplier = isListening ? 2.6 : isProcessing ? 3.8 : 1.3;

      for (let i = 0; i < pulsePaths.length; i++) {
        const p = pulsePaths[i];
        const progress = (Math.sin(t * p.speed * speedMultiplier + p.offset) + 1.0) / 2.0;

        array[i * 3] = p.from[0] + (p.to[0] - p.from[0]) * progress;
        array[i * 3 + 1] = p.from[1] + (p.to[1] - p.from[1]) * progress;
        array[i * 3 + 2] = p.from[2] + (p.to[2] - p.from[2]) * progress;
      }
      posAttr.needsUpdate = true;
    }

    // 3. Rotate Micro-Interneurons with slight offset
    if (microNodesRef.current) {
      microNodesRef.current.rotation.y = t * 0.02;
    }

    // 4. Rotate Outer Synaptic Cloud
    if (outerCloudRef.current) {
      outerCloudRef.current.rotation.y = -t * 0.04;
      outerCloudRef.current.rotation.z = Math.cos(t * 0.03) * 0.06;
    }

    // 5. Counter-rotating Quad Quantum Gyro Rings
    if (gyroRing1Ref.current) {
      gyroRing1Ref.current.rotation.z = t * 0.22;
      gyroRing1Ref.current.rotation.x = Math.sin(t * 0.15) * 0.28;
    }
    if (gyroRing2Ref.current) {
      gyroRing2Ref.current.rotation.y = -t * 0.28;
      gyroRing2Ref.current.rotation.z = Math.cos(t * 0.2) * 0.24;
    }
    if (gyroRing3Ref.current) {
      gyroRing3Ref.current.rotation.x = t * 0.18;
      gyroRing3Ref.current.rotation.y = Math.sin(t * 0.1) * 0.35;
    }
    if (gyroRing4Ref.current) {
      gyroRing4Ref.current.rotation.z = -t * 0.32;
      gyroRing4Ref.current.rotation.x = Math.cos(t * 0.18) * 0.3;
    }
  });

  // Dynamic Color Palette
  const nodeColor = isListening ? '#22d3ee' : isProcessing ? '#c084fc' : '#38bdf8';
  const microColor = isListening ? '#67e8f9' : isProcessing ? '#e879f9' : '#7dd3fc';
  const lineColor = isListening ? '#06b6d4' : isProcessing ? '#a855f7' : '#0284c7';
  const pulseColor = isListening ? '#ffffff' : isProcessing ? '#f472b6' : '#67e8f9';
  const haloColor = isListening ? '#0891b2' : isProcessing ? '#7e22ce' : '#1e3a8a';

  return (
    <group>
      {/* 3D Brain Core Group (Clean, zero hovering text, 100% complex neural architecture) */}
      <group ref={brainGroupRef}>
        
        {/* Layer 1: Primary Anatomical Cortex Nodes */}
        <points ref={nodesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[nodePositions, 3]}
            />
          </bufferGeometry>
          <pointsMaterial
            color={nodeColor}
            size={0.040}
            sizeAttenuation
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

        {/* Layer 2: Micro-Interneurons (Density Layer) */}
        <points ref={microNodesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[microNodePositions, 3]}
            />
          </bufferGeometry>
          <pointsMaterial
            color={microColor}
            size={0.022}
            sizeAttenuation
            transparent
            opacity={0.80}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

        {/* Layer 3: Dense Axonal Synaptic Network Lines */}
        <lineSegments ref={linesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[linePositions, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            color={lineColor}
            transparent
            opacity={0.24}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </lineSegments>

        {/* Layer 4: Firing Action Potentials (Traveling Impulses with Comet Trails) */}
        <points ref={pulsesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[initialPulsePositions, 3]}
            />
          </bufferGeometry>
          <pointsMaterial
            color={pulseColor}
            size={0.078}
            sizeAttenuation
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

        {/* Layer 5: Outer Synaptic Quantum Cloud */}
        <points ref={outerCloudRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[outerPositions, 3]}
            />
          </bufferGeometry>
          <pointsMaterial
            color={haloColor}
            size={0.020}
            sizeAttenuation
            transparent
            opacity={0.45}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

      </group>

      {/* Quad-Axis Quantum Gyroscopic Stabilizer Rings */}
      {/* Ring 1: Equatorial Latitude Ring */}
      <mesh ref={gyroRing1Ref}>
        <torusGeometry args={[2.85, 0.008, 16, 120]} />
        <meshBasicMaterial 
          color="#22d3ee" 
          transparent 
          opacity={0.35} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Ring 2: Sagittal Polar Ring */}
      <mesh ref={gyroRing2Ref} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[3.10, 0.006, 16, 120]} />
        <meshBasicMaterial 
          color="#818cf8" 
          transparent 
          opacity={0.28} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Ring 3: Oblique Quantum Gyro Ring */}
      <mesh ref={gyroRing3Ref} rotation={[Math.PI / 4, Math.PI / 4, 0]}>
        <torusGeometry args={[3.35, 0.005, 16, 120]} />
        <meshBasicMaterial 
          color="#c084fc" 
          transparent 
          opacity={0.22} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Ring 4: Inner Core Synaptic Halo */}
      <mesh ref={gyroRing4Ref} rotation={[Math.PI / 3, -Math.PI / 6, 0]}>
        <torusGeometry args={[2.15, 0.005, 16, 100]} />
        <meshBasicMaterial 
          color="#38bdf8" 
          transparent 
          opacity={0.25} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>
    </group>
  );
};
