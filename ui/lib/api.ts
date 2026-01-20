const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Helper to call the housing authority chat API
export async function callChatAPI(message: string, conversationId: string | null) {
  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        conversation_id: conversationId || undefined
      }),
    });
    if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Error sending message:", err);
    return null;
  }
}

// Travel-specific API functions
export async function searchFlights(searchParams: {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  passengers: number;
  flight_class: string;
}) {
  try {
    const res = await fetch(`${API_BASE_URL}/search/flights`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(searchParams),
    });
    if (!res.ok) throw new Error(`Flight search error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error searching flights:", err);
    return null;
  }
}

export async function searchTrains(searchParams: {
  origin: string;
  destination: string;
  departure_date: string;
  passengers: number;
  train_class: string;
}) {
  try {
    const res = await fetch(`${API_BASE_URL}/search/trains`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(searchParams),
    });
    if (!res.ok) throw new Error(`Train search error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error searching trains:", err);
    return null;
  }
}

export async function getWeather(location: string, date?: string) {
  try {
    const url = `${API_BASE_URL}/weather/${encodeURIComponent(location)}${date ? `?date=${date}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Weather API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting weather:", err);
    return null;
  }
}

export async function createBooking(bookingData: {
  booking_type: string;
  selection_id: string;
  passenger_info: any;
  payment_method: string;
}) {
  try {
    const res = await fetch(`${API_BASE_URL}/booking`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bookingData),
    });
    if (!res.ok) throw new Error(`Booking API error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error creating booking:", err);
    return null;
  }
}

// Voice API functions

export interface VoiceSynthesizeResponse {
  audio_base64: string | null;
  error: string | null;
  success: boolean;
}

export interface VoiceTranscribeResponse {
  text: string;
  language: string;
  error: string | null;
  success: boolean;
}

export interface VoiceStatusResponse {
  tts_enabled: boolean;
  stt_enabled: boolean;
  supported_languages: string[];
}

export async function synthesizeVoice(
  text: string,
  agent: string = "triage",
  language: string = "english"
): Promise<VoiceSynthesizeResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/voice/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, agent, language }),
    });
    if (!res.ok) throw new Error(`Voice synthesis error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error synthesizing voice:", err);
    return null;
  }
}

export async function transcribeSpeech(audioBlob: Blob, language: string = "english"): Promise<VoiceTranscribeResponse | null> {
  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");
    formData.append("language", language);

    const res = await fetch(`${API_BASE_URL}/voice/transcribe`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error(`Voice transcription error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error transcribing speech:", err);
    return null;
  }
}

export async function getVoiceStatus(): Promise<VoiceStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/voice/status`);
    if (!res.ok) throw new Error(`Voice status error: ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Error getting voice status:", err);
    return null;
  }
}

export function playAudioBase64(base64Audio: string): HTMLAudioElement {
  const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
  audio.play();
  return audio;
}
