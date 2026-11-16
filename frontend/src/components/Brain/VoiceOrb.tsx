import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  amplitude: number;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({ isListening, isProcessing, amplitude }) => {
  const innerRef = useRef<THREE.Mesh>(null!);
  const glowRef = useRef<THREE.Mesh>(null!);
  const ringRef = useRef<THREE.Mesh>(null!);
  const ring2Ref = useRef<THREE.Mesh>(null!);
  const wireCoreRef = useRef<THREE.Mesh>(null!);

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    // Inner arc reactor orb pulsing
    if (innerRef.current) {
      const baseScale = 0.28;
      const pulse = isListening 
        ? baseScale + amplitude * 0.25 
        : isProcessing 
          ? baseScale + Math.sin(time * 8) * 0.05 
          : baseScale + Math.sin(time * 2.0) * 0.025;
      innerRef.current.scale.setScalar(pulse);

      const mat = innerRef.current.material as THREE.MeshBasicMaterial;
      if (isListening) {
        mat.color.lerpColors(new THREE.Color('#22d3ee'), new THREE.Color('#38bdf8'), Math.sin(time * 4) * 0.5 + 0.5);
      } else if (isProcessing) {
        mat.color.lerpColors(new THREE.Color('#a855f7'), new THREE.Color('#ec4899'), Math.sin(time * 5) * 0.5 + 0.5);
      } else {
        mat.color.set('#38bdf8');
      }
    }

    // Outer plasma glow sphere
    if (glowRef.current) {
      const glowScale = 0.55 + (isListening ? amplitude * 0.35 : Math.sin(time * 1.5) * 0.04);
      glowRef.current.scale.setScalar(glowScale);
      const mat = glowRef.current.material as THREE.MeshBasicMaterial;
      mat.opacity = isListening ? 0.22 + amplitude * 0.15 : isProcessing ? 0.18 : 0.12;
    }

    // Wireframe energy containment core
    if (wireCoreRef.current) {
      wireCoreRef.current.rotation.y = time * 0.6;
      wireCoreRef.current.rotation.x = time * 0.4;
      const wireScale = 0.38 + (isListening ? amplitude * 0.15 : 0);
      wireCoreRef.current.scale.setScalar(wireScale);
    }

    // Segmented orbital rings
    if (ringRef.current) {
      ringRef.current.rotation.z = time * 0.8;
      ringRef.current.rotation.x = Math.sin(time * 0.4) * 0.4;
      const rScale = 0.72 + (isListening ? amplitude * 0.15 : 0);
      ringRef.current.scale.setScalar(rScale);
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.z = -time * 0.5;
      ring2Ref.current.rotation.y = Math.cos(time * 0.3) * 0.5;
      const rScale = 0.88 + (isListening ? amplitude * 0.12 : 0);
      ring2Ref.current.scale.setScalar(rScale);
    }
  });

  return (
    <group>
      {/* Inner high-energy arc reactor core */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.95} />
      </mesh>

      {/* Wireframe crystalline plasma shell */}
      <mesh ref={wireCoreRef}>
        <icosahedronGeometry args={[1, 2]} />
        <meshBasicMaterial 
          color="#67e8f9" 
          wireframe 
          transparent 
          opacity={0.35} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Outer atmospheric aura */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial 
          color="#22d3ee" 
          transparent 
          opacity={0.12} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Orbital Reactor Ring 1 */}
      <mesh ref={ringRef}>
        <torusGeometry args={[1, 0.006, 16, 100]} />
        <meshBasicMaterial 
          color="#38bdf8" 
          transparent 
          opacity={0.45} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>

      {/* Orbital Reactor Ring 2 */}
      <mesh ref={ring2Ref}>
        <torusGeometry args={[1, 0.005, 16, 100]} />
        <meshBasicMaterial 
          color="#818cf8" 
          transparent 
          opacity={0.35} 
          blending={THREE.AdditiveBlending} 
          depthWrite={false} 
        />
      </mesh>
    </group>
  );
};
