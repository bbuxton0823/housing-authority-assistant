"use client";

import { useState, useEffect, useCallback } from 'react';
import { getElevenLabsConfig, getElevenLabsSignedUrl } from '../api';

interface ElevenLabsConfig {
  has_api_key: boolean;
  default_agent_id?: string;
  public_agent: boolean;
}

interface UseElevenLabsVoiceOptions {
  agentId?: string;
  autoLoadSignedUrl?: boolean;
}

interface UseElevenLabsVoiceReturn {
  config: ElevenLabsConfig | null;
  agentId: string | null;
  signedUrl: string | null;
  isLoading: boolean;
  error: string | null;
  isConfigured: boolean;
  isPublicAgent: boolean;
  loadSignedUrl: (agentId?: string) => Promise<string | null>;
  refreshConfig: () => Promise<void>;
}

export function useElevenLabsVoice(options: UseElevenLabsVoiceOptions = {}): UseElevenLabsVoiceReturn {
  const [config, setConfig] = useState<ElevenLabsConfig | null>(null);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine which agent ID to use
  const agentId = options.agentId || config?.default_agent_id || null;
  const isConfigured = !!(config?.has_api_key && agentId);
  const isPublicAgent = config?.public_agent || false;

  // Load ElevenLabs configuration
  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const configData = await getElevenLabsConfig();
      if (configData && !configData.error) {
        setConfig(configData);
      } else {
        setError(configData?.error || 'Failed to load ElevenLabs configuration');
      }
    } catch (err) {
      setError('Failed to load ElevenLabs configuration');
      console.error('Error loading ElevenLabs config:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load signed URL for private agents
  const loadSignedUrl = useCallback(async (targetAgentId?: string): Promise<string | null> => {
    const useAgentId = targetAgentId || agentId;
    
    if (!useAgentId) {
      setError('No agent ID provided');
      return null;
    }

    if (isPublicAgent) {
      // For public agents, we don't need a signed URL
      return null;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await getElevenLabsSignedUrl(useAgentId);
      if (response && response.signed_url) {
        setSignedUrl(response.signed_url);
        return response.signed_url;
      } else {
        const errorMsg = response?.error || 'Failed to get signed URL';
        setError(errorMsg);
        return null;
      }
    } catch (err) {
      const errorMsg = 'Failed to get signed URL';
      setError(errorMsg);
      console.error('Error loading signed URL:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [agentId, isPublicAgent]);

  // Refresh configuration
  const refreshConfig = useCallback(async () => {
    await loadConfig();
  }, [loadConfig]);

  // Load config on mount
  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // Auto-load signed URL if configured
  useEffect(() => {
    if (
      options.autoLoadSignedUrl && 
      isConfigured && 
      !isPublicAgent && 
      !signedUrl && 
      !isLoading
    ) {
      loadSignedUrl();
    }
  }, [options.autoLoadSignedUrl, isConfigured, isPublicAgent, signedUrl, isLoading, loadSignedUrl]);

  return {
    config,
    agentId,
    signedUrl,
    isLoading,
    error,
    isConfigured,
    isPublicAgent,
    loadSignedUrl,
    refreshConfig,
  };
}