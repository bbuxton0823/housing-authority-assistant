"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
// RecordRTC will be dynamically imported to avoid SSR issues
import type RecordRTC from 'recordrtc';
import { saveRecording } from '../api';

export type VoiceMode = 'push-to-talk' | 'continuous' | 'disabled';
export type VoiceState = 'idle' | 'recording' | 'processing' | 'playing' | 'error';

interface VoiceSettings {
  mode: VoiceMode;
  volume: number;
  enableVoiceActivity: boolean;
  selectedVoice: string;
  autoPlayResponses: boolean;
  noiseSuppressionLevel: number;
  saveRecordings: boolean;
  userId?: string;
  conversationId?: string;
}

interface VoiceData {
  audioBlob: Blob;
  transcript?: string;
  confidence?: number;
}

interface UseVoiceReturn {
  // State
  voiceState: VoiceState;
  isRecording: boolean;
  isPlaying: boolean;
  voiceEnabled: boolean;
  audioLevel: number;
  settings: VoiceSettings;
  error: string | null;
  
  // Controls
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<VoiceData | null>;
  playAudio: (audioData: string | Blob) => Promise<void>;
  stopPlayback: () => void;
  toggleVoice: () => void;
  updateSettings: (settings: Partial<VoiceSettings>) => void;
  
  // Speech Recognition
  startListening: () => void;
  stopListening: () => void;
  
  // Audio Analysis
  audioAnalyzer: AnalyserNode | null;
  getFrequencyData: () => Uint8Array | null;
}

