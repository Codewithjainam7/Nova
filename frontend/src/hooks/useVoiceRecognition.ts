import { useRef, useCallback, useState, useEffect } from 'react';

interface VoiceRecognitionResult {
  transcript: string;
  isFinal: boolean;
}

interface UseVoiceRecognitionOptions {
  onResult?: (result: VoiceRecognitionResult) => void;
  onEnd?: () => void;
  continuous?: boolean;
  language?: string;
}

export const useVoiceRecognition = (options: UseVoiceRecognitionOptions = {}) => {
  const { onResult, onEnd } = options;
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [amplitude, setAmplitude] = useState(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const silenceTimerRef = useRef<any>(null);
  
  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
  }, []);

  const resetSilenceTimer = useCallback(() => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    }, 4000); // 4 seconds of silence stops it
  }, [clearSilenceTimer]);

  // Setup audio analyser for amplitude tracking
  const startAudioAnalysis = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      
      const updateAmplitude = () => {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length / 255;
        setAmplitude(avg);
        
        if (avg > 0.05) {
          resetSilenceTimer();
        }
        
        animFrameRef.current = requestAnimationFrame(updateAmplitude);
      };
      updateAmplitude();
    } catch (e) {
      console.error('Microphone access denied:', e);
    }
  }, [resetSilenceTimer]);

  const stopAudioAnalysis = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current);
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setAmplitude(0);
  }, []);

  const startListening = useCallback(async () => {
    // Mute any old speech
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    
    try {
      stopAudioAnalysis();
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      let mimeType = 'audio/webm';
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        }
      }
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setIsListening(true);
        startAudioAnalysis();
        resetSilenceTimer();
        setInterimTranscript('Listening to your voice...');
      };

      mediaRecorder.onstop = async () => {
        clearSilenceTimer();
        setIsListening(false);
        stopAudioAnalysis();
        setInterimTranscript('Transcribing...');

        if (audioChunksRef.current.length === 0) {
          setInterimTranscript('');
          onEnd?.();
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
        
        try {
          const response = await fetch('http://localhost:8000/api/voice/transcribe', {
            method: 'POST',
            body: audioBlob
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.transcript && data.transcript.trim()) {
              setInterimTranscript('');
              const raw = data.transcript.trim();
              // Clean natural wake phrase prefix if present
              const clean = raw.replace(/^(hey|hi|hello|ok|okay)?\s*(ada|ayda|aida|eda|ida)[\s,.:;!?]*/i, '').trim() || raw;
              onResult?.({ transcript: clean, isFinal: true });
            } else {
              setInterimTranscript('');
            }
          } else {
            console.error('Transcription failed on server');
            setInterimTranscript('');
          }
        } catch (error) {
          console.error('Error uploading audio:', error);
          setInterimTranscript('');
        }
        
        onEnd?.();
      };

      mediaRecorder.start(200);
    } catch (e: any) {
      console.error('Microphone access error:', e);
      setIsListening(false);
    }
  }, [onResult, onEnd, startAudioAnalysis, stopAudioAnalysis, resetSilenceTimer, clearSilenceTimer]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  useEffect(() => {
    return () => {
      stopListening();
      stopAudioAnalysis();
      clearSilenceTimer();
    };
  }, [clearSilenceTimer, stopAudioAnalysis, stopListening]);

  return {
    isListening,
    interimTranscript,
    amplitude,
    startListening,
    stopListening,
    toggleListening,
  };
};

// Active studio audio element tracking
let activeAudio: HTMLAudioElement | null = null;
let lastSpokenText = '';
let lastSpokenTime = 0;

/**
 * ADA Single-Voice Engine:
 * Strictly uses the ADA V2 Studio Neural Voice (nazirlouis/ada_v2 en-GB-SoniaNeural / Kore persona).
 * Never uses Windows SAPI / Zira robotic voices.
 * Deduplicates calls to prevent two voices from ever playing at once.
 */
export const speakResponse = (text: string) => {
  if (!text || !text.trim()) return;

  const cleanText = text.replace(/[*#_`]/g, '').trim();
  if (!cleanText) return;

  // Prevent duplicate execution if triggered multiple times within 3 seconds
  const now = Date.now();
  if (cleanText === lastSpokenText && (now - lastSpokenTime < 3000)) {
    return;
  }
  lastSpokenText = cleanText;
  lastSpokenTime = now;

  // Cancel any existing audio playback
  if (activeAudio) {
    try {
      activeAudio.pause();
      activeAudio.currentTime = 0;
    } catch {}
    activeAudio = null;
  }
  
  // Make sure native browser speech synthesis is permanently silenced
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch {}
  }

  // Play exclusively via the ADA V2 Studio Neural Voice backend endpoint
  try {
    const ttsUrl = `http://localhost:8000/api/tts?text=${encodeURIComponent(cleanText)}`;
    const audio = new Audio(ttsUrl);
    audio.playbackRate = 1.04;
    activeAudio = audio;

    audio.play().catch((err) => {
      console.warn('[ADA Voice] Audio playback note:', err);
    });
  } catch (e) {
    console.error('[ADA Voice] Playback initialization error:', e);
  }
};
