"use client";

import React, { useState, useEffect, useCallback } from 'react';
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
  AlertCircle
} from 'lucide-react';
import { useConversation } from '@elevenlabs/react';

interface ElevenLabsVoiceAgentProps {
  agentId?: string;
  signedUrl?: string;
  className?: string;
  position?: 'bottom-left' | 'bottom-right' | 'floating' | 'inline';
  theme?: 'light' | 'dark';
  onConversationStart?: () => void;
  onConversationEnd?: () => void;
  onMessage?: (message: any) => void;
  onError?: (error: any) => void;
}

interface ConversationState {
  isConnected: boolean;
  isConnecting: boolean;
  isMuted: boolean;
  volume: number;
  error: string | null;
  conversationId: string | null;
}

export function ElevenLabsVoiceAgent({
  agentId,
  signedUrl,
  className = '',
  position = 'bottom-right',
  theme = 'light',
  onConversationStart,
  onConversationEnd,
  onMessage,
  onError,
}: ElevenLabsVoiceAgentProps) {
  const [state, setState] = useState<ConversationState>({
    isConnected: false,
    isConnecting: false,
    isMuted: false,
    volume: 80,
    error: null,
    conversationId: null,
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [hasPermissions, setHasPermissions] = useState(false);

  // Initialize ElevenLabs conversation hook
  const conversation = useConversation({
    onConnect: () => {
      console.log('ElevenLabs conversation connected');
      setState(prev => ({ 
        ...prev, 
        isConnected: true, 
        isConnecting: false,
        error: null 
      }));
      onConversationStart?.();
    },
    onDisconnect: () => {
      console.log('ElevenLabs conversation disconnected');
      setState(prev => ({ 
        ...prev, 
        isConnected: false, 
        isConnecting: false,
        conversationId: null 
      }));
      onConversationEnd?.();
    },
    onMessage: (message) => {
      console.log('ElevenLabs message received:', message);
      onMessage?.(message);
    },
    onError: (error) => {
      console.error('ElevenLabs conversation error:', error);
      const errorMessage = typeof error === 'string' 
        ? error 
        : error && typeof error === 'object' && 'message' in error 
          ? (error as any).message 
          : 'Connection error';
      
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        isConnecting: false,
        isConnected: false 
      }));
      onError?.(error);
    },
  });

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

  // Start conversation
  const startConversation = useCallback(async () => {
    if (!hasPermissions) {
      const granted = await requestMicrophonePermission();
      if (!granted) return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      let conversationId: string;
      
      if (agentId) {
        // Use agent ID - this is the standard approach
        conversationId = await conversation.startSession({ agentId });
      } else {
        throw new Error('Agent ID must be provided');
      }

      setState(prev => ({ 
        ...prev, 
        conversationId,
        isConnecting: false 
      }));
      
    } catch (error) {
      console.error('Failed to start conversation:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to start conversation',
        isConnecting: false 
      }));
    }
  }, [agentId, signedUrl, conversation, hasPermissions, requestMicrophonePermission]);

  // End conversation
  const endConversation = useCallback(async () => {
    try {
      await conversation.endSession();
    } catch (error) {
      console.error('Error ending conversation:', error);
    }
  }, [conversation]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    setState(prev => ({ ...prev, isMuted: !prev.isMuted }));
    // Note: ElevenLabs SDK mute functionality would go here when available
  }, []);

  // Change volume
  const changeVolume = useCallback((newVolume: number) => {
    setState(prev => ({ ...prev, volume: newVolume }));
    conversation.setVolume({ volume: newVolume / 100 });
  }, [conversation]);

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

  if (position === 'inline') {
    return (
      <div className={`w-full ${className}`}>
        <InlineVoiceInterface
          state={state}
          onStartConversation={startConversation}
          onEndConversation={endConversation}
          onToggleMute={toggleMute}
          onVolumeChange={changeVolume}
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
              onStartConversation={startConversation}
              onEndConversation={endConversation}
              onToggleMute={toggleMute}
              onVolumeChange={changeVolume}
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
          ${state.isConnected 
            ? 'bg-red-500 hover:bg-red-600' 
            : 'bg-blue-500 hover:bg-blue-600'
          }
          ${state.error ? 'ring-4 ring-red-300' : ''}
        `}
        onClick={() => {
          if (state.isConnected) {
            endConversation();
          } else if (isExpanded) {
            setIsExpanded(false);
          } else {
            setIsExpanded(true);
          }
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {state.isConnecting ? (
          <Loader2 className="animate-spin text-white" size={24} />
        ) : state.isConnected ? (
          <PhoneOff className="text-white" size={24} />
        ) : state.error ? (
          <AlertCircle className="text-white" size={24} />
        ) : (
          <Phone className="text-white" size={24} />
        )}
      </motion.button>
    </div>
  );
}

// Expanded interface component
function ExpandedVoiceInterface({
  state,
  onStartConversation,
  onEndConversation,
  onToggleMute,
  onVolumeChange,
  onCollapse,
  theme,
}: {
  state: ConversationState;
  onStartConversation: () => void;
  onEndConversation: () => void;
  onToggleMute: () => void;
  onVolumeChange: (volume: number) => void;
  onCollapse: () => void;
  theme: 'light' | 'dark';
}) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="text-blue-500" size={20} />
          <h3 className="font-semibold">Housing Authority Assistant</h3>
        </div>
        <button
          onClick={onCollapse}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
        >
          <Settings size={16} />
        </button>
      </div>

      {/* Status */}
      <div className="text-center">
        {state.error ? (
          <div className="text-red-500 text-sm">{state.error}</div>
        ) : state.isConnecting ? (
          <div className="text-blue-500 text-sm">Connecting...</div>
        ) : state.isConnected ? (
          <div className="text-green-500 text-sm">Connected • Ready to help</div>
        ) : (
          <div className="text-gray-500 text-sm">Click to start conversation</div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {!state.isConnected ? (
          <button
            onClick={onStartConversation}
            disabled={state.isConnecting}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors
              ${state.isConnecting 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600 text-white'
              }
            `}
          >
            {state.isConnecting ? 'Connecting...' : 'Start Conversation'}
          </button>
        ) : (
          <>
            <button
              onClick={onToggleMute}
              className={`
                p-2 rounded-lg transition-colors
                ${state.isMuted 
                  ? 'bg-red-100 text-red-600' 
                  : 'bg-gray-100 text-gray-600'
                }
              `}
            >
              {state.isMuted ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            
            <button
              onClick={onEndConversation}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              End Call
            </button>
          </>
        )}
      </div>

      {/* Volume Control */}
      {state.isConnected && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Volume2 size={16} className="text-gray-500" />
            <span className="text-sm text-gray-500">Volume</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={state.volume}
            onChange={(e) => onVolumeChange(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      )}
    </div>
  );
}

