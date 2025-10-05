/**
 * Driver Preferences Service - Handles working hours preferences and recommendations
 */
import Config from "../config/Config";

export interface WorkingHoursRequest {
  earliest_start_time: string;
  latest_start_time: string;
  nr_hours: number;
}

export interface OptimalTimeResponse {
  optimal_time: string;
  score: number;
  remaining_hours: number;
}

/**
 * Save driver's working hours preferences
 */
export async function saveWorkingHours(
  driverId: string,
  preferences: WorkingHoursRequest
): Promise<any> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/preferences`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(preferences),
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get driver's working hours preferences
 */
export async function getWorkingHours(driverId: string): Promise<any> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/preferences`,
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

/**
 * Get optimal start time recommendation
 */
export async function getOptimalTime(
  driverId: string
): Promise<OptimalTimeResponse> {
  const response = await fetch(
    `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/optimal-time`,
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
