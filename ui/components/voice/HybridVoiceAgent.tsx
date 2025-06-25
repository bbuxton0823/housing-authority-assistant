"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  Settings, 
  Volume2, 
  VolumeX,
  MessageSquare,
  Loader2,
  AlertCircle,
  Users,
  ArrowRight
} from 'lucide-react';

interface HybridVoiceAgentProps {
  className?: string;
  position?: 'bottom-left' | 'bottom-right' | 'floating' | 'inline';
  theme?: 'light' | 'dark';
  conversationId?: string;
  onMessage?: (message: any) => void;
  onAgentChange?: (agent: string) => void;
  onError?: (error: any) => void;
}

interface VoiceState {
  isRecording: boolean;
  isProcessing: boolean;
  isPlaying: boolean;
  currentAgent: string;
  volume: number;
  error: string | null;
  conversationId: string | null;
}

export function HybridVoiceAgent({
  className = '',
  position = 'bottom-right',
  theme = 'light',
  conversationId,
  onMessage,
  onAgentChange,
  onError,
}: HybridVoiceAgentProps) {
  const [state, setState] = useState<VoiceState>({
    isRecording: false,
    isProcessing: false,
    isPlaying: false,
    currentAgent: 'Triage Agent',
    volume: 80,
    error: null,
    conversationId: conversationId || null,
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [hasPermissions, setHasPermissions] = useState(false);

  // Refs for audio recording and playback
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  // Agent voice mapping
  const agentVoices = {
    'Triage Agent': { name: 'Rachel', color: 'blue', description: 'Warm, professional' },
    'General Information Agent': { name: 'Natasha', color: 'purple', description: 'Sophisticated, helpful' },
    'Inspection Agent': { name: 'Daniel', color: 'green', description: 'Clear, authoritative' },
    'Landlord Services Agent': { name: 'Adam', color: 'orange', description: 'Deep, business-like' },
    'HPS Agent': { name: 'Bella', color: 'pink', description: 'Friendly, approachable' },
  };

  // Request microphone permissions
  const requestMicrophonePermission = useCallback(async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setHasPermissions(true);
      setState(prev => ({ ...prev, error: null }));
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Microphone access required for voice conversation' 
      }));
      setHasPermissions(false);
      return false;
    }
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    if (!hasPermissions) {
      const granted = await requestMicrophonePermission();
      if (!granted) return;
    }

    try {
      setState(prev => ({ ...prev, isRecording: true, error: null }));
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Try to use webm format, fallback to default
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/mp4';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = '';
        }
      }
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
        console.log('Audio blob created:', audioBlob.size, 'bytes, type:', audioBlob.type);
        await processVoiceMessage(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
    } catch (error) {
      console.error('Failed to start recording:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to start recording',
        isRecording: false 
      }));
    }
  }, [hasPermissions, requestMicrophonePermission]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      setState(prev => ({ ...prev, isRecording: false, isProcessing: true }));
      mediaRecorderRef.current.stop();
    }
  }, [state.isRecording]);

  // Process voice message through hybrid system
  const processVoiceMessage = useCallback(async (audioBlob: Blob) => {
    try {
      // First, transcribe the audio
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      
      const transcriptionResponse = await fetch('/speech-to-text', {
        method: 'POST',
        body: formData,
      });

      if (!transcriptionResponse.ok) {
        console.error('Transcription response not OK:', transcriptionResponse.status, transcriptionResponse.statusText);
        throw new Error(`Transcription request failed: ${transcriptionResponse.status}`);
      }

      const transcriptionData = await transcriptionResponse.json();
      console.log('Transcription response:', transcriptionData);
      const transcript = transcriptionData.transcript;

      if (!transcript) {
        console.error('No transcript in response:', transcriptionData);
        throw new Error('Failed to transcribe audio');
      }

      // Process through hybrid voice-agent system
      const agentResponse = await fetch('/voice/agent-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: transcript,
          conversation_id: state.conversationId,
          user_id: 'voice_user',
          enable_voice: true,
          enable_navigation: true,
        }),
      });

      const agentData = await agentResponse.json();

      if (agentData.success) {
        // Update state with new agent and conversation ID
        setState(prev => ({
          ...prev,
          currentAgent: agentData.current_agent,
          conversationId: agentData.conversation_id,
          isProcessing: false,
        }));

        // Notify parent components
        onMessage?.(agentData);
        if (agentData.current_agent !== state.currentAgent) {
          onAgentChange?.(agentData.current_agent);
        }

        // Play audio response if available
        if (agentData.audio_base64) {
          await playAudioResponse(agentData.audio_base64);
        }

      } else {
        throw new Error(agentData.message || 'Failed to get agent response');
      }

    } catch (error) {
      console.error('Error processing voice message:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to process voice message',
        isProcessing: false 
      }));
      onError?.(error);
    }
  }, [state.conversationId, state.currentAgent, onMessage, onAgentChange, onError]);

  // Play audio response
  const playAudioResponse = useCallback(async (audioBase64: string) => {
    try {
      setState(prev => ({ ...prev, isPlaying: true }));

      if (!audioElementRef.current) {
        audioElementRef.current = new Audio();
      }

      const audio = audioElementRef.current;
      audio.src = `data:audio/mp3;base64,${audioBase64}`;
      audio.volume = state.volume / 100;

      audio.onended = () => {
        setState(prev => ({ ...prev, isPlaying: false }));
      };

      audio.onerror = () => {
        setState(prev => ({ 
          ...prev, 
          error: 'Failed to play audio response',
          isPlaying: false 
        }));
      };

      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Audio playback failed',
        isPlaying: false 
      }));
    }
  }, [state.volume]);

  // Check permissions on mount
  useEffect(() => {
    requestMicrophonePermission();
  }, [requestMicrophonePermission]);

  // Position styles
  const positionStyles = {
    'bottom-left': 'fixed bottom-4 left-4 z-50',
    'bottom-right': 'fixed bottom-4 right-4 z-50',
    'floating': 'fixed bottom-1/2 right-4 transform translate-y-1/2 z-50',
    'inline': 'relative'
  };

  // Theme styles
  const themeStyles = theme === 'dark' 
    ? 'bg-gray-900 text-white border-gray-700' 
    : 'bg-white text-gray-900 border-gray-200';

  const currentVoice = agentVoices[state.currentAgent as keyof typeof agentVoices] || agentVoices['Triage Agent'];

  if (position === 'inline') {
    return (
      <div className={`w-full ${className}`}>
        <InlineVoiceInterface
          state={state}
          currentVoice={currentVoice}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          theme={theme}
        />
      </div>
    );
  }

  return (
    <div className={`${positionStyles[position]} ${className}`}>
      <AnimatePresence>
        {isExpanded ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className={`
              ${themeStyles} rounded-xl shadow-2xl border-2 p-4 w-80 mb-4
            `}
          >
            <ExpandedVoiceInterface
              state={state}
              currentVoice={currentVoice}
              onStartRecording={startRecording}
              onStopRecording={stopRecording}
              onCollapse={() => setIsExpanded(false)}
              theme={theme}
            />
          </motion.div>
        ) : null}
      </AnimatePresence>

      {/* Floating Action Button */}
      <motion.button
        className={`
          w-14 h-14 rounded-full shadow-lg flex items-center justify-center
          transition-all duration-200 hover:scale-105 active:scale-95
          ${state.isRecording 
            ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
            : state.isProcessing || state.isPlaying
              ? 'bg-yellow-500 hover:bg-yellow-600'
              : `bg-${currentVoice.color}-500 hover:bg-${currentVoice.color}-600`
          }
          ${state.error ? 'ring-4 ring-red-300' : ''}
        `}
        onClick={() => {
          if (state.isRecording) {
            stopRecording();
          } else if (isExpanded) {
            setIsExpanded(false);
          } else {
            setIsExpanded(true);
          }
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {state.isProcessing || state.isPlaying ? (
          <Loader2 className="animate-spin text-white" size={24} />
        ) : state.isRecording ? (
          <MicOff className="text-white" size={24} />
        ) : state.error ? (
          <AlertCircle className="text-white" size={24} />
        ) : (
          <Mic className="text-white" size={24} />
        )}
      </motion.button>

      {/* Agent indicator */}
      <div className="absolute -top-8 left-1/2 transform -translate-x-1/2">
        <div className={`
          text-xs px-2 py-1 rounded-full bg-${currentVoice.color}-100 text-${currentVoice.color}-800 
          border border-${currentVoice.color}-200 whitespace-nowrap
        `}>
          {currentVoice.name}
        </div>
      </div>
    </div>
  );
}

