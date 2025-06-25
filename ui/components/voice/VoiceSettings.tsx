"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Settings, 
  Volume2, 
  Mic, 
  Headphones, 
  Zap, 
  Clock,
  User,
  X,
  ChevronDown,
  ChevronUp,
  TestTube,
  Database,
  Archive
} from 'lucide-react';
import { VoiceMode } from '@/lib/hooks/useVoice';
import { RecordingsManager } from './RecordingsManager';

interface VoiceSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  settings: {
    mode: VoiceMode;
    volume: number;
    enableVoiceActivity: boolean;
    selectedVoice: string;
    autoPlayResponses: boolean;
    noiseSuppressionLevel: number;
    saveRecordings: boolean;
    conversationId?: string;
    userId?: string;
  };
  onSettingsChange: (settings: any) => void;
  className?: string;
}

const VOICE_OPTIONS = [
  { id: 'Rachel', name: 'Rachel', description: 'Professional, warm female voice', preview: 'preview_rachel.mp3' },
  { id: 'Daniel', name: 'Daniel', description: 'Clear, confident male voice', preview: 'preview_daniel.mp3' },
  { id: 'Bella', name: 'Bella', description: 'Friendly, approachable female voice', preview: 'preview_bella.mp3' },
  { id: 'Adam', name: 'Adam', description: 'Deep, authoritative male voice', preview: 'preview_adam.mp3' },
  { id: 'Natasha', name: 'Natasha', description: 'Sophisticated female voice', preview: 'preview_natasha.mp3' },
];

const AGENT_VOICE_ASSIGNMENTS = {
  'Triage Agent': { primary: 'Rachel', secondary: 'Bella' },
  'Inspection Agent': { primary: 'Daniel', secondary: 'Adam' },
  'HPS Agent': { primary: 'Bella', secondary: 'Rachel' },
  'Landlord Services Agent': { primary: 'Adam', secondary: 'Daniel' },
  'General Information Agent': { primary: 'Natasha', secondary: 'Rachel' },
};

