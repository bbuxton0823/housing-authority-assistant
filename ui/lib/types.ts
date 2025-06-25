export interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  agent?: string
  timestamp: Date
  audioData?: string | null  // Base64 audio data
  audioBlob?: Blob | null    // Audio blob for playback
  hasVoice?: boolean         // Whether this message has voice
}

export interface Agent {
  name: string
  description: string
  handoffs: string[]
  tools: string[]
  /** List of input guardrail identifiers for this agent */
  input_guardrails: string[]
}

export type EventType = "message" | "handoff" | "tool_call" | "tool_output" | "context_update"

export interface AgentEvent {
  id: string
  type: EventType
  agent: string
  content: string
  timestamp: Date
  metadata?: {
    source_agent?: string
    target_agent?: string
    tool_name?: string
    tool_args?: Record<string, any>
    tool_result?: any
    context_key?: string
    context_value?: any
    changes?: Record<string, any>
  }
}

export interface GuardrailCheck {
  id: string
  name: string
  input: string
  reasoning: string
  passed: boolean
  timestamp: Date
}

export interface RecordingMetadata {
  recording_id: string
  conversation_id?: string
  user_id?: string
  timestamp: string
  duration?: number
  file_size?: number
  transcript?: string
  agent_response?: string
  confidence_score?: number
  language?: string
  file_format: string
}

export interface RecordingResponse {
  recording_id: string
  status: string
  message: string
  metadata?: RecordingMetadata
}

