import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface NeuralNetworkProps {
  isListening: boolean;
  isProcessing: boolean;
  amplitude: number;
}

export const NeuralNetwork: React.FC<NeuralNetworkProps> = ({ isListening, isProcessing, amplitude }) => {
  const nodesRef = useRef<THREE.Points>(null!);
  const linesRef = useRef<THREE.LineSegments>(null!);
  const outerNodesRef = useRef<THREE.Points>(null!);
  const labelsGroupRef = useRef<THREE.Group>(null!);

  // Generate neural network geometry
  const { nodePositions, linePositions, outerPositions, labels } = useMemo(() => {
    const nodeCount = 500;
    const outerCount = 1000;
    const positions = new Float32Array(nodeCount * 3);
    const outerPositions = new Float32Array(outerCount * 3);
    
    // Create nodes distributed in a brain-like sphere
    for (let i = 0; i < nodeCount; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      const r = 2.0 + (Math.random() - 0.5) * 0.8;
      
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.8; // Flatten slightly
      positions[i * 3 + 2] = r * Math.cos(phi);
    }

    // Outer particles
    for (let i = 0; i < outerCount; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      const r = 3.0 + Math.random() * 1.5;
      
      outerPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      outerPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      outerPositions[i * 3 + 2] = r * Math.cos(phi);
    }

    // Connect nearby nodes
    const maxConnections = 1200;
    const linePositions = new Float32Array(maxConnections * 6);
    let lineIdx = 0;

    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        const dx = positions[i * 3] - positions[j * 3];
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist < 0.7 && lineIdx < maxConnections) {
          linePositions[lineIdx * 6] = positions[i * 3];
          linePositions[lineIdx * 6 + 1] = positions[i * 3 + 1];
          linePositions[lineIdx * 6 + 2] = positions[i * 3 + 2];
          linePositions[lineIdx * 6 + 3] = positions[j * 3];
          linePositions[lineIdx * 6 + 4] = positions[j * 3 + 1];
          linePositions[lineIdx * 6 + 5] = positions[j * 3 + 2];
          lineIdx++;
        }
      }
    }

    const labels = [
      { text: "ADA_CORE // 01", position: [positions[0], positions[1], positions[2]] as [number, number, number] },
      { text: "MEMORY_STORE // ACTIVE", position: [positions[30], positions[31], positions[32]] as [number, number, number] },
      { text: "VISION_NODE // ONLINE", position: [positions[60], positions[61], positions[62]] as [number, number, number] },
      { text: "NEURAL_SYNAPSE // 99.4%", position: [positions[90], positions[91], positions[92]] as [number, number, number] }
    ];

    return {
      nodePositions: positions,
      linePositions: linePositions.slice(0, lineIdx * 6),
      outerPositions,
      labels
    };
  }, []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    const pulse = 1 + amplitude * 0.5;

    // Rotate core nodes
    if (nodesRef.current) {
      nodesRef.current.rotation.y = t * 0.08;
      nodesRef.current.rotation.x = Math.sin(t * 0.05) * 0.1;
      nodesRef.current.scale.set(pulse, pulse, pulse);
    }

    // Rotate lines
    if (linesRef.current) {
      linesRef.current.rotation.y = t * 0.08;
      linesRef.current.rotation.x = Math.sin(t * 0.05) * 0.1;
      linesRef.current.scale.set(pulse, pulse, pulse);
    }

    // Rotate outer cloud counter-direction
    if (outerNodesRef.current) {
      outerNodesRef.current.rotation.y = -t * 0.04;
      outerNodesRef.current.rotation.z = Math.cos(t * 0.03) * 0.1;
    }

    // Rotate labels
    if (labelsGroupRef.current) {
      labelsGroupRef.current.rotation.y = t * 0.08;
      labelsGroupRef.current.rotation.x = Math.sin(t * 0.05) * 0.1;
    }
  });

  // Dynamic colors based on state
  const nodeColor = isListening ? '#00e5ff' : isProcessing ? '#aa66ff' : '#4fc3f7';
  const lineColor = isListening ? '#00b8d4' : isProcessing ? '#7c4dff' : '#0277bd';
  const outerColor = isListening ? '#00e5ff' : '#1a237e';

  return (
    <group>
      {/* Core neural nodes */}
      <points ref={nodesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[nodePositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          color={nodeColor}
          size={0.015}
          sizeAttenuation
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Synaptic connections */}
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
          opacity={0.15}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </lineSegments>

      {/* Outer floating particles */}
      <points ref={outerNodesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[outerPositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          color={outerColor}
          size={0.015}
          sizeAttenuation
          transparent
          opacity={0.4}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Algorithm Labels */}
      <group ref={labelsGroupRef}>
        {labels.map((label, idx) => (
          <Html 
            key={idx} 
            position={new THREE.Vector3(...label.position)}
            center
            distanceFactor={10}
            zIndexRange={[100, 0]}
            style={{ pointerEvents: 'none' }}
          >
            <div className={`px-1.5 py-0.5 rounded bg-black/80 border text-[7px] font-mono tracking-widest whitespace-nowrap transition-all duration-500
              ${isListening ? 'border-cyan-500/80 text-cyan-200' : 
                isProcessing ? 'border-purple-500/80 text-purple-200' : 
                'border-white/20 text-white/50'}`}
            >
              {label.text}
            </div>
          </Html>
        ))}
      </group>
    </group>
  );
};