export function useVoice(): UseVoiceReturn {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  // Ensure we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);
  const [settings, setSettings] = useState<VoiceSettings>({
    mode: 'push-to-talk',
    volume: 80,
    enableVoiceActivity: true,
    selectedVoice: 'Rachel',
    autoPlayResponses: true,
    noiseSuppressionLevel: 0.7,
    saveRecordings: true,
  });

  // Refs
  const mediaRecorderRef = useRef<RecordRTC | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);

  // Initialize audio context and analyzer
  const initializeAudioContext = useCallback(async () => {
    if (typeof window === 'undefined') return;
    
    try {
      if (!audioContextRef.current) {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioContext) {
          audioContextRef.current = new AudioContext();
          analyzerRef.current = audioContextRef.current.createAnalyser();
          analyzerRef.current.fftSize = 256;
        }
      }
    } catch (err) {
      console.error('Failed to initialize audio context:', err);
      setError('Audio not supported in this browser');
    }
  }, []);

  // Audio level monitoring
  const monitorAudioLevel = useCallback(() => {
    if (!analyzerRef.current) return;

    const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);
    
    const updateLevel = () => {
      if (analyzerRef.current && voiceState === 'recording') {
        analyzerRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average / 255);
        animationFrameRef.current = requestAnimationFrame(updateLevel);
      }
    };
    
    updateLevel();
  }, [voiceState]);

  // Start recording
  const startRecording = useCallback(async () => {
    if (!isClient || typeof window === 'undefined' || !navigator.mediaDevices) {
      setError('Recording not supported in this environment');
      return;
    }

    try {
      setError(null);
      setVoiceState('recording');
      
      await initializeAudioContext();
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
        }
      });
      
      streamRef.current = stream;
      
      // Connect to analyzer for visual feedback
      if (audioContextRef.current && analyzerRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyzerRef.current);
      }

      // Dynamically import RecordRTC to avoid SSR issues
      const { default: RecordRTC } = await import('recordrtc');
      
      mediaRecorderRef.current = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/webm',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1,
        desiredSampRate: 16000,
        bufferSize: 4096,
      });

      mediaRecorderRef.current.startRecording();
      recordingStartTimeRef.current = Date.now();
      monitorAudioLevel();
      
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Microphone access denied or not available');
      setVoiceState('error');
    }
  }, [isClient, initializeAudioContext, monitorAudioLevel]);

  // Stop recording
  const stopRecording = useCallback(async (): Promise<VoiceData | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        resolve(null);
        return;
      }

      setVoiceState('processing');
      
      mediaRecorderRef.current.stopRecording(async () => {
        const blob = mediaRecorderRef.current?.getBlob();
        const endTime = Date.now();
        const duration = recordingStartTimeRef.current 
          ? (endTime - recordingStartTimeRef.current) / 1000 
          : undefined;
        
        // Cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }
        
        recordingStartTimeRef.current = null;
        setAudioLevel(0);
        setVoiceState('idle');
        
        if (blob) {
          // Save recording to backend if enabled
          if (settings.saveRecordings) {
            try {
              await saveRecording(blob, {
                conversationId: settings.conversationId,
                userId: settings.userId,
                duration,
                language: 'en-US',
              });
            } catch (error) {
              console.error('Failed to save recording:', error);
            }
          }
          
          resolve({ audioBlob: blob });
        } else {
          resolve(null);
        }
      });
    });
  }, []);

  // Play audio
  const playAudio = useCallback(async (audioData: string | Blob) => {
    if (!isClient || typeof window === 'undefined') return;

    try {
      setVoiceState('playing');
      setError(null);

      if (!audioElementRef.current) {
        audioElementRef.current = new Audio();
      }

      const audio = audioElementRef.current;
      
      if (typeof audioData === 'string') {
        // Base64 audio data
        audio.src = `data:audio/mp3;base64,${audioData}`;
      } else {
        // Blob data
        audio.src = URL.createObjectURL(audioData);
      }

      audio.volume = settings.volume / 100;
      
      audio.onended = () => {
        setVoiceState('idle');
        if (typeof audioData === 'object') {
          URL.revokeObjectURL(audio.src);
        }
      };

      audio.onerror = () => {
        setError('Failed to play audio');
        setVoiceState('error');
      };

      await audio.play();
      
    } catch (err) {
      console.error('Failed to play audio:', err);
      setError('Audio playback failed');
      setVoiceState('error');
    }
  }, [isClient, settings.volume]);

  // Stop playback
  const stopPlayback = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.currentTime = 0;
      setVoiceState('idle');
    }
  }, []);

  // Speech recognition setup
  useEffect(() => {
    if (isClient && typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      if (recognitionRef.current) {
        recognitionRef.current.continuous = settings.mode === 'continuous';
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = 'en-US';
      }
    }
  }, [isClient, settings.mode]);

  // Start listening (speech recognition)
  const startListening = useCallback(() => {
    if (recognitionRef.current && settings.enableVoiceActivity) {
      try {
        recognitionRef.current.start();
      } catch (err) {
        console.error('Speech recognition failed:', err);
      }
    }
  }, [settings.enableVoiceActivity]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  // Toggle voice functionality
  const toggleVoice = useCallback(() => {
    setVoiceEnabled(prev => !prev);
    if (voiceEnabled) {
      stopRecording();
      stopPlayback();
      stopListening();
    }
  }, [voiceEnabled, stopRecording, stopPlayback, stopListening]);

  // Update settings
  const updateSettings = useCallback((newSettings: Partial<VoiceSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  // Get frequency data for visualization
  const getFrequencyData = useCallback((): Uint8Array | null => {
    if (!analyzerRef.current) return null;
    const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);
    analyzerRef.current.getByteFrequencyData(dataArray);
    return dataArray;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    // State
    voiceState,
    isRecording: voiceState === 'recording',
    isPlaying: voiceState === 'playing',
    voiceEnabled,
    audioLevel,
    settings,
    error,
    
    // Controls
    startRecording,
    stopRecording,
    playAudio,
    stopPlayback,
    toggleVoice,
    updateSettings,
    
    // Speech Recognition
    startListening,
    stopListening,
    
    // Audio Analysis
    audioAnalyzer: analyzerRef.current,
    getFrequencyData,
  };
}