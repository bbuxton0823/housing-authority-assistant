"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import type { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import { SeatMap } from "./seat-map";
import { VoiceMicrophone } from "./voice/VoiceMicrophone";
import { VoicePlayback } from "./voice/VoicePlayback";
import { VoiceSettings } from "./voice/VoiceSettings";
import { useVoice } from "@/lib/hooks/useVoice";
import { Settings, Volume2, VolumeX } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { uploadAudio } from "@/lib/api";

interface ChatProps {
  messages: Message[];
  onSendMessage: (message: string, options?: { enableVoice?: boolean; enableNavigation?: boolean }) => void;
  onVoiceMessage?: (audioBlob: Blob) => void;
  /** Whether waiting for assistant response */
  isLoading?: boolean;
  /** Whether voice features are enabled */
  voiceEnabled?: boolean;
}

export function Chat({ 
  messages, 
  onSendMessage, 
  onVoiceMessage,
  isLoading,
  voiceEnabled = true,
}: ChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const [showSeatMap, setShowSeatMap] = useState(false);
  const [selectedSeat, setSelectedSeat] = useState<string | undefined>(undefined);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [voiceModeActive, setVoiceModeActive] = useState(false);

  const { 
    voiceEnabled: voiceHookEnabled, 
    toggleVoice, 
    settings, 
    updateSettings,
    playAudio,
  } = useVoice();

  // Auto-scroll to bottom when messages or loading indicator change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
  }, [messages, isLoading]);

  // Watch for special seat map trigger message (anywhere in list) and only if a seat has not been picked yet
  useEffect(() => {
    const hasTrigger = messages.some(
      (m) => m.role === "assistant" && m.content === "DISPLAY_SEAT_MAP"
    );
    // Show map if trigger exists and seat not chosen yet
    if (hasTrigger && !selectedSeat) {
      setShowSeatMap(true);
    }
  }, [messages, selectedSeat]);

  // Auto-play voice responses
  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (
      latestMessage && 
      latestMessage.role === 'assistant' && 
      latestMessage.audioData && 
      settings.autoPlayResponses &&
      voiceHookEnabled
    ) {
      playAudio(latestMessage.audioData);
    }
  }, [messages, settings.autoPlayResponses, voiceHookEnabled, playAudio]);

  const handleSend = useCallback(() => {
    if (!inputText.trim()) return;
    onSendMessage(inputText, { 
      enableVoice: voiceHookEnabled, 
      enableNavigation: true 
    });
    setInputText("");
  }, [inputText, onSendMessage, voiceHookEnabled]);

  const handleVoiceRecording = useCallback(async (audioBlob: Blob) => {
    if (onVoiceMessage) {
      onVoiceMessage(audioBlob);
    } else {
      // Fallback: convert audio to text and send as regular message
      try {
        const response = await uploadAudio(audioBlob);
        if (response && response.transcript) {
          onSendMessage(response.transcript, { 
            enableVoice: voiceHookEnabled, 
            enableNavigation: true 
          });
        }
      } catch (error) {
        console.error('Failed to process voice message:', error);
      }
    }
  }, [onVoiceMessage, onSendMessage, voiceHookEnabled]);

  const handleSeatSelect = useCallback(
    (seat: string) => {
      setSelectedSeat(seat);
      setShowSeatMap(false);
      onSendMessage(`I would like seat ${seat}`);
    },
    [onSendMessage]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !isComposing) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend, isComposing]
  );

  return (
    <div className="flex flex-col h-full flex-1 bg-white shadow-sm border border-gray-200 border-t-0 rounded-xl">
      <div className="bg-blue-600 text-white h-12 px-4 flex items-center justify-between rounded-t-xl">
        <h2 className="font-semibold text-sm sm:text-base lg:text-lg">
          Customer View
        </h2>
        <div className="flex items-center gap-2">
          {/* Voice toggle */}
          <button
            onClick={toggleVoice}
            className={`
              p-2 rounded-lg transition-all duration-200
              ${voiceHookEnabled 
                ? 'bg-white bg-opacity-20 text-white hover:bg-opacity-30' 
                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
              }
            `}
            title={voiceHookEnabled ? 'Disable voice' : 'Enable voice'}
          >
            {voiceHookEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
          
          {/* Voice settings */}
          <button
            onClick={() => setShowVoiceSettings(true)}
            className="p-2 rounded-lg bg-white bg-opacity-20 text-white hover:bg-opacity-30 transition-all duration-200"
            title="Voice settings"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto min-h-0 md:px-4 pt-4 pb-20">
        {messages.map((msg, idx) => {
          if (msg.content === "DISPLAY_SEAT_MAP") return null; // Skip rendering marker message
          return (
            <div
              key={idx}
              className={`flex mb-5 text-sm ${msg.role === "user" ? "justify-end" : "justify-start"
                }`}
            >
              {msg.role === "user" ? (
                <div className="ml-4 rounded-[16px] rounded-br-[4px] px-4 py-2 md:ml-24 bg-black text-white font-light max-w-[80%]">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <div className="mr-4 rounded-[16px] rounded-bl-[4px] px-4 py-2 md:mr-24 text-zinc-900 bg-[#ECECF1] font-light max-w-[80%]">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {/* Voice playback for assistant messages */}
                  {msg.role === 'assistant' && msg.audioData && voiceHookEnabled && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <VoicePlayback
                        audioData={msg.audioData}
                        agentName={msg.agent || 'Assistant'}
                        showControls={true}
                        showWaveform={false}
                        className="text-xs"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {showSeatMap && (
          <div className="flex justify-start mb-5">
            <div className="mr-4 rounded-[16px] rounded-bl-[4px] md:mr-24">
              <SeatMap
                onSeatSelect={handleSeatSelect}
                selectedSeat={selectedSeat}
              />
            </div>
          </div>
        )}
        {isLoading && (
          <div className="flex mb-5 text-sm justify-start">
            <div className="h-3 w-3 bg-black rounded-full animate-pulse" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Voice mode full interface */}
      <AnimatePresence>
        {voiceModeActive && voiceHookEnabled && (
          <motion.div
            className="p-6 border-t border-gray-200 bg-gray-50"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <VoiceMicrophone
              onAudioRecorded={handleVoiceRecording}
              mode="full"
              className="w-full"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input area */}
      <div className="p-2 md:px-4">
        <div className="flex items-center">
          <div className="flex w-full items-center pb-4 md:pb-1">
            <div className="flex w-full flex-col gap-1.5 rounded-2xl p-2.5 pl-1.5 bg-white border border-stone-200 shadow-sm transition-colors">
              <div className="flex items-end gap-1.5 md:gap-2 pl-4">
                <div className="flex min-w-0 flex-1 flex-col">
                  <textarea
                    id="prompt-textarea"
                    tabIndex={0}
                    dir="auto"
                    rows={2}
                    placeholder={voiceHookEnabled ? "Type a message or use voice..." : "Message..."}
                    className="mb-2 resize-none border-0 focus:outline-none text-sm bg-transparent px-0 pb-6 pt-2"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onCompositionStart={() => setIsComposing(true)}
                    onCompositionEnd={() => setIsComposing(false)}
                  />
                </div>
                
                {/* Voice microphone (compact mode) */}
                {voiceHookEnabled && (
                  <VoiceMicrophone
                    onAudioRecorded={handleVoiceRecording}
                    mode="compact"
                    className="mr-2"
                  />
                )}
                
                {/* Voice mode toggle */}
                {voiceHookEnabled && (
                  <button
                    onClick={() => setVoiceModeActive(!voiceModeActive)}
                    className={`
                      flex h-8 w-8 items-center justify-center rounded-full transition-colors mr-2
                      ${voiceModeActive 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                      }
                    `}
                    title={voiceModeActive ? 'Hide voice interface' : 'Show voice interface'}
                  >
                    <Volume2 size={16} />
                  </button>
                )}
                
                <button
                  disabled={!inputText.trim()}
                  className="flex h-8 w-8 items-end justify-center rounded-full bg-black text-white hover:opacity-70 disabled:bg-gray-300 disabled:text-gray-400 transition-colors focus:outline-none"
                  onClick={handleSend}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="32"
                    height="32"
                    fill="none"
                    viewBox="0 0 32 32"
                    className="icon-2xl"
                  >
                    <path
                      fill="currentColor"
                      fillRule="evenodd"
                      d="M15.192 8.906a1.143 1.143 0 0 1 1.616 0l5.143 5.143a1.143 1.143 0 0 1-1.616 1.616l-3.192-3.192v9.813a1.143 1.143 0 0 1-2.286 0v-9.813l-3.192 3.192a1.143 1.143 0 1 1-1.616-1.616z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Voice Settings Modal */}
      <VoiceSettings
        isOpen={showVoiceSettings}
        onClose={() => setShowVoiceSettings(false)}
        settings={settings}
        onSettingsChange={updateSettings}
      />
    </div>
  );
}
