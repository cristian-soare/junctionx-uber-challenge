/**
 * Driving Session Service - Handles driver hours tracking
 */
import Config from "../config/Config";

export interface DrivingHoursResponse {
  driver_id: string;
  total_hours_today: number;
  active_session_hours: number;
  is_driving: boolean;
  should_take_break: boolean;
  timestamp: string;
}

export interface SessionResponse {
  session_id?: number;
  driver_id: string;
  session_start?: string;
  session_end?: string;
  hours_driven?: number;
  status: string;
}

/**
 * Start a new driving session
 */
export async function startDrivingSession(
  driverId: string
): Promise<SessionResponse> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/start-session`,
    {
      method: "POST",
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

/**
 * Stop the active driving session
 */
export async function stopDrivingSession(
  driverId: string
): Promise<SessionResponse> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/stop-session`,
    {
      method: "POST",
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

/**
 * Get current driving hours for today
 */
export async function getDrivingHours(
  driverId: string
): Promise<DrivingHoursResponse> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/driving-hours`,
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
