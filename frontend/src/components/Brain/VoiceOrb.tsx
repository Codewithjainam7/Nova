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

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    // Inner orb pulsing
    if (innerRef.current) {
      const baseScale = 0.25;
      const pulse = isListening 
        ? baseScale + amplitude * 0.15 
        : isProcessing 
          ? baseScale + Math.sin(time * 6) * 0.04 
          : baseScale + Math.sin(time * 1.5) * 0.02;
      innerRef.current.scale.setScalar(pulse);

      const mat = innerRef.current.material as THREE.MeshBasicMaterial;
      if (isListening) {
        mat.color.lerpColors(new THREE.Color('#00e5ff'), new THREE.Color('#00bcd4'), Math.sin(time * 3) * 0.5 + 0.5);
      } else if (isProcessing) {
        mat.color.lerpColors(new THREE.Color('#7c4dff'), new THREE.Color('#e040fb'), Math.sin(time * 4) * 0.5 + 0.5);
      } else {
        mat.color.set('#4fc3f7');
      }
    }

    // Glow sphere
    if (glowRef.current) {
      const glowScale = 0.45 + (isListening ? amplitude * 0.2 : Math.sin(time * 1.2) * 0.03);
      glowRef.current.scale.setScalar(glowScale);
      const mat = glowRef.current.material as THREE.MeshBasicMaterial;
      mat.opacity = isListening ? 0.15 + amplitude * 0.1 : 0.08;
    }

    // Rotating rings
    if (ringRef.current) {
      ringRef.current.rotation.z = time * 0.5;
      ringRef.current.rotation.x = Math.sin(time * 0.3) * 0.3;
      const rScale = 0.6 + (isListening ? amplitude * 0.1 : 0);
      ringRef.current.scale.setScalar(rScale);
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.z = -time * 0.3;
      ring2Ref.current.rotation.y = Math.cos(time * 0.2) * 0.4;
      const rScale = 0.75 + (isListening ? amplitude * 0.08 : 0);
      ring2Ref.current.scale.setScalar(rScale);
    }
  });

  return (
    <group>
      {/* Inner core orb */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial color="#4fc3f7" transparent opacity={0.9} />
      </mesh>

      {/* Glow sphere */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial color="#4fc3f7" transparent opacity={0.08} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* Orbital ring 1 */}
      <mesh ref={ringRef}>
        <torusGeometry args={[1, 0.005, 16, 100]} />
        <meshBasicMaterial color="#00e5ff" transparent opacity={0.3} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* Orbital ring 2 */}
      <mesh ref={ring2Ref}>
        <torusGeometry args={[1, 0.004, 16, 100]} />
        <meshBasicMaterial color="#0288d1" transparent opacity={0.2} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
    </group>
  );
};
