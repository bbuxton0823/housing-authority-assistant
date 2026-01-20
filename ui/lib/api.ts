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
