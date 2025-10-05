export interface WorkingHoursRequest {
  earliest_start_time: string;
  latest_start_time: string;
  nr_hours: number;
}

export interface TimeSelectionRequest {
  time: number;
}

export interface TimeScore {
  time: number;
  score: number;
  remaining_hours: number;
}

export interface OptimalTimeResponse {
  optimal_time: number;
  score: number;
  remaining_hours: number;
}

export interface TimeScoresResponse {
  scores: TimeScore[];
}

export interface ZoneScore {
  cluster_id: string;
  score: number;
  expected_earnings: number;
  expected_hourly_rate: number;
  lat: number;
  lon: number;
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  work_hours: number;
  remaining_hours: number;
  path_length: number;
}

export interface ZoneScoresResponse {
  zones: ZoneScore[];
}

export interface BestZoneResponse {
  cluster_id: string | null;
  score: number;
  expected_earnings: number;
  expected_hourly_rate: number;
  lat: number;
  lon: number;
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  work_hours: number;
  path_length: number | null;
  optimal_path: string[] | null;
  error: string | null;
}

export interface DriverSelectionsResponse {
  selected_time: number | null;
  remaining_hours: number | null;
  selected_zone: string | null;
}

export interface Coordinate {
  lat: number;
  lon: number;
}

export interface StartDrivingResponse {
  zone_id: string;
  zone_center: Coordinate;
  zone_corners: Coordinate[];
}

export function hourToTimeString(hour: number): string {
  if (hour < 0 || hour > 23) {
    throw new Error("Hour must be between 0 and 23");
  }
  return `${hour.toString().padStart(2, "0")}:00`;
}

export function timeStringToHour(time: string): number {
  const parts = time.split(":");
  if (parts.length !== 2) {
    throw new Error("Invalid time format. Expected HH:MM");
  }
  const hour = parseInt(parts[0], 10);
  if (isNaN(hour) || hour < 0 || hour > 23) {
    throw new Error("Invalid hour value");
  }
  return hour;
}