export function VoiceSettings({
  isOpen,
  onClose,
  settings,
  onSettingsChange,
  className = '',
}: VoiceSettingsProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'voices' | 'recordings' | 'advanced'>('general');
  const [testingVoice, setTestingVoice] = useState<string | null>(null);
  const [showRecordingsManager, setShowRecordingsManager] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    onSettingsChange({ [key]: value });
  };

  const testVoice = async (voiceId: string) => {
    setTestingVoice(voiceId);
    
    try {
      // Call the voice synthesis API to test the voice
      const response = await fetch(`/voice/synthesize?text=Hello, this is ${voiceId} voice from the Housing Authority assistant.&agent=Triage Agent&return_base64=true`);
      const data = await response.json();
      
      if (data.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audio.play();
      }
    } catch (error) {
      console.error('Failed to test voice:', error);
    } finally {
      setTimeout(() => setTestingVoice(null), 2000);
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
        className={`bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden ${className}`}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Settings className="text-blue-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-900">Voice Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {[
            { id: 'general' as const, label: 'General', icon: Volume2 },
            { id: 'voices' as const, label: 'Voices', icon: User },
            { id: 'recordings' as const, label: 'Recordings', icon: Database },
            { id: 'advanced' as const, label: 'Advanced', icon: Settings },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-6 py-3 transition-colors
                ${activeTab === tab.id 
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }
              `}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'general' && (
            <div className="space-y-6">
              {/* Voice Mode */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Recording Mode
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'push-to-talk' as VoiceMode, label: 'Push to Talk', desc: 'Hold button to record' },
                    { value: 'continuous' as VoiceMode, label: 'Continuous', desc: 'Always listening' },
                  ].map(mode => (
                    <button
                      key={mode.value}
                      onClick={() => handleSettingChange('mode', mode.value)}
                      className={`
                        p-4 border-2 rounded-lg text-left transition-all
                        ${settings.mode === mode.value 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="font-medium text-gray-900">{mode.label}</div>
                      <div className="text-sm text-gray-500">{mode.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Volume */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Playback Volume
                </label>
                <div className="flex items-center gap-4">
                  <Volume2 size={16} className="text-gray-500" />
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.volume}
                    onChange={(e) => handleSettingChange('volume', Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 w-12">{settings.volume}%</span>
                </div>
              </div>

              {/* Auto-play responses */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">Auto-play Responses</div>
                  <div className="text-sm text-gray-500">Automatically play agent voice responses</div>
                </div>
                <button
                  onClick={() => handleSettingChange('autoPlayResponses', !settings.autoPlayResponses)}
                  className={`
                    relative w-12 h-6 rounded-full transition-colors
                    ${settings.autoPlayResponses ? 'bg-blue-600' : 'bg-gray-300'}
                  `}
                >
                  <motion.div
                    className="w-5 h-5 bg-white rounded-full shadow-sm"
                    animate={{ x: settings.autoPlayResponses ? 26 : 2, y: 2 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                </button>
              </div>

              {/* Save Recordings */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">Save Recordings</div>
                  <div className="text-sm text-gray-500">Automatically save all voice recordings to backend</div>
                </div>
                <button
                  onClick={() => handleSettingChange('saveRecordings', !settings.saveRecordings)}
                  className={`
                    relative w-12 h-6 rounded-full transition-colors
                    ${settings.saveRecordings ? 'bg-blue-600' : 'bg-gray-300'}
                  `}
                >
                  <motion.div
                    className="w-5 h-5 bg-white rounded-full shadow-sm"
                    animate={{ x: settings.saveRecordings ? 26 : 2, y: 2 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                </button>
              </div>

              {/* Voice Activity Detection */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">Voice Activity Detection</div>
                  <div className="text-sm text-gray-500">Automatically detect when you're speaking</div>
                </div>
                <button
                  onClick={() => handleSettingChange('enableVoiceActivity', !settings.enableVoiceActivity)}
                  className={`
                    relative w-12 h-6 rounded-full transition-colors
                    ${settings.enableVoiceActivity ? 'bg-blue-600' : 'bg-gray-300'}
                  `}
                >
                  <motion.div
                    className="w-5 h-5 bg-white rounded-full shadow-sm"
                    animate={{ x: settings.enableVoiceActivity ? 26 : 2, y: 2 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                </button>
              </div>
            </div>
          )}

          {activeTab === 'voices' && (
            <div className="space-y-6">
              {/* Global Voice Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Default Voice
                </label>
                <div className="space-y-3">
                  {VOICE_OPTIONS.map(voice => (
                    <div
                      key={voice.id}
                      className={`
                        p-4 border rounded-lg cursor-pointer transition-all
                        ${settings.selectedVoice === voice.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                      onClick={() => handleSettingChange('selectedVoice', voice.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{voice.name}</div>
                          <div className="text-sm text-gray-500">{voice.description}</div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            testVoice(voice.id);
                          }}
                          disabled={testingVoice === voice.id}
                          className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                        >
                          {testingVoice === voice.id ? (
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                            >
                              <TestTube size={16} />
                            </motion.div>
                          ) : (
                            <TestTube size={16} />
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent-specific Voice Assignments */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Agent Voice Assignments
                </label>
                <div className="space-y-3">
                  {Object.entries(AGENT_VOICE_ASSIGNMENTS).map(([agent, voices]) => (
                    <div key={agent} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{agent}</div>
                          <div className="text-sm text-gray-500">
                            Primary: {voices.primary} • Secondary: {voices.secondary}
                          </div>
                        </div>
                        <button className="text-blue-600 hover:text-blue-800 text-sm">
                          Customize
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'recordings' && (
            <div className="space-y-6">
              {/* Recording Storage Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Storage Settings
                </label>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">Auto-Save Recordings</div>
                      <div className="text-sm text-gray-500">Automatically save all voice recordings to the backend</div>
                    </div>
                    <button
                      onClick={() => handleSettingChange('saveRecordings', !settings.saveRecordings)}
                      className={`
                        relative w-12 h-6 rounded-full transition-colors
                        ${settings.saveRecordings ? 'bg-blue-600' : 'bg-gray-300'}
                      `}
                    >
                      <motion.div
                        className="w-5 h-5 bg-white rounded-full shadow-sm"
                        animate={{ x: settings.saveRecordings ? 26 : 2, y: 2 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                      />
                    </button>
                  </div>
                  
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Archive className="text-blue-600" size={16} />
                      <div className="font-medium text-blue-900">Recording Storage</div>
                    </div>
                    <div className="text-sm text-blue-800">
                      <p className="mb-2">When enabled, recordings are automatically saved with:</p>
                      <ul className="list-disc list-inside space-y-1 ml-4">
                        <li>Audio file (WebM format)</li>
                        <li>Transcript (if available)</li>
                        <li>Agent response (if available)</li>
                        <li>Conversation metadata</li>
                        <li>Timestamp and duration</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recording Quality Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Recording Quality
                </label>
                <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="high">High Quality (44.1kHz, Stereo)</option>
                  <option value="medium">Medium Quality (22kHz, Mono)</option>
                  <option value="low">Low Quality (16kHz, Mono) - Smaller files</option>
                </select>
                <div className="text-sm text-gray-500 mt-1">
                  Higher quality recordings use more storage space
                </div>
              </div>

              {/* Storage Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Storage Information
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">--</div>
                    <div className="text-sm text-gray-500">Total Recordings</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">-- MB</div>
                    <div className="text-sm text-gray-500">Storage Used</div>
                  </div>
                </div>
              </div>

              {/* Privacy Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Privacy & Retention
                </label>
                <div className="space-y-3">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="font-medium text-gray-900 mb-2">Auto-Delete Old Recordings</div>
                    <select className="w-full p-2 border border-gray-300 rounded">
                      <option value="never">Never delete</option>
                      <option value="30">Delete after 30 days</option>
                      <option value="90">Delete after 90 days</option>
                      <option value="365">Delete after 1 year</option>
                    </select>
                  </div>
                  
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
                      <div className="font-medium text-yellow-800">Privacy Notice</div>
                    </div>
                    <div className="text-sm text-yellow-700">
                      Voice recordings may contain sensitive information. Ensure proper security measures are in place for stored recordings.
                    </div>
                  </div>
                </div>
              </div>

              {/* Recording Management */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Recording Management
                </label>
                <div className="flex gap-3">
                  <button 
                    onClick={() => setShowRecordingsManager(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    View All Recordings
                  </button>
                  <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                    Export All Recordings
                  </button>
                  <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                    Clear All Recordings
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="space-y-6">
              {/* Noise Suppression */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Noise Suppression Level
                </label>
                <div className="flex items-center gap-4">
                  <Mic size={16} className="text-gray-500" />
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={settings.noiseSuppressionLevel}
                    onChange={(e) => handleSettingChange('noiseSuppressionLevel', Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 w-12">
                    {Math.round(settings.noiseSuppressionLevel * 100)}%
                  </span>
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  Higher values reduce background noise but may affect voice quality
                </div>
              </div>

              {/* Audio Quality Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Audio Quality
                </label>
                <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="high">High Quality (44.1kHz)</option>
                  <option value="medium">Medium Quality (22kHz)</option>
                  <option value="low">Low Quality (16kHz) - Faster</option>
                </select>
              </div>

              {/* Latency Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Response Latency
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'low', label: 'Low Latency', desc: 'Faster responses' },
                    { value: 'balanced', label: 'Balanced', desc: 'Good quality & speed' },
                    { value: 'quality', label: 'High Quality', desc: 'Better audio quality' },
                  ].map(option => (
                    <button
                      key={option.value}
                      className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors text-left"
                    >
                      <div className="font-medium text-gray-900 text-sm">{option.label}</div>
                      <div className="text-xs text-gray-500">{option.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Experimental Features */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Experimental Features
                </label>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">Real-time Transcription</div>
                      <div className="text-sm text-gray-500">Show live transcription while speaking</div>
                    </div>
                    <button className="relative w-12 h-6 bg-gray-300 rounded-full">
                      <div className="w-5 h-5 bg-white rounded-full shadow-sm" style={{ transform: 'translate(2px, 2px)' }} />
                    </button>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">Voice Emotion Detection</div>
                      <div className="text-sm text-gray-500">Adjust agent responses based on tone</div>
                    </div>
                    <button className="relative w-12 h-6 bg-gray-300 rounded-full">
                      <div className="w-5 h-5 bg-white rounded-full shadow-sm" style={{ transform: 'translate(2px, 2px)' }} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            Voice powered by ElevenLabs
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Save Settings
            </button>
          </div>
        </div>
      </motion.div>
      
      {/* Recordings Manager Modal */}
      <RecordingsManager
        isOpen={showRecordingsManager}
        onClose={() => setShowRecordingsManager(false)}
        conversationId={settings.conversationId}
        userId={settings.userId}
      />
    </motion.div>
  );
}