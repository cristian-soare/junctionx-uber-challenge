import Config from "../config/Config";
import { WorkingHoursRequest, OptimalTimeResponse, TimeScoresResponse, BestZoneResponse, ZoneScoresResponse } from "../models/api";

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

export async function getOptimalTime(
  driverId: string
): Promise<OptimalTimeResponse> {
  const url = `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/optimal-time`;
  console.log("getOptimalTime URL:", url);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  console.log("getOptimalTime status:", response.status);
  const responseText = await response.text();
  console.log("getOptimalTime response:", responseText);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }

  return JSON.parse(responseText);
}

export async function getTimeScores(
  driverId: string
): Promise<TimeScoresResponse> {
  const url = `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/time-scores`;
  console.log("getTimeScores URL:", url);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  console.log("getTimeScores status:", response.status);
  const responseText = await response.text();
  console.log("getTimeScores response:", responseText);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }

  return JSON.parse(responseText);
}

export async function getBestZone(
  driverId: string,
  currentTime?: number
): Promise<BestZoneResponse> {
  const url = currentTime !== undefined
    ? `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/best-zone?current_time=${currentTime}`
    : `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/best-zone`;
  console.log("getBestZone URL:", url);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  console.log("getBestZone status:", response.status);
  const responseText = await response.text();
  console.log("getBestZone response:", responseText);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }

  return JSON.parse(responseText);
}

export async function selectTime(
  driverId: string,
  time: number
): Promise<void> {
  const url = `${Config.API_BASE_URL}/drivers/${driverId}/selections/time`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ time }),
  });

  if (!response.ok) {
    const responseText = await response.text();
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }
}

export async function getZoneScores(
  driverId: string
): Promise<ZoneScoresResponse> {
  const url = `${Config.API_BASE_URL}/drivers/${driverId}/recommendations/zone-scores`;
  console.log("getZoneScores URL:", url);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  console.log("getZoneScores status:", response.status);
  const responseText = await response.text();
  console.log("getZoneScores response:", responseText);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }

  return JSON.parse(responseText);
}

export async function selectZone(
  driverId: string,
  clusterId: string
): Promise<void> {
  const url = `${Config.API_BASE_URL}/drivers/${driverId}/selections/zone`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ cluster_id: clusterId }),
  });

  if (!response.ok) {
    const responseText = await response.text();
    throw new Error(`API error: ${response.status} ${response.statusText} - ${responseText}`);
  }
}
