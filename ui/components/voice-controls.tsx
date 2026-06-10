"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { transcribeSpeech, synthesizeVoice, playAudioBase64, getVoiceStatus } from "@/lib/api";

interface VoiceControlsProps {
  onTranscription: (text: string) => void;
  lastAssistantMessage?: string;
  currentAgent?: string;
  language?: string;
  disabled?: boolean;
}

type RecordingState = "idle" | "recording" | "processing";

export function VoiceControls({
  onTranscription,
  lastAssistantMessage,
  currentAgent = "triage",
  language = "english",
  disabled = false,
}: VoiceControlsProps) {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [voiceEnabled, setVoiceEnabled] = useState<boolean | null>(null);
  const [autoPlayResponses, setAutoPlayResponses] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Check voice service status on mount
  useEffect(() => {
    getVoiceStatus().then((status) => {
      if (status) {
        setVoiceEnabled(status.stt_enabled);
      }
    });
  }, []);

  // Auto-play assistant responses if enabled
  useEffect(() => {
    if (autoPlayResponses && lastAssistantMessage) {
      playAssistantResponse(lastAssistantMessage);
    }
  }, [lastAssistantMessage, autoPlayResponses]);

  const playAssistantResponse = async (text: string) => {
    const response = await synthesizeVoice(text, currentAgent, language);
    if (response?.success && response.audio_base64) {
      playAudioBase64(response.audio_base64);
    }
  };

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4",
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setRecordingState("processing");

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType
        });

        // Transcribe the audio
        const result = await transcribeSpeech(audioBlob, language);

        if (result?.success && result.text) {
          onTranscription(result.text);
        } else if (result?.error) {
          setError(result.error);
        } else {
          setError("Failed to transcribe audio");
        }

        setRecordingState("idle");

        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setRecordingState("recording");
    } catch (err) {
      console.error("Error starting recording:", err);
      setError("Could not access microphone. Please check permissions.");
      setRecordingState("idle");
    }
  }, [language, onTranscription]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, [recordingState]);

  const toggleRecording = useCallback(() => {
    if (recordingState === "idle") {
      startRecording();
    } else if (recordingState === "recording") {
      stopRecording();
    }
  }, [recordingState, startRecording, stopRecording]);

  // Keyboard shortcut: hold space to record
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body && recordingState === "idle" && !disabled) {
        e.preventDefault();
        startRecording();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space" && recordingState === "recording") {
        e.preventDefault();
        stopRecording();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [recordingState, disabled, startRecording, stopRecording]);

  if (voiceEnabled === false) {
    return null; // Don't show voice controls if service is unavailable
  }

  return (
    <div className="flex items-center gap-2">
      {/* Recording button */}
      <button
        onClick={toggleRecording}
        disabled={disabled || recordingState === "processing"}
        className={`
          flex items-center justify-center w-10 h-10 rounded-full transition-all duration-200
          ${recordingState === "recording"
            ? "bg-red-500 hover:bg-red-600 animate-pulse"
            : recordingState === "processing"
            ? "bg-gray-400 cursor-wait"
            : "bg-blue-600 hover:bg-blue-700"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
        `}
        title={
          recordingState === "recording"
            ? "Click to stop recording"
            : recordingState === "processing"
            ? "Processing..."
            : "Click to start recording (or hold Space)"
        }
      >
        {recordingState === "processing" ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : recordingState === "recording" ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        )}
      </button>

      {/* Auto-play toggle */}
      <button
        onClick={() => setAutoPlayResponses(!autoPlayResponses)}
        className={`
          flex items-center justify-center w-8 h-8 rounded-full transition-colors
          ${autoPlayResponses ? "bg-green-500 text-white" : "bg-gray-200 text-gray-600"}
          hover:opacity-80 focus:outline-none
        `}
        title={autoPlayResponses ? "Disable voice responses" : "Enable voice responses"}
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          {autoPlayResponses ? (
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
          ) : (
            <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
          )}
        </svg>
      </button>

      {/* Recording indicator */}
      {recordingState === "recording" && (
        <span className="text-xs text-red-600 animate-pulse">Recording...</span>
      )}
      {recordingState === "processing" && (
        <span className="text-xs text-gray-500">Processing...</span>
      )}

      {/* Error message */}
      {error && (
        <span className="text-xs text-red-600">{error}</span>
      )}
    </div>
  );
}