// Inline interface component
function InlineVoiceInterface({
  state,
  onStartConversation,
  onEndConversation,
  onToggleMute,
  onVolumeChange,
  theme,
}: {
  state: ConversationState;
  onStartConversation: () => void;
  onEndConversation: () => void;
  onToggleMute: () => void;
  onVolumeChange: (volume: number) => void;
  theme: 'light' | 'dark';
}) {
  const themeStyles = theme === 'dark' 
    ? 'bg-gray-900 text-white border-gray-700' 
    : 'bg-white text-gray-900 border-gray-200';

  return (
    <div className={`${themeStyles} rounded-xl border-2 p-6 shadow-lg`}>
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2">
          <MessageSquare className="text-blue-500" size={24} />
          <h3 className="text-lg font-semibold">Voice Assistant</h3>
        </div>

        {state.error ? (
          <div className="text-red-500 text-sm">{state.error}</div>
        ) : state.isConnecting ? (
          <div className="text-blue-500 text-sm">Connecting...</div>
        ) : state.isConnected ? (
          <div className="text-green-500 text-sm">Connected • Listening</div>
        ) : (
          <div className="text-gray-500 text-sm">Click to start voice conversation</div>
        )}

        <div className="flex items-center justify-center gap-4">
          {!state.isConnected ? (
            <button
              onClick={onStartConversation}
              disabled={state.isConnecting}
              className={`
                px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2
                ${state.isConnecting 
                  ? 'bg-gray-300 cursor-not-allowed' 
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
                }
              `}
            >
              {state.isConnecting ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <Phone size={20} />
              )}
              {state.isConnecting ? 'Connecting...' : 'Start Voice Chat'}
            </button>
          ) : (
            <>
              <button
                onClick={onToggleMute}
                className={`
                  p-3 rounded-lg transition-colors
                  ${state.isMuted 
                    ? 'bg-red-100 text-red-600' 
                    : 'bg-gray-100 text-gray-600'
                  }
                `}
              >
                {state.isMuted ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
              
              <button
                onClick={onEndConversation}
                className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
              >
                <PhoneOff size={20} />
                End Call
              </button>
            </>
          )}
        </div>

        {state.isConnected && (
          <div className="space-y-2 max-w-xs mx-auto">
            <div className="flex items-center gap-2 justify-center">
              <Volume2 size={16} className="text-gray-500" />
              <span className="text-sm text-gray-500">Volume: {state.volume}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={state.volume}
              onChange={(e) => onVolumeChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        )}
      </div>
    </div>
  );
}