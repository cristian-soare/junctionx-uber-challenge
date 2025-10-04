"""Compute service for driver optimization ML inference."""

from typing import Any

from app.schemas.internal import Coordinate, ZoneRecommendation


class ComputeService:
  """Service for driver optimization ML inference."""

  async def _predict_optimal_zone(
    self,
    driver_id: str,
    current_coordinate: Coordinate,
    all_surges: dict[str, float] | None = None,
  ) -> ZoneRecommendation:
    """Predict optimal hexagon zone for driver to move to.

    Model considers:
    - Historical demand patterns per zone
    - Current active requests
    - Predicted surge pricing
    - Distance from current coordinate
    - Competitor density (other drivers in zone)
    - Time of day patterns
    - Weather impact on zone demand

    Args:
        driver_id: Driver identifier.
        current_coordinate: Current geographic coordinate.
        all_surges: Dictionary of surge multipliers per hexagon.

    Returns:
        ZoneRecommendation object.

    """
    # TODO: Load ML model and run inference
    # - Get demand heatmap predictions from CSV/model
    # - Calculate distance to each zone using current_coordinate
    # - Consider driver's historical success rate per zone

    best_hex = "89fb0333e75a7e5"
    best_surge = 1.0
    if all_surges:
      for hex_id, surge in all_surges.items():
        if surge > best_surge:
          best_hex = hex_id
          best_surge = surge

    # TODO: Calculate actual distance using current_coordinate
    predicted_eph = best_surge * 20.0
    lat, lon = self._get_zone_coordinates(best_hex)

    return ZoneRecommendation(
      hexagon_id=best_hex,
      predicted_demand=best_surge,
      predicted_earnings_per_hour=predicted_eph,
      distance_km=2.5,  # TODO: Calculate from current_coordinate
      confidence=0.7,
      lat=lat,
      lon=lon,
    )

  async def process_trip_request(self, trip_request: Any) -> dict[str, Any]:
    """Process trip request (legacy method - keeping for compatibility).

    Args:
        trip_request: TripRequest object.

    Returns:
        Basic inference results.

    """
    return {
      "matched_drivers": [],
      "estimated_eta": None,
      "estimated_price": None,
      "surge_multiplier": 1.0,
    }

  async def compute_score(
    self,
    zone_id: str,
    start_time: int,
    remaining_hours: int,
    driver_id: str,
    city_id: int,
  ) -> float:
    """Calculate score for a (zone, time, remaining_hours) combination.

    This is the core scoring algorithm that will be replaced with ML model.
    Score considers:
    - Zone demand at specific time
    - Continuous working hours (longer = better)
    - Driver's historical performance in zone
    - Surge pricing patterns
    - Weather impact

    Args:
        zone_id: Hexagon zone identifier.
        start_time: Start hour (0-23).
        remaining_hours: Continuous hours from start_time.
        driver_id: Driver identifier.
        city_id: City identifier.

    Returns:
        Predicted score (higher is better).

    """
    # TODO: Replace with actual ML model inference
    hours_score = remaining_hours * 10.0

    if 7 <= start_time <= 9 or 17 <= start_time <= 19:
      time_score = 50.0
    elif 10 <= start_time <= 16:
      time_score = 30.0
    else:
      time_score = 20.0

    zone_score = 25.0

    return hours_score + time_score + zone_score

  async def get_optimal_time(
    self,
    driver_id: str,
    start_hour: int,
    end_hour: int,
    city_id: int,
  ) -> dict[str, Any]:
    """Find optimal start time from working hours range.

    Args:
        driver_id: Driver identifier.
        start_hour: Earliest start hour (0-23).
        end_hour: Latest end hour (0-23).
        city_id: City identifier.

    Returns:
        Dict with optimal_time, score, and remaining_hours.

    """
    zones = await self._get_city_zones(city_id)
    if not zones:
      zones = ["89fb0333e75a7e5"]

    best_time = start_hour
    best_score = 0.0
    best_remaining = 0

    if end_hour < start_hour:
      hours_range = list(range(start_hour, 24)) + list(range(end_hour + 1))
    else:
      hours_range = list(range(start_hour, end_hour + 1))

    for time in hours_range:
      if end_hour < start_hour:
        if time >= start_hour:
          remaining = 24 - time + end_hour
        else:
          remaining = end_hour - time
      else:
        remaining = end_hour - time

      if remaining <= 0:
        continue

      time_score = 0.0
      for zone in zones:
        zone_score = await self.compute_score(
          zone_id=zone,
          start_time=time,
          remaining_hours=remaining,
          driver_id=driver_id,
          city_id=city_id,
        )
        time_score += zone_score

      avg_score = time_score / len(zones) if zones else 0.0

      if avg_score > best_score:
        best_score = avg_score
        best_time = time
        best_remaining = remaining

    return {
      "optimal_time": best_time,
      "score": best_score,
      "remaining_hours": best_remaining,
    }

  async def get_all_time_scores(
    self,
    driver_id: str,
    start_hour: int,
    end_hour: int,
    city_id: int,
  ) -> list[dict[str, Any]]:
    """Get scores for all possible start times in working hours range.

    Args:
        driver_id: Driver identifier.
        start_hour: Earliest start hour (0-23).
        end_hour: Latest end hour (0-23).
        city_id: City identifier.

    Returns:
        List of dicts with time, score, and remaining_hours.

    """
    zones = await self._get_city_zones(city_id)
    if not zones:
      zones = ["89fb0333e75a7e5"]

    scores = []

    if end_hour < start_hour:
      hours_range = list(range(start_hour, 24)) + list(range(end_hour + 1))
    else:
      hours_range = list(range(start_hour, end_hour + 1))

    for time in hours_range:
      if end_hour < start_hour:
        if time >= start_hour:
          remaining = 24 - time + end_hour
        else:
          remaining = end_hour - time
      else:
        remaining = end_hour - time

      if remaining <= 0:
        continue

      time_score = 0.0
      for zone in zones:
        zone_score = await self.compute_score(
          zone_id=zone,
          start_time=time,
          remaining_hours=remaining,
          driver_id=driver_id,
          city_id=city_id,
        )
        time_score += zone_score

      avg_score = time_score / len(zones) if zones else 0.0

      scores.append(
        {
          "time": time,
          "score": avg_score,
          "remaining_hours": remaining,
        }
      )

    return scores

  async def get_all_zone_scores(
    self,
    driver_id: str,
    start_time: int,
    remaining_hours: int,
    city_id: int,
  ) -> list[dict[str, Any]]:
    """Get ranked zones by score for a specific time.

    Args:
        driver_id: Driver identifier.
        start_time: Start hour (0-23).
        remaining_hours: Continuous hours from start_time.
        city_id: City identifier.

    Returns:
        List of zones ranked by score (descending).

    """
    zones = await self._get_city_zones(city_id)
    if not zones:
      zones = ["89fb0333e75a7e5"]

    zone_scores = []
    for zone in zones:
      score = await self.compute_score(
        zone_id=zone,
        start_time=start_time,
        remaining_hours=remaining_hours,
        driver_id=driver_id,
        city_id=city_id,
      )

      lat, lon = self._get_zone_coordinates(zone)

      zone_scores.append(
        {
          "hexagon_id": zone,
          "score": score,
          "lat": lat,
          "lon": lon,
          "remaining_hours": remaining_hours,
        }
      )

    zone_scores.sort(key=lambda x: x["score"], reverse=True)

    return zone_scores

  async def get_best_zone_for_time(
    self,
    driver_id: str,
    start_time: int,
    remaining_hours: int,
    city_id: int,
  ) -> dict[str, Any]:
    """Get best zone for a specific time.

    Args:
        driver_id: Driver identifier.
        start_time: Start hour (0-23).
        remaining_hours: Continuous hours from start_time.
        city_id: City identifier.

    Returns:
        Best zone with score and coordinates.

    """
    zone_scores = await self.get_all_zone_scores(
      driver_id=driver_id,
      start_time=start_time,
      remaining_hours=remaining_hours,
      city_id=city_id,
    )

    if zone_scores:
      return zone_scores[0]

    return {
      "hexagon_id": "89fb0333e75a7e5",
      "score": 0.0,
      "lat": 47.4979,
      "lon": 19.0402,
      "remaining_hours": remaining_hours,
    }

  async def _get_city_zones(self, city_id: int) -> list[str]:
    """Get all zones for a city.

    TODO: Replace with actual database query or hexagon generation.

    Args:
        city_id: City identifier.

    Returns:
        List of hexagon IDs.

    """
    return [
      "89fb0333e75a7e5",
      "89fb0333e75a7e6",
      "89fb0333e75a7e7",
      "89fb0333e75a7e8",
      "89fb0333e75a7e9",
    ]

  def _get_zone_coordinates(self, hexagon_id: str) -> tuple[float, float]:
    """Get center coordinates for a hexagon zone.

    TODO: Replace with actual H3 library call (h3.h3_to_geo).

    Args:
        hexagon_id: H3 hexagon identifier.

    Returns:
        Tuple of (lat, lon).

    """
    return (47.4979, 19.0402)

  def calculate_zone_center(
    self, hexagon_coordinates: list[tuple[float, float]]
  ) -> tuple[float, float]:
    """Calculate center coordinate of a zone from hexagon coordinates.

    Args:
        hexagon_coordinates: List of (lat, lon) tuples for hexagons in zone.

    Returns:
        Tuple of (center_lat, center_lon).

    """
    if not hexagon_coordinates:
      return (0.0, 0.0)

    avg_lat = sum(lat for lat, _ in hexagon_coordinates) / len(hexagon_coordinates)
    avg_lon = sum(lon for _, lon in hexagon_coordinates) / len(hexagon_coordinates)

    return (avg_lat, avg_lon)

  async def get_zone_corners(self, zone_id: str, city_id: int) -> list[dict[str, float]]:
    """Get bounding box corners for a zone.

    Args:
        zone_id: Zone identifier (hexagon ID).
        city_id: City identifier.

    Returns:
        List of 4 corner coordinates representing the bounding box.

    """
    zones = await self._get_city_zones(city_id)

    hexagon_coords = []
    for hex_id in zones:
      lat, lon = self._get_zone_coordinates(hex_id)
      hexagon_coords.append((lat, lon))

    if not hexagon_coords:
      return []

    lats = [coord[0] for coord in hexagon_coords]
    lons = [coord[1] for coord in hexagon_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    return [
      {"lat": min_lat, "lon": min_lon},
      {"lat": min_lat, "lon": max_lon},
      {"lat": max_lat, "lon": max_lon},
      {"lat": max_lat, "lon": min_lon},
    ]