// Expanded interface component
function ExpandedVoiceInterface({
  state,
  currentVoice,
  onStartRecording,
  onStopRecording,
  onCollapse,
  theme,
}: {
  state: VoiceState;
  currentVoice: any;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onCollapse: () => void;
  theme: 'light' | 'dark';
}) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className={`text-${currentVoice.color}-500`} size={20} />
          <div>
            <h3 className="font-semibold">Housing Authority Assistant</h3>
            <p className="text-xs text-gray-500">Current: {state.currentAgent}</p>
          </div>
        </div>
        <button
          onClick={onCollapse}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
        >
          <Settings size={16} />
        </button>
      </div>

      {/* Current Agent Voice */}
      <div className={`p-3 bg-${currentVoice.color}-50 border border-${currentVoice.color}-200 rounded-lg`}>
        <div className="flex items-center gap-2 mb-1">
          <Volume2 className={`text-${currentVoice.color}-600`} size={16} />
          <span className={`text-${currentVoice.color}-800 font-medium`}>{currentVoice.name}</span>
        </div>
        <p className={`text-xs text-${currentVoice.color}-600`}>{currentVoice.description}</p>
      </div>

      {/* Status */}
      <div className="text-center">
        {state.error ? (
          <div className="text-red-500 text-sm">{state.error}</div>
        ) : state.isProcessing ? (
          <div className="text-blue-500 text-sm flex items-center justify-center gap-2">
            <Loader2 className="animate-spin" size={16} />
            Processing through {state.currentAgent}...
          </div>
        ) : state.isPlaying ? (
          <div className="text-green-500 text-sm flex items-center justify-center gap-2">
            <Volume2 size={16} />
            {currentVoice.name} is speaking...
          </div>
        ) : state.isRecording ? (
          <div className="text-red-500 text-sm flex items-center justify-center gap-2">
            <Mic className="animate-pulse" size={16} />
            Listening...
          </div>
        ) : (
          <div className="text-gray-500 text-sm">Click to start voice conversation</div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {state.isRecording ? (
          <button
            onClick={onStopRecording}
            className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
          >
            <MicOff size={16} />
            Stop Recording
          </button>
        ) : (
          <button
            onClick={onStartRecording}
            disabled={state.isProcessing || state.isPlaying}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${state.isProcessing || state.isPlaying
                ? 'bg-gray-300 cursor-not-allowed' 
                : `bg-${currentVoice.color}-500 hover:bg-${currentVoice.color}-600 text-white`
              }
            `}
          >
            <Mic size={16} />
            {state.isProcessing ? 'Processing...' : state.isPlaying ? 'Playing...' : 'Start Recording'}
          </button>
        )}
      </div>
    </div>
  );
}

// Inline interface component
function InlineVoiceInterface({
  state,
  currentVoice,
  onStartRecording,
  onStopRecording,
  theme,
}: {
  state: VoiceState;
  currentVoice: any;
  onStartRecording: () => void;
  onStopRecording: () => void;
  theme: 'light' | 'dark';
}) {
  const themeStyles = theme === 'dark' 
    ? 'bg-gray-900 text-white border-gray-700' 
    : 'bg-white text-gray-900 border-gray-200';

  return (
    <div className={`${themeStyles} rounded-xl border-2 p-6 shadow-lg`}>
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2">
          <Users className={`text-${currentVoice.color}-500`} size={24} />
          <div>
            <h3 className="text-lg font-semibold">Voice Assistant</h3>
            <p className="text-sm text-gray-500">Speaking as: {currentVoice.name} ({state.currentAgent})</p>
          </div>
        </div>

        {state.error ? (
          <div className="text-red-500 text-sm">{state.error}</div>
        ) : state.isProcessing ? (
          <div className="text-blue-500 text-sm">Processing through {state.currentAgent}...</div>
        ) : state.isPlaying ? (
          <div className="text-green-500 text-sm">{currentVoice.name} is speaking...</div>
        ) : state.isRecording ? (
          <div className="text-red-500 text-sm">Listening...</div>
        ) : (
          <div className="text-gray-500 text-sm">Click to start voice conversation with agents</div>
        )}

        <div className="flex items-center justify-center gap-4">
          {state.isRecording ? (
            <button
              onClick={onStopRecording}
              className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
            >
              <MicOff size={20} />
              Stop Recording
            </button>
          ) : (
            <button
              onClick={onStartRecording}
              disabled={state.isProcessing || state.isPlaying}
              className={`
                px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2
                ${state.isProcessing || state.isPlaying
                  ? 'bg-gray-300 cursor-not-allowed' 
                  : `bg-${currentVoice.color}-500 hover:bg-${currentVoice.color}-600 text-white`
                }
              `}
            >
              <Mic size={20} />
              {state.isProcessing ? 'Processing...' : state.isPlaying ? 'Playing...' : 'Start Voice Chat'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}