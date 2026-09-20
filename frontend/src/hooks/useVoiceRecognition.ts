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
        const avg = sum / dataArray.length / 255; // Normalize 0-1
        setAmplitude(avg);
        
        // If we hear loud noise, reset the silence timer
        if (avg > 0.05) {
            resetSilenceTimer();
        }
        
        animFrameRef.current = requestAnimationFrame(updateAmplitude);
      };
      updateAmplitude();
    } catch (e) {
      console.error('Microphone access denied:', e);
    }
  }, []);

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
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    
    try {
      // Clean up any old streams
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
              onResult?.({ transcript: data.transcript.trim(), isFinal: true });
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

      mediaRecorder.start(200); // Collect data every 200ms
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

  // Cleanup on unmount
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

// Utility: make NOVA speak a response
export const speakResponse = (text: string) => {
  if (!window.speechSynthesis) return;
  
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();
  
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  const attemptSpeak = (retryCount = 0) => {
    let voices = window.speechSynthesis.getVoices();
    
    // If voices haven't loaded yet (common on page load), wait and retry up to 10 times
    if (voices.length === 0 && retryCount < 10) {
        setTimeout(() => attemptSpeak(retryCount + 1), 100);
        return;
    }
    
    const femaleKeywords = ['zira', 'samantha', 'hazel', 'female', 'susan', 'lisa', 'jenny', 'aria'];
    const maleKeywords = ['david', 'mark', 'george', 'paul', 'male', 'guy', 'ryan', 'brian'];
    
    // Filter out any voice with a male keyword
    let safeVoices = voices.filter(v => !maleKeywords.some(name => v.name.toLowerCase().includes(name)));
    
    // Prioritize known female voices
    const preferred = safeVoices.find(v => femaleKeywords.some(name => v.name.toLowerCase().includes(name)))
      || safeVoices.find(v => v.lang.startsWith('en-US')) 
      || safeVoices.find(v => v.lang.startsWith('en'))
      || safeVoices[0]; // Strict fallback to a non-male voice, never the unfiltered list
      
    if (preferred) utterance.voice = preferred;
    
    window.speechSynthesis.speak(utterance);
  };
  
  attemptSpeak();
};
