// Helper to call the server
export async function callChatAPI(
  message: string, 
  conversationId: string, 
  options?: {
    enableVoice?: boolean;
    enableNavigation?: boolean;
    userId?: string;
  }
) {
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        conversation_id: conversationId, 
        message,
        enable_voice: options?.enableVoice || false,
        enable_navigation: options?.enableNavigation || false,
        user_id: options?.userId,
      }),
    });
    if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error sending message:", err);
    return null;
  }
}

// Helper to synthesize voice
export async function synthesizeVoice(
  text: string,
  agent: string = "Triage Agent",
  returnBase64: boolean = true
) {
  try {
    const params = new URLSearchParams({
      text,
      agent,
      return_base64: returnBase64.toString(),
    });
    
    const res = await fetch(`/voice/synthesize?${params}`, {
      method: "POST",
    });
    
    if (!res.ok) throw new Error(`Voice API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error synthesizing voice:", err);
    return null;
  }
}

// Helper to get voice info
export async function getVoiceInfo() {
  try {
    const res = await fetch("/voice/info");
    if (!res.ok) throw new Error(`Voice info API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting voice info:", err);
    return null;
  }
}

// Helper to upload audio for speech-to-text
export async function uploadAudio(audioBlob: Blob) {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    const res = await fetch("/speech-to-text", {
      method: "POST",
      body: formData,
    });
    
    if (!res.ok) throw new Error(`Speech-to-text API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error uploading audio:", err);
    return null;
  }
}

// Helper to save recording to backend
export async function saveRecording(
  audioBlob: Blob,
  metadata: {
    conversationId?: string;
    userId?: string;
    transcript?: string;
    agentResponse?: string;
    duration?: number;
    confidenceScore?: number;
    language?: string;
  }
) {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    if (metadata.conversationId) formData.append('conversation_id', metadata.conversationId);
    if (metadata.userId) formData.append('user_id', metadata.userId);
    if (metadata.transcript) formData.append('transcript', metadata.transcript);
    if (metadata.agentResponse) formData.append('agent_response', metadata.agentResponse);
    if (metadata.duration) formData.append('duration', metadata.duration.toString());
    if (metadata.confidenceScore) formData.append('confidence_score', metadata.confidenceScore.toString());
    if (metadata.language) formData.append('language', metadata.language);
    
    const res = await fetch("/recordings/save", {
      method: "POST",
      body: formData,
    });
    
    if (!res.ok) throw new Error(`Recording save API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error saving recording:", err);
    return null;
  }
}

// Helper to list recordings
export async function listRecordings(
  conversationId?: string,
  userId?: string,
  limit?: number
) {
  try {
    const params = new URLSearchParams();
    if (conversationId) params.append('conversation_id', conversationId);
    if (userId) params.append('user_id', userId);
    if (limit) params.append('limit', limit.toString());
    
    const res = await fetch(`/recordings?${params}`);
    if (!res.ok) throw new Error(`Recordings list API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error listing recordings:", err);
    return [];
  }
}

// Helper to get a specific recording
export async function getRecording(recordingId: string) {
  try {
    const res = await fetch(`/recordings/${recordingId}`);
    if (!res.ok) throw new Error(`Recording get API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting recording:", err);
    return null;
  }
}

// Helper to delete a recording
export async function deleteRecording(recordingId: string) {
  try {
    const res = await fetch(`/recordings/${recordingId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Recording delete API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error deleting recording:", err);
    return null;
  }
}

// =========================
// ElevenLabs Conversational AI API
// =========================

// Helper to get ElevenLabs configuration
export async function getElevenLabsConfig() {
  try {
    const res = await fetch("/elevenlabs/config");
    if (!res.ok) throw new Error(`ElevenLabs config API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting ElevenLabs config:", err);
    return null;
  }
}

// Helper to get signed URL for ElevenLabs agent
export async function getElevenLabsSignedUrl(agentId: string) {
  try {
    const params = new URLSearchParams({ agent_id: agentId });
    const res = await fetch(`/elevenlabs/signed-url?${params}`);
    if (!res.ok) throw new Error(`ElevenLabs signed URL API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting ElevenLabs signed URL:", err);
    return null;
  }
}
