import React, { useState, useCallback, useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { NeuralNetwork } from './NeuralNetwork';
import { VoiceOrb } from './VoiceOrb';
import { ResponseOverlay } from './ResponseOverlay';
import { VoiceController } from '../Voice/VoiceController';
import { GestureController } from './GestureController';
import { SystemHUD } from './SystemHUD';
import { WidgetCustomizerModal } from '../HUD/WidgetCustomizerModal';
import { useVoiceRecognition, speakResponse } from '../../hooks/useVoiceRecognition';
import { useNovaWebSocket } from '../../contexts/NovaWebSocket';
import { useNovaStore } from '../../store/useNovaStore';

// Ambient Floating Holographic Synaptic Dust
const HoloDust: React.FC = () => {
  const pointsRef = useRef<THREE.Points>(null!);
  const count = 150;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 16;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 16;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (pointsRef.current) {
      const time = state.clock.getElapsedTime();
      pointsRef.current.rotation.y = time * 0.015;
      const pos = pointsRef.current.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < count; i++) {
        let y = pos[i * 3 + 1] + 0.002;
        if (y > 5) y = -4;
        pos[i * 3 + 1] = y;
      }
      pointsRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#22d3ee"
        transparent
        opacity={0.3}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

export const BrainScene: React.FC = () => {
  const [response, setResponse] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const { sendChat } = useNovaWebSocket();
  const { messages, isStreaming } = useNovaStore();

  // Watch for new assistant messages
  const lastAssistantMsg = messages.filter(m => m.role === 'assistant').slice(-1)[0];
  
  // Update response when streaming completes
  React.useEffect(() => {
    if (lastAssistantMsg && !isStreaming && lastAssistantMsg.content) {
      const content = lastAssistantMsg.content;
      if (content && content !== 'Thinking...' && content !== '') {
        setResponse(content);
        setIsProcessing(false);
        speakResponse(content);
      }
    }
  }, [lastAssistantMsg?.content, isStreaming]);

  const handleVoiceResult = useCallback((result: { transcript: string; isFinal: boolean }) => {
    if (result.isFinal) {
      setIsProcessing(true);
      setResponse('');
      sendChat(result.transcript);
    }
  }, [sendChat]);

  const handleVoiceEnd = useCallback(() => {
    // Voice session ended
  }, []);

  const { isListening, interimTranscript, amplitude, toggleListening } = useVoiceRecognition({
    onResult: handleVoiceResult,
    onEnd: handleVoiceEnd,
  });

  const handleSendText = useCallback((text: string) => {
    setIsProcessing(true);
    setResponse('');
    sendChat(text);
  }, [sendChat]);

  return (
    <div className="w-full h-full relative overflow-hidden select-none bg-[#020409]">
      {/* Sci-Fi Atmospheric Ambient Vignette & Backlight */}
      <div 
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background: 'radial-gradient(circle at 50% 40%, rgba(10, 28, 56, 0.45) 0%, rgba(3, 8, 20, 0.8) 55%, #020409 100%)'
        }}
      />
      
      {/* Subtle Holographic Grid Pattern */}
      <div className="absolute inset-0 pointer-events-none z-0 cyber-grid-bg opacity-30" />

      {/* Cyber Horizon Glow Line */}
      <div className="absolute top-[68%] inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/25 to-transparent pointer-events-none z-0" />

      {/* Three.js Canvas */}
      <Canvas
        camera={{ position: [0, 0, 7.2], fov: 48 }}
        style={{ background: 'transparent', zIndex: 5, position: 'absolute', inset: 0 }}
        gl={{ antialias: true, alpha: true }}
      >
        {/* Horizon Depth Fog - Fades grid seamlessly into deep space */}
        <fog attach="fog" args={['#020409', 7, 24]} />

        {/* Primary Cyber Floor Grid */}
        <gridHelper 
          args={[36, 36, '#00f0ff', '#003852']} 
          position={[0, -2.8, 0]} 
          rotation={[0, 0, 0]} 
        />
        
        {/* Secondary Expansive Horizon Grid */}
        <gridHelper 
          args={[60, 15, '#38bdf8', '#001a2b']} 
          position={[0, -2.81, 0]} 
          rotation={[0, 0, 0]} 
        />

        {/* Cinematic Dual Cyber Lighting */}
        <ambientLight intensity={0.15} />
        <pointLight position={[12, 10, 10]} intensity={0.4} color="#38bdf8" />
        <pointLight position={[-12, -8, -10]} intensity={0.25} color="#a855f7" />
        <pointLight position={[0, -4, 2]} intensity={0.3} color="#06b6d4" />

        {/* Neural Network */}
        <NeuralNetwork 
          isListening={isListening} 
          isProcessing={isProcessing} 
          amplitude={amplitude} 
        />

        {/* Central Voice Orb */}
        <VoiceOrb 
          isListening={isListening} 
          isProcessing={isProcessing} 
          amplitude={amplitude} 
        />

        {/* Ambient Synaptic Dust */}
        <HoloDust />
        
        {/* Hand Gesture Camera Controller */}
        <GestureController />

        {/* User Orbit Controls */}
        <OrbitControls 
          enableZoom={true}
          enablePan={false}
          minDistance={4}
          maxDistance={12}
          autoRotate={!isListening && !isProcessing}
          autoRotateSpeed={0.25}
          dampingFactor={0.05}
          enableDamping
        />
      </Canvas>

      {/* Advanced HUD */}
      <SystemHUD />

      {/* Response & Transcript Overlay */}
      <ResponseOverlay
        response={response}
        interimTranscript={interimTranscript}
        isListening={isListening}
        isProcessing={isProcessing}
      />

      {/* Voice Controller */}
      <VoiceController
        isListening={isListening}
        onToggleListening={toggleListening}
        onSendText={handleSendText}
        isProcessing={isProcessing}
      />

      {/* Top-Level HUD Customizer Modal (z-[100]) */}
      <WidgetCustomizerModal />
    </div>
  );
};
