/**
 * AI Service - Handles communication with AI endpoints
 */
import Config from "../config/Config";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  chat_history: ChatMessage[];
}

export interface ChatResponse {
  response: string;
  timestamp: string;
}

export interface SuggestionsResponse {
  suggestions: string[];
}

export interface WellnessReminderResponse {
  wellness_reminder: string | null;
  should_take_break: boolean;
  hours_driven: number;
}

/**
 * Send a chat message to the AI assistant
 */
export async function sendChatMessage(
  driverId: string,
  message: string,
  chatHistory: ChatMessage[] = []
): Promise<ChatResponse> {
  const url = `${Config.API_BASE_URL}/ai/chat/${driverId}`;
  const payload = {
    message,
    chat_history: chatHistory,
  };

  console.log('Sending chat request:', { url, payload });

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), Config.REQUEST_TIMEOUT);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log('Response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API error response:', errorText);
      throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    return data;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.error('Request timeout');
      throw new Error('Request timeout - server may be unreachable');
    }
    console.error('Fetch error:', error);
    throw error;
  }
}

/**
 * Get proactive suggestions for the driver
 */
export async function getProactiveSuggestions(
  driverId: string
): Promise<string[]> {
  const response = await fetch(
    `${Config.API_BASE_URL}/ai/suggestions/${driverId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data: SuggestionsResponse = await response.json();
  return data.suggestions;
}

/**
 * Get wellness reminder based on hours driven
 */
export async function getWellnessReminder(
  driverId: string,
  hoursDriven: number
): Promise<WellnessReminderResponse> {
  const response = await fetch(
    `${Config.API_BASE_URL}/ai/wellness/${driverId}?hours_driven=${hoursDriven}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}
