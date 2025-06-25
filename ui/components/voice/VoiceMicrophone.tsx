"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, MicOff, Square, Play, Pause, Volume2, VolumeX } from 'lucide-react';
import { VoiceWaveform, VoicePulse } from './VoiceWaveform';
import { useVoice, VoiceMode } from '@/lib/hooks/useVoice';

interface VoiceMicrophoneProps {
  onVoiceMessage?: (message: string) => void;
  onAudioRecorded?: (audioBlob: Blob) => void;
  disabled?: boolean;
  className?: string;
  mode?: 'compact' | 'full' | 'minimal';
}

export function VoiceMicrophone({
  onVoiceMessage,
  onAudioRecorded,
  disabled = false,
  className = '',
  mode = 'full',
}: VoiceMicrophoneProps) {
  const {
    voiceState,
    isRecording,
    isPlaying,
    voiceEnabled,
    audioLevel,
    settings,
    error,
    startRecording,
    stopRecording,
    playAudio,
    stopPlayback,
    toggleVoice,
    updateSettings,
    getFrequencyData,
  } = useVoice();

  const [transcript, setTranscript] = useState('');
  const [showTranscript, setShowTranscript] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // Recording timer
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration(prev => prev + 0.1);
      }, 100);
    } else {
      setRecordingDuration(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  // Handle recording start/stop
  const handleMicrophoneClick = async () => {
    if (disabled || !voiceEnabled) {
      if (!voiceEnabled) toggleVoice();
      return;
    }

    if (isRecording) {
      const voiceData = await stopRecording();
      if (voiceData && onAudioRecorded) {
        onAudioRecorded(voiceData.audioBlob);
      }
    } else {
      await startRecording();
    }
  };

  // Handle push-to-talk
  const handleMouseDown = () => {
    if (settings.mode === 'push-to-talk' && !isRecording && voiceEnabled && !disabled) {
      startRecording();
    }
  };

  const handleMouseUp = () => {
    if (settings.mode === 'push-to-talk' && isRecording) {
      stopRecording().then(voiceData => {
        if (voiceData && onAudioRecorded) {
          onAudioRecorded(voiceData.audioBlob);
        }
      });
    }
  };

  // Render different modes
  if (mode === 'minimal') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <motion.button
          className={`
            p-2 rounded-full transition-all duration-200
            ${voiceEnabled 
              ? isRecording 
                ? 'bg-red-500 text-white shadow-lg' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          onClick={handleMicrophoneClick}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          disabled={disabled}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.05 }}
        >
          {voiceEnabled ? (
            isRecording ? <Square size={16} /> : <Mic size={16} />
          ) : (
            <MicOff size={16} />
          )}
        </motion.button>
        
        {(isRecording || isPlaying) && (
          <VoicePulse 
            isActive={isRecording || isPlaying} 
            size="small"
            color={isRecording ? '#EF4444' : '#3B82F6'} 
          />
        )}
      </div>
    );
  }

  if (mode === 'compact') {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Microphone Button */}
        <motion.button
          className={`
            relative p-3 rounded-full transition-all duration-200
            ${voiceEnabled 
              ? isRecording 
                ? 'bg-red-500 text-white shadow-lg' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          onClick={handleMicrophoneClick}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          disabled={disabled}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.05 }}
        >
          {voiceEnabled ? (
            isRecording ? <Square size={20} /> : <Mic size={20} />
          ) : (
            <MicOff size={20} />
          )}
          
          {/* Recording indicator */}
          {isRecording && (
            <motion.div
              className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
        </motion.button>

        {/* Waveform */}
        {(isRecording || isPlaying) && (
          <VoiceWaveform
            isActive={isRecording || isPlaying}
            audioLevel={audioLevel}
            frequencyData={getFrequencyData()}
            mode="bars"
            size="small"
            color={isRecording ? '#EF4444' : '#3B82F6'}
          />
        )}

        {/* Status text */}
        <div className="text-sm text-gray-600">
          {isRecording && `Recording... ${recordingDuration.toFixed(1)}s`}
          {isPlaying && 'Playing response...'}
          {voiceState === 'processing' && 'Processing...'}
        </div>
      </div>
    );
  }

  // Full mode
  return (
    <div className={`flex flex-col items-center gap-4 p-4 ${className}`}>
      {/* Main Voice Interface */}
      <div className="relative flex items-center justify-center">
        {/* Waveform Visualization */}
        <VoiceWaveform
          isActive={isRecording || isPlaying}
          audioLevel={audioLevel}
          frequencyData={getFrequencyData()}
          mode="orb"
          size="large"
          color={isRecording ? '#EF4444' : isPlaying ? '#10B981' : '#3B82F6'}
        />

        {/* Central Microphone Button */}
        <motion.button
          className={`
            absolute p-4 rounded-full transition-all duration-200 z-10
            ${voiceEnabled 
              ? isRecording 
                ? 'bg-red-500 text-white shadow-2xl' 
                : 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg'
              : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          onClick={handleMicrophoneClick}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          disabled={disabled}
          whileTap={{ scale: 0.9 }}
          whileHover={{ scale: 1.1 }}
        >
          {voiceEnabled ? (
            isRecording ? <Square size={24} /> : <Mic size={24} />
          ) : (
            <MicOff size={24} />
          )}
        </motion.button>

        {/* Recording duration indicator */}
        {isRecording && (
          <motion.div
            className="absolute top-0 right-0 bg-red-500 text-white text-xs px-2 py-1 rounded-full"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            {recordingDuration.toFixed(1)}s
          </motion.div>
        )}
      </div>

      {/* Status and Controls */}
      <div className="flex flex-col items-center gap-2 text-center">
        {/* Status Text */}
        <div className="text-sm font-medium">
          {!voiceEnabled && 'Voice disabled'}
          {voiceEnabled && voiceState === 'idle' && (
            settings.mode === 'push-to-talk' 
              ? 'Hold to record' 
              : 'Click to record'
          )}
          {voiceState === 'recording' && 'Recording...'}
          {voiceState === 'processing' && 'Processing...'}
          {voiceState === 'playing' && 'Playing response...'}
          {voiceState === 'error' && 'Error occurred'}
        </div>

        {/* Mode indicator */}
        <div className="text-xs text-gray-500 capitalize">
          {settings.mode.replace('-', ' ')} mode
        </div>

        {/* Quick Controls */}
        <div className="flex items-center gap-3 mt-2">
          {/* Voice toggle */}
          <button
            onClick={toggleVoice}
            className={`
              p-2 rounded-lg transition-colors
              ${voiceEnabled 
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200' 
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }
            `}
            title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
          >
            {voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>

          {/* Mode toggle */}
          <button
            onClick={() => updateSettings({ 
              mode: settings.mode === 'push-to-talk' ? 'continuous' : 'push-to-talk' 
            })}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={!voiceEnabled}
          >
            {settings.mode === 'push-to-talk' ? 'PTT' : 'Continuous'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded-lg text-sm"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Transcript Display */}
      <AnimatePresence>
        {showTranscript && transcript && (
          <motion.div
            className="bg-gray-100 border border-gray-300 p-3 rounded-lg text-sm max-w-md"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="font-medium text-gray-700 mb-1">Transcript:</div>
            <div className="text-gray-600">{transcript}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}