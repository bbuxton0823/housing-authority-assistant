"use client";

import { useEffect, useState } from "react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/Chat";
import { TravelSearch } from "@/components/travel-search";
import { WeatherWidget } from "@/components/weather-widget";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import { callChatAPI } from "@/lib/api";

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
  
  // Travel-specific state
  const [activeTab, setActiveTab] = useState<'chat' | 'search' | 'weather'>('chat');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [weatherData, setWeatherData] = useState<any>(null);

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
  const handleSendMessage = async (content: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const data = await callChatAPI(content, conversationId ?? "");

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
      }));
      setMessages((prev) => [...prev, ...responses]);
    }

    setIsLoading(false);
  };

  return (
    <main className="flex h-screen gap-2 bg-gray-100 p-2">
      <AgentPanel
        agents={agents}
        currentAgent={currentAgent}
        events={events}
        guardrails={guardrails}
        context={context}
      />
      
      <div className="flex-1 flex flex-col">
        {/* Travel App Header */}
        <div className="bg-white rounded-lg p-4 mb-2 shadow-sm">
          <h1 className="text-2xl font-bold text-blue-600">AI Travel Assistant</h1>
          <p className="text-gray-600">Your intelligent travel companion for flights, trains, and more</p>
          
          {/* Tab Navigation */}
          <div className="flex space-x-4 mt-4 border-b">
            <button
              onClick={() => setActiveTab('chat')}
              className={`pb-2 px-1 ${activeTab === 'chat' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
            >
              Chat Assistant
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`pb-2 px-1 ${activeTab === 'search' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
            >
              Search Travel
            </button>
            <button
              onClick={() => setActiveTab('weather')}
              className={`pb-2 px-1 ${activeTab === 'weather' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
            >
              Weather
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1">
          {activeTab === 'chat' && (
            <Chat
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          )}
          
          {activeTab === 'search' && (
            <TravelSearch
              onSearchResults={setSearchResults}
              searchResults={searchResults}
            />
          )}
          
          {activeTab === 'weather' && (
            <WeatherWidget
              weatherData={weatherData}
              onWeatherUpdate={setWeatherData}
            />
          )}
        </div>
      </div>
    </main>
  );
}
