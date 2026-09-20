import React, { useState, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { NeuralNetwork } from './NeuralNetwork';
import { VoiceOrb } from './VoiceOrb';
import { ResponseOverlay } from './ResponseOverlay';
import { VoiceController } from '../Voice/VoiceController';
import { GestureController } from './GestureController';
import { SystemHUD } from './SystemHUD';
import { useVoiceRecognition, speakResponse } from '../../hooks/useVoiceRecognition';
import { useNovaWebSocket } from '../../contexts/NovaWebSocket';
import { useNovaStore } from '../../store/useNovaStore';

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
    <div className="w-full h-full relative bg-[#030508]">
      {/* Three.js Canvas */}
      <Canvas
        camera={{ position: [0, 0, 7], fov: 50 }}
        style={{ background: 'transparent', zIndex: 5 }}
        gl={{ antialias: true, alpha: true }}
      >
        {/* Floor grid */}
        <gridHelper args={[30, 30, '#00e5ff', '#004d66']} position={[0, -3, 0]} rotation={[0, 0, 0]} />
        
        {/* Ambient light */}
        <ambientLight intensity={0.1} />
        <pointLight position={[10, 10, 10]} intensity={0.3} color="#4fc3f7" />
        <pointLight position={[-10, -10, -10]} intensity={0.2} color="#7c4dff" />

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
        
        {/* Hand Gesture Camera Controller */}
        <GestureController />

        {/* Allow user to orbit the brain with mouse */}
        <OrbitControls 
          enableZoom={true}
          enablePan={false}
          minDistance={4}
          maxDistance={12}
          autoRotate={!isListening && !isProcessing}
          autoRotateSpeed={0.3}
          dampingFactor={0.05}
          enableDamping
        />
      </Canvas>

      {/* Title */}
      <div className="absolute top-8 left-1/2 -translate-x-1/2 z-10 text-center">
        <h1 className="text-2xl font-light tracking-[0.3em] text-white/50 uppercase">ADA</h1>
        <p className="text-[10px] tracking-[0.2em] text-white/20 mt-1 uppercase">Autonomous AI Operating System</p>
      </div>

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
    </div>
  );
};
