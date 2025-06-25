"use client";

import { useEffect, useState } from "react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/Chat";
import { HybridVoiceAgent } from "@/components/voice/HybridVoiceAgent";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import { callChatAPI, uploadAudio } from "@/lib/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [currentAgent, setCurrentAgent] = useState<string>("");
  const [guardrails, setGuardrails] = useState<GuardrailCheck[]>([]);
  const [context, setContext] = useState<Record<string, any>>({});
  const [conversationId, setConversationId] = useState<string | null>(null);
  // Loading state while awaiting assistant response
  const [isLoading, setIsLoading] = useState(false);

  // Boot the conversation
  useEffect(() => {
    (async () => {
      const data = await callChatAPI("", conversationId ?? "");
      if (data) {
        setConversationId(data.conversation_id);
        setCurrentAgent(data.current_agent);
        setContext(data.context);
        const initialEvents = (data.events || []).map((e: any) => ({
          ...e,
          timestamp: e.timestamp ?? Date.now(),
        }));
        setEvents(initialEvents);
        setAgents(data.agents || []);
        setGuardrails(data.guardrails || []);
        if (Array.isArray(data.messages)) {
          setMessages(
            data.messages.map((m: any) => ({
              id: Date.now().toString() + Math.random().toString(),
              content: m.content,
              role: "assistant",
              agent: m.agent,
              timestamp: new Date(),
            }))
          );
        }
      } else {
        console.error("Failed to initialize conversation - backend may be down or API key not configured");
      }
    })();
  }, []);

  // Send a user message
  const handleSendMessage = async (
    content: string, 
    options?: { enableVoice?: boolean; enableNavigation?: boolean }
  ) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const data = await callChatAPI(content, conversationId ?? "", options);

    if (data) {
      if (!conversationId) setConversationId(data.conversation_id);
      setCurrentAgent(data.current_agent);
      setContext(data.context);
    } else {
      // Handle API error
      const errorMsg: Message = {
        id: Date.now().toString(),
        content: "Sorry, I'm having trouble connecting to the server. Please check that the backend is running and your API key is configured.",
        role: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setIsLoading(false);
      return;
    }
    if (data.events) {
      const stamped = data.events.map((e: any) => ({
        ...e,
        timestamp: e.timestamp ?? Date.now(),
      }));
      setEvents((prev) => [...prev, ...stamped]);
    }
    if (data.agents) setAgents(data.agents);
    // Update guardrails state
    if (data.guardrails) setGuardrails(data.guardrails);

    if (data.messages) {
      const responses: Message[] = data.messages.map((m: any) => ({
        id: Date.now().toString() + Math.random().toString(),
        content: m.content,
        role: "assistant",
        agent: m.agent,
        timestamp: new Date(),
        audioData: m.audio_base64 || null,
        hasVoice: !!m.audio_base64,
      }));
      setMessages((prev) => [...prev, ...responses]);
    }

    setIsLoading(false);
  };

  // Handle voice message (audio blob)
  const handleVoiceUpload = async (audioBlob: Blob) => {
    try {
      // Convert audio to text first
      const speechResponse = await uploadAudio(audioBlob);
      
      if (speechResponse && speechResponse.transcript) {
        // Send the transcript as a regular message with voice enabled
        await handleSendMessage(speechResponse.transcript, { 
          enableVoice: true, 
          enableNavigation: true 
        });
      } else {
        console.error('Failed to transcribe audio');
        // Could show error message to user here
      }
    } catch (error) {
      console.error('Error processing voice message:', error);
      // Could show error message to user here
    }
  };

  // Handle voice-triggered navigation
  const handleVoiceNavigation = async (messageText: string) => {
    if (!messageText) return;

    // Check for navigation keywords
    const navigationKeywords = [
      'navigate', 'go to', 'show me', 'take me to', 'open', 'visit',
      'inspection', 'application', 'housing', 'landlord', 'requirements'
    ];

    const hasNavigationIntent = navigationKeywords.some(keyword => 
      messageText.toLowerCase().includes(keyword)
    );

    if (hasNavigationIntent) {
      try {
        const response = await fetch('/elevenlabs/navigation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: messageText,
            user_id: conversationId || 'voice_user',
            action: 'navigate'
          }),
        });

        const result = await response.json();
        
        if (result.success) {
          console.log('Navigation completed:', result);
          // Show success notification in chat
          const navMessage: Message = {
            id: Date.now().toString(),
            content: `✅ Navigation completed: ${result.message}`,
            role: "assistant",
            agent: "Navigation Assistant",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, navMessage]);
        } else {
          console.error('Navigation failed:', result.message);
        }
      } catch (error) {
        console.error('Error triggering navigation:', error);
      }
    }
  };

  // Start voice session with navigation
  const handleVoiceSessionStart = async () => {
    try {
      const response = await fetch('/elevenlabs/start-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: conversationId || 'voice_user'
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        console.log('Voice session started:', result);
        // Show success notification in chat
        const navMessage: Message = {
          id: Date.now().toString(),
          content: `🌐 Voice session started! I've opened the Housing Authority website (${result.url}) so I can help you navigate and find information.`,
          role: "assistant",
          agent: "Navigation Assistant",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, navMessage]);
      } else {
        console.error('Failed to start voice session:', result.message);
      }
    } catch (error) {
      console.error('Error starting voice session:', error);
    }
  };

  // Handle hybrid voice agent events
  const handleVoiceMessage = async (response: any) => {
    console.log('Voice agent response:', response);
    
    // Add agent response to chat messages
    if (response.message) {
      const agentMessage: Message = {
        id: Date.now().toString(),
        content: response.message,
        role: "assistant",
        agent: response.current_agent,
        timestamp: new Date(),
        audioData: response.audio_base64,
        hasVoice: !!response.audio_base64,
      };
      setMessages((prev) => [...prev, agentMessage]);
    }

    // Update current agent if handoff occurred
    if (response.handoff_occurred && response.current_agent !== currentAgent) {
      setCurrentAgent(response.current_agent);
      
      // Add handoff notification
      const handoffMessage: Message = {
        id: Date.now().toString() + '_handoff',
        content: `🔄 Conversation handed off to ${response.current_agent}`,
        role: "assistant",
        agent: "System",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, handoffMessage]);
    }

    // Update conversation state
    if (response.conversation_id && response.conversation_id !== conversationId) {
      setConversationId(response.conversation_id);
    }

    // Update events and agents
    if (response.events) {
      const stamped = response.events.map((e: any) => ({
        ...e,
        timestamp: e.timestamp ?? Date.now(),
      }));
      setEvents((prev) => [...prev, ...stamped]);
    }

    if (response.agents) {
      setAgents(response.agents);
    }
  };

  const handleAgentChange = (newAgent: string) => {
    console.log('Agent changed to:', newAgent);
    setCurrentAgent(newAgent);
  };

  const handleVoiceError = (error: any) => {
    console.error('Voice agent error:', error);
    
    // Show error message in chat
    const errorMessage: Message = {
      id: Date.now().toString(),
      content: `❌ Voice Error: ${error.message || 'Something went wrong with the voice system'}`,
      role: "assistant",
      agent: "System",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, errorMessage]);
  };

  return (
    <main className="flex h-screen gap-2 bg-gray-100 p-2 relative">
      <AgentPanel
        agents={agents}
        currentAgent={currentAgent}
        events={events}
        guardrails={guardrails}
        context={context}
      />
      <Chat
        messages={messages}
        onSendMessage={handleSendMessage}
        onVoiceMessage={handleVoiceUpload}
        isLoading={isLoading}
        voiceEnabled={true}
      />
      
      {/* Hybrid Voice Agent (ElevenLabs + OpenAI) */}
      <HybridVoiceAgent
        position="bottom-right"
        theme="light"
        conversationId={conversationId}
        onMessage={handleVoiceMessage}
        onAgentChange={handleAgentChange}
        onError={handleVoiceError}
        className="z-50"
      />
    </main>
  );
}
