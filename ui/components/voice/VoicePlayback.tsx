"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Play, 
  Pause, 
  Square, 
  Volume2, 
  VolumeX, 
  SkipBack, 
  SkipForward,
  RotateCcw,
  Download,
  Loader2
} from 'lucide-react';
import { VoiceWaveform } from './VoiceWaveform';

interface VoicePlaybackProps {
  audioData?: string | Blob | null;
  agentName?: string;
  isPlaying?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  showControls?: boolean;
  showWaveform?: boolean;
  className?: string;
  autoPlay?: boolean;
}

export function VoicePlayback({
  audioData,
  agentName = 'Assistant',
  isPlaying = false,
  onPlay,
  onPause,
  onStop,
  showControls = true,
  showWaveform = true,
  className = '',
  autoPlay = false,
}: VoicePlaybackProps) {
  const [internalPlaying, setInternalPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playbackRate, setPlaybackRate] = useState(1);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  const playing = isPlaying || internalPlaying;

  // Initialize audio element
  useEffect(() => {
    if (!audioData) return;

    setIsLoading(true);
    setError(null);

    const audio = new Audio();
    audioRef.current = audio;

    // Set up audio source
    if (typeof audioData === 'string') {
      // Base64 audio data
      audio.src = `data:audio/mp3;base64,${audioData}`;
    } else {
      // Blob data
      audio.src = URL.createObjectURL(audioData);
    }

    // Audio event listeners
    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration);
      setIsLoading(false);
    });

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setInternalPlaying(false);
      setCurrentTime(0);
      onStop?.();
    });

    audio.addEventListener('error', (e) => {
      setError('Failed to load audio');
      setIsLoading(false);
      console.error('Audio error:', e);
    });

    audio.addEventListener('play', () => {
      setInternalPlaying(true);
      initializeAudioContext();
    });

    audio.addEventListener('pause', () => {
      setInternalPlaying(false);
    });

    // Set initial volume and playback rate
    audio.volume = volume / 100;
    audio.playbackRate = playbackRate;
    audio.muted = isMuted;

    // Auto play if enabled
    if (autoPlay) {
      audio.play().catch(console.error);
    }

    return () => {
      if (audio.src.startsWith('blob:')) {
        URL.revokeObjectURL(audio.src);
      }
      audio.remove();
      audioRef.current = null;
    };
  }, [audioData, autoPlay]);

  // Initialize audio context for visualization
  const initializeAudioContext = () => {
    if (!audioRef.current || audioContextRef.current) return;

    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyzerRef.current = audioContextRef.current.createAnalyser();
      sourceRef.current = audioContextRef.current.createMediaElementSource(audioRef.current);
      
      sourceRef.current.connect(analyzerRef.current);
      analyzerRef.current.connect(audioContextRef.current.destination);
      
      analyzerRef.current.fftSize = 256;
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
    }
  };

  // Get frequency data for visualization
  const getFrequencyData = (): Uint8Array | null => {
    if (!analyzerRef.current) return null;
    const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);
    analyzerRef.current.getByteFrequencyData(dataArray);
    return dataArray;
  };

  // Control functions
  const handlePlay = () => {
    if (!audioRef.current) return;
    
    audioRef.current.play().catch(console.error);
    onPlay?.();
  };

  const handlePause = () => {
    if (!audioRef.current) return;
    
    audioRef.current.pause();
    onPause?.();
  };

  const handleStop = () => {
    if (!audioRef.current) return;
    
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    setCurrentTime(0);
    onStop?.();
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressRef.current) return;
    
    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume / 100;
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const handlePlaybackRateChange = (rate: number) => {
    setPlaybackRate(rate);
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
    }
  };

  const handleDownload = () => {
    if (typeof audioData === 'string') {
      const link = document.createElement('a');
      link.href = `data:audio/mp3;base64,${audioData}`;
      link.download = `${agentName}_response.mp3`;
      link.click();
    } else if (audioData instanceof Blob) {
      const url = URL.createObjectURL(audioData);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${agentName}_response.wav`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!audioData) {
    return null;
  }

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Waveform Visualization */}
      {showWaveform && (
        <div className="flex justify-center">
          <VoiceWaveform
            isActive={playing}
            audioLevel={playing ? 0.6 : 0}
            frequencyData={getFrequencyData()}
            mode="line"
            size="medium"
            color="#10B981"
          />
        </div>
      )}

      {/* Main Controls */}
      <div className="flex items-center gap-3">
        {/* Play/Pause Button */}
        <motion.button
          className={`
            p-2 rounded-full transition-all duration-200
            ${playing 
              ? 'bg-green-500 text-white shadow-lg' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
            }
            ${isLoading || error ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          onClick={playing ? handlePause : handlePlay}
          disabled={isLoading || !!error}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.05 }}
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : playing ? (
            <Pause size={16} />
          ) : (
            <Play size={16} />
          )}
        </motion.button>

        {/* Progress Bar */}
        <div className="flex-1">
          <div
            ref={progressRef}
            className="h-2 bg-gray-200 rounded-full cursor-pointer relative overflow-hidden"
            onClick={handleSeek}
          >
            <motion.div
              className="h-full bg-green-500 rounded-full"
              style={{ width: `${(currentTime / duration) * 100}%` }}
              initial={{ width: 0 }}
              animate={{ width: `${(currentTime / duration) * 100}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Agent Name */}
        <div className="text-sm text-gray-600 font-medium">
          {agentName}
        </div>
      </div>

      {/* Extended Controls */}
      {showControls && (
        <div className="flex items-center justify-between">
          {/* Left Controls */}
          <div className="flex items-center gap-2">
            {/* Stop */}
            <button
              onClick={handleStop}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              disabled={!playing}
              title="Stop"
            >
              <Square size={14} />
            </button>

            {/* Restart */}
            <button
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.currentTime = 0;
                  setCurrentTime(0);
                }
              }}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              title="Restart"
            >
              <RotateCcw size={14} />
            </button>

            {/* Download */}
            <button
              onClick={handleDownload}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              title="Download"
            >
              <Download size={14} />
            </button>
          </div>

          {/* Center Controls - Playback Rate */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">Speed:</span>
            {[0.75, 1, 1.25, 1.5].map(rate => (
              <button
                key={rate}
                onClick={() => handlePlaybackRateChange(rate)}
                className={`
                  px-2 py-1 text-xs rounded transition-colors
                  ${playbackRate === rate 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {rate}x
              </button>
            ))}
          </div>

          {/* Right Controls - Volume */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggleMute}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>
            
            <input
              type="range"
              min="0"
              max="100"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(Number(e.target.value))}
              className="w-16 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              disabled={isMuted}
            />
            
            <span className="text-xs text-gray-500 w-8">
              {isMuted ? '0%' : `${volume}%`}
            </span>
          </div>
        </div>
      )}

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
    </div>
  );
}