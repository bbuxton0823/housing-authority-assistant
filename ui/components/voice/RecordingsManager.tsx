"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Play, 
  Pause, 
  Download, 
  Trash2, 
  RefreshCw, 
  Search,
  Calendar,
  Clock,
  User,
  MessageSquare,
  Volume2,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { VoicePlayback } from './VoicePlayback';
import { listRecordings, getRecording, deleteRecording } from '../../lib/api';
import type { RecordingMetadata } from '../../lib/types';

interface RecordingsManagerProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId?: string;
  userId?: string;
  className?: string;
}

interface RecordingWithAudio extends RecordingMetadata {
  audio_base64?: string;
  isPlaying?: boolean;
}

export function RecordingsManager({
  isOpen,
  onClose,
  conversationId,
  userId,
  className = '',
}: RecordingsManagerProps) {
  const [recordings, setRecordings] = useState<RecordingWithAudio[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecording, setSelectedRecording] = useState<RecordingWithAudio | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const recordingsPerPage = 10;

  // Load recordings
  const loadRecordings = async () => {
    if (!isOpen) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await listRecordings(conversationId, userId, 100);
      if (Array.isArray(data)) {
        setRecordings(data);
        setTotalPages(Math.ceil(data.length / recordingsPerPage));
      } else {
        setRecordings([]);
      }
    } catch (err) {
      setError('Failed to load recordings');
      console.error('Error loading recordings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecordings();
  }, [isOpen, conversationId, userId]);

  // Filter recordings based on search term
  const filteredRecordings = recordings.filter(recording => 
    recording.transcript?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recording.agent_response?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recording.recording_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Paginate recordings
  const paginatedRecordings = filteredRecordings.slice(
    (currentPage - 1) * recordingsPerPage,
    currentPage * recordingsPerPage
  );

  // Load audio for a recording
  const loadRecordingAudio = async (recording: RecordingWithAudio) => {
    try {
      const data = await getRecording(recording.recording_id);
      if (data && data.audio_base64) {
        const updatedRecording = {
          ...recording,
          audio_base64: data.audio_base64,
        };
        setSelectedRecording(updatedRecording);
        
        // Update in recordings list
        setRecordings(prev => 
          prev.map(r => 
            r.recording_id === recording.recording_id 
              ? updatedRecording 
              : r
          )
        );
      }
    } catch (err) {
      console.error('Error loading recording audio:', err);
      setError('Failed to load recording audio');
    }
  };

  // Delete recording
  const handleDeleteRecording = async (recordingId: string) => {
    if (!confirm('Are you sure you want to delete this recording?')) return;
    
    try {
      await deleteRecording(recordingId);
      setRecordings(prev => prev.filter(r => r.recording_id !== recordingId));
      if (selectedRecording?.recording_id === recordingId) {
        setSelectedRecording(null);
      }
    } catch (err) {
      console.error('Error deleting recording:', err);
      setError('Failed to delete recording');
    }
  };

  // Format duration
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Format file size
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '--';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className={`bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden ${className}`}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Volume2 className="text-blue-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-900">Voice Recordings</h2>
            {conversationId && (
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                Conversation: {conversationId.slice(0, 8)}...
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadRecordings}
              disabled={loading}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex h-[calc(90vh-120px)]">
          {/* Recordings List */}
          <div className="w-1/2 border-r border-gray-200 flex flex-col">
            {/* Search and filters */}
            <div className="p-4 border-b border-gray-200">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="text"
                  placeholder="Search recordings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
                <span>{filteredRecordings.length} recordings</span>
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <span>{currentPage} / {totalPages}</span>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Recordings list */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <RefreshCw className="animate-spin" size={24} />
                  <span className="ml-2">Loading recordings...</span>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-32 text-red-600">
                  <span>{error}</span>
                </div>
              ) : paginatedRecordings.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <span>No recordings found</span>
                </div>
              ) : (
                <div className="space-y-2 p-4">
                  {paginatedRecordings.map((recording) => (
                    <motion.div
                      key={recording.recording_id}
                      className={`
                        p-4 border rounded-lg cursor-pointer transition-all
                        ${selectedRecording?.recording_id === recording.recording_id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }
                      `}
                      onClick={() => loadRecordingAudio(recording)}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <Calendar size={14} className="text-gray-400" />
                            <span className="text-sm text-gray-600">
                              {formatTimestamp(recording.timestamp)}
                            </span>
                            {recording.duration && (
                              <>
                                <Clock size={14} className="text-gray-400" />
                                <span className="text-sm text-gray-600">
                                  {formatDuration(recording.duration)}
                                </span>
                              </>
                            )}
                          </div>
                          
                          {recording.transcript && (
                            <div className="mb-2">
                              <div className="flex items-center gap-1 mb-1">
                                <User size={12} className="text-blue-500" />
                                <span className="text-xs font-medium text-blue-600">User:</span>
                              </div>
                              <p className="text-sm text-gray-800 truncate">
                                "{recording.transcript}"
                              </p>
                            </div>
                          )}
                          
                          {recording.agent_response && (
                            <div>
                              <div className="flex items-center gap-1 mb-1">
                                <MessageSquare size={12} className="text-green-500" />
                                <span className="text-xs font-medium text-green-600">Agent:</span>
                              </div>
                              <p className="text-sm text-gray-800 truncate">
                                "{recording.agent_response}"
                              </p>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>{formatFileSize(recording.file_size)}</span>
                            <span>{recording.file_format?.toUpperCase()}</span>
                            {recording.confidence_score && (
                              <span>Confidence: {Math.round(recording.confidence_score * 100)}%</span>
                            )}
                          </div>
                        </div>
                        
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteRecording(recording.recording_id);
                          }}
                          className="p-1 text-red-500 hover:bg-red-100 rounded transition-colors"
                          title="Delete recording"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recording Details and Player */}
          <div className="w-1/2 flex flex-col">
            {selectedRecording ? (
              <div className="flex-1 p-6">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Recording Details
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">ID:</span>
                      <span className="ml-2 font-mono text-xs">
                        {selectedRecording.recording_id}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Timestamp:</span>
                      <span className="ml-2">
                        {formatTimestamp(selectedRecording.timestamp)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <span className="ml-2">
                        {formatDuration(selectedRecording.duration)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Size:</span>
                      <span className="ml-2">
                        {formatFileSize(selectedRecording.file_size)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Format:</span>
                      <span className="ml-2">
                        {selectedRecording.file_format?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Language:</span>
                      <span className="ml-2">
                        {selectedRecording.language}
                      </span>
                    </div>
                  </div>
                </div>

                {selectedRecording.transcript && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-900 mb-2">Transcript</h4>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-800">"{selectedRecording.transcript}"</p>
                    </div>
                  </div>
                )}

                {selectedRecording.agent_response && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-900 mb-2">Agent Response</h4>
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-800">"{selectedRecording.agent_response}"</p>
                    </div>
                  </div>
                )}

                {selectedRecording.audio_base64 && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-900 mb-2">Audio Playback</h4>
                    <VoicePlayback
                      audioData={selectedRecording.audio_base64}
                      agentName="Recording"
                      showControls={true}
                      showWaveform={true}
                    />
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = `/recordings/${selectedRecording.recording_id}/download`;
                      link.download = `recording_${selectedRecording.recording_id}.${selectedRecording.file_format}`;
                      link.click();
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download size={16} />
                    Download
                  </button>
                  
                  <button
                    onClick={() => handleDeleteRecording(selectedRecording.recording_id)}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Volume2 size={48} className="mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Select a recording to view details</p>
                  <p className="text-sm">Click on any recording from the list to play and manage it</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}