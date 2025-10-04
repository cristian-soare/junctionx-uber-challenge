"""Compute service for driver optimization ML inference."""

from typing import Any
from datetime import datetime, timedelta
import pandas as pd

from app.schemas.internal import Coordinate, ZoneRecommendation
from app.dynamic_programming_optimizer import MobilityOptimizer


class ComputeService:
  """Service for driver optimization ML inference."""

  def __init__(self):
    """Initialize the compute service with the DP optimizer."""
    self.optimizer = MobilityOptimizer(
      epsilon=0.1,
      gamma=0.95,
      lambda_floor=0.5
    )

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

  # async def _predict_optimal_zone(
  #   self,
  #   driver_id: str,
  #   current_location: Location,
  #   all_surges: dict[str, float] | None = None,
  # ) -> ZoneRecommendation:
  #   """Predict optimal hexagon zone for driver to move to.

  #   Model considers:
  #   - Historical demand patterns per zone
  #   - Current active requests
  #   - Predicted surge pricing
  #   - Distance from current location
  #   - Competitor density (other drivers in zone)
  #   - Time of day patterns
  #   - Weather impact on zone demand

  #   Args:
  #       driver_id: Driver identifier.
  #       current_location: Current geographic location with city.
  #       all_surges: Dictionary of surge multipliers per hexagon.

  #   Returns:
  #       ZoneRecommendation object.

  #   """
  #   # TODO: Load ML model and run inference
  #   # - Get demand heatmap predictions from CSV/model
  #   # - Calculate distance to each zone using current_location
  #   # - Consider driver's historical success rate per zone

  #   best_hex = "89fb0333e75a7e5"
  #   best_surge = 1.0
  #   if all_surges:
  #     for hex_id, surge in all_surges.items():
  #       if surge > best_surge:
  #         best_hex = hex_id
  #         best_surge = surge

  #   # TODO: Calculate actual distance using current_location
  #   predicted_eph = best_surge * 20.0
  #   coords = self._get_zone_coordinates(best_hex)

  #   return ZoneRecommendation(
  #     hexagon_id=best_hex,
  #     predicted_demand=best_surge,
  #     predicted_earnings_per_hour=predicted_eph,
  #     distance_km=2.5,  # TODO: Calculate from current_location
  #     confidence=0.7,
  #     lat=coords['lat_avg'],
  #     lon=coords['lon_avg'],
  #   )

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
    start_date: str = None,
  ) -> float:
    """Calculate score for a (zone, time, remaining_hours) combination using DP optimizer.

    Uses the dynamic programming optimizer to compute expected earnings for a cluster
    at a specific time and work duration. This provides accurate, data-driven scoring
    based on:
    - Historical demand patterns per zone
    - Actual trip data (fares, durations, counts)
    - Surge pricing patterns
    - Weather impact
    - Optimal routing through the cluster network

    Args:
        zone_id: Cluster/zone identifier.
        start_time: Start hour (0-23).
        remaining_hours: Continuous hours from start_time.
        driver_id: Driver identifier.
        city_id: City identifier.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        Expected earnings score (higher is better).

    """
    # Parse or default the start date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    # Validate city and cluster exist
    if city_id not in self.optimizer.graphs:
      return 0.0

    graph = self.optimizer.graphs[city_id]
    if zone_id not in graph.nodes():
      return 0.0

    # Use DP optimizer to compute expected earnings for this cluster
    try:
      expected_earnings, _ = self.optimizer.solve_dp(
        city_id=city_id,
        start_cluster=zone_id,
        start_hour=start_time,
        work_hours=remaining_hours,
        start_date=date
      )
      return expected_earnings
    except Exception as e:
      print(f"Error computing score for cluster {zone_id}: {e}")
      return 0.0

  async def get_optimal_time(
    self,
    driver_id: str,
    start_hour: int,
    end_hour: int,
    work_hours: int,
    city_id: int,
    start_date: str = None,
  ) -> dict[str, Any]:
    """Find optimal start time from working hours range using Dynamic Programming.

    This function evaluates all possible start times within the given timeframe
    and uses the DP optimizer to find the best starting hour that maximizes
    expected earnings for the specified work duration.

    Args:
        driver_id: Driver identifier.
        start_hour: Earliest start hour (0-23) - start of timeframe.
        end_hour: Latest end hour (0-23) - end of timeframe.
        city_id: City identifier.
        work_hours: Number of hours the driver wants to work.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        Dict with optimal_time, score (expected earnings), and remaining_hours (0).

    """
    # Parse or default the start date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    # Handle wraparound times (e.g., 22:00 to 06:00)
    if end_hour < start_hour:
      hours_range = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
    else:
      hours_range = list(range(start_hour, end_hour + 1))

    # Get all clusters for the city to find best starting position for each hour
    if city_id not in self.optimizer.graphs:
      return {
        "optimal_time": start_hour,
        "score": 0.0,
        "remaining_hours": 0,
        "error": f"City {city_id} not found in graphs"
      }

    graph = self.optimizer.graphs[city_id]
    clusters = list(graph.nodes())

    if not clusters:
      return {
        "optimal_time": start_hour,
        "score": 0.0,
        "remaining_hours": 0,
        "error": "No clusters found for city"
      }

    best_start_hour = start_hour
    best_score = 0.0
    best_cluster = None

    # Evaluate each possible start hour in the timeframe
    for candidate_hour in hours_range:
      # For this start hour, find the best starting cluster using DP
      try:
        best_positions = self.optimizer.analyze_best_starting_positions(
          city_id=city_id,
          start_hour=candidate_hour,
          work_hours=work_hours,
          start_date=date,
          top_k=1  # We only need the best one
        )

        if best_positions:
          cluster, expected_earnings, path = best_positions[0]

          # Update if this is better than current best
          if expected_earnings > best_score:
            best_score = expected_earnings
            best_start_hour = candidate_hour
            best_cluster = cluster

      except Exception as e:
        print(f"Error analyzing start hour {candidate_hour}: {e}")
        continue

    return {
      "optimal_time": best_start_hour,
      "score": best_score,
      "remaining_hours": 0,  # Set to 0 as requested
    }

  async def get_optimal_strategy(
    self,
    driver_id: str,
    start_hour: int,
    city_id: int,
    work_hours: int,
    start_cluster: str = None,
    start_date: str = None,
  ) -> dict[str, Any]:
    """Get the complete optimal strategy for a driver starting at a specific time.

    Args:
        driver_id: Driver identifier.
        start_hour: Hour to start working (0-23).
        city_id: City identifier.
        work_hours: Number of hours to work.
        start_cluster: Starting cluster ID. If None, finds best cluster.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        Dict with strategy details including path, earnings, and timing.

    """
    # Parse date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    if city_id not in self.optimizer.graphs:
      return {
        "error": f"City {city_id} not found in graphs"
      }

    # If no starting cluster specified, find the best one
    if start_cluster is None:
      best_positions = self.optimizer.analyze_best_starting_positions(
        city_id=city_id,
        start_hour=start_hour,
        work_hours=work_hours,
        start_date=date,
        top_k=1
      )

      if not best_positions:
        return {"error": "Could not find optimal starting position"}

      start_cluster, expected_earnings, optimal_path = best_positions[0]
    else:
      # Use specified cluster
      expected_earnings, optimal_path = self.optimizer.solve_dp(
        city_id=city_id,
        start_cluster=start_cluster,
        start_hour=start_hour,
        work_hours=work_hours,
        start_date=date
      )

    # Get cluster coordinates from CSV
    coords = self._get_zone_coordinates(start_cluster)

    return {
      "start_cluster": start_cluster,
      "start_hour": start_hour,
      "work_hours": work_hours,
      "expected_total_earnings": expected_earnings,
      "expected_hourly_rate": expected_earnings / work_hours if work_hours > 0 else 0,
      "optimal_path": optimal_path,
      "num_trips": len(optimal_path) - 1 if len(optimal_path) > 1 else 0,
      "path_length": len(optimal_path),
      "start_lat": coords['lat_avg'],
      "start_lon": coords['lon_avg'],
      "start_lat_min": coords['lat_min'],
      "start_lat_max": coords['lat_max'],
      "start_lon_min": coords['lon_min'],
      "start_lon_max": coords['lon_max'],
    }

  async def get_all_time_scores(
    self,
    driver_id: str,
    start_hour: int,
    end_hour: int,
    city_id: int,
    work_hours: int = None,
    start_date: str = None,
  ) -> list[dict[str, Any]]:
    """Get scores for all possible start times in working hours range using DP optimizer.

    Args:
        driver_id: Driver identifier.
        start_hour: Earliest start hour (0-23).
        end_hour: Latest end hour (0-23).
        city_id: City identifier.
        work_hours: Number of hours to work. If None, uses remaining hours for each time.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        List of dicts with time, score (best expected earnings), remaining_hours, and best_cluster.

    """
    # Parse or default the start date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    # Validate city exists in graphs
    if city_id not in self.optimizer.graphs:
      return []

    scores = []

    # Calculate hours range (handle wraparound)
    if end_hour < start_hour:
      hours_range = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
    else:
      hours_range = list(range(start_hour, end_hour + 1))

    for time in hours_range:
      # Calculate remaining hours in the timeframe
      if end_hour < start_hour:
        if time >= start_hour:
          remaining = 24 - time + end_hour
        else:
          remaining = end_hour - time
      else:
        remaining = end_hour - time

      if remaining <= 0:
        continue

      # Use work_hours if provided, otherwise use remaining hours
      hours_to_work = work_hours if work_hours is not None else remaining

      # Find best starting cluster for this time using DP optimizer
      try:
        best_positions = self.optimizer.analyze_best_starting_positions(
          city_id=city_id,
          start_hour=time,
          work_hours=hours_to_work,
          start_date=date,
          top_k=1  # Only need the best one
        )

        if best_positions:
          best_cluster, best_score, _ = best_positions[0]

          scores.append(
            {
              "time": time,
              "score": best_score,
              "remaining_hours": remaining,
              "best_cluster": best_cluster,
              "work_hours": hours_to_work,
            }
          )
        else:
          # No valid position found
          scores.append(
            {
              "time": time,
              "score": 0.0,
              "remaining_hours": remaining,
              "best_cluster": None,
              "work_hours": hours_to_work,
            }
          )

      except Exception as e:
        print(f"Error analyzing time {time}: {e}")
        scores.append(
          {
            "time": time,
            "score": 0.0,
            "remaining_hours": remaining,
            "best_cluster": None,
            "work_hours": hours_to_work,
            "error": str(e),
          }
        )

    return scores

  async def get_all_zone_scores(
    self,
    driver_id: str,
    start_time: int,
    work_hours: int,
    city_id: int,
    start_date: str = None,
  ) -> list[dict[str, Any]]:
    """Get ranked clusters (zones) by expected earnings using DP optimizer.

    Args:
        driver_id: Driver identifier.
        start_time: Start hour (0-23).
        work_hours: Continuous hours from start_time.
        city_id: City identifier.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        List of clusters ranked by expected earnings (descending).

    """
    # Parse or default the start date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    # Validate city exists in graphs
    if city_id not in self.optimizer.graphs:
      return []

    graph = self.optimizer.graphs[city_id]
    clusters = list(graph.nodes())

    if not clusters:
      return []

    cluster_scores = []

    # Analyze each cluster as a potential starting position
    for cluster in clusters:
      try:
        # Use DP to compute optimal earnings starting from this cluster
        expected_earnings, optimal_path = self.optimizer.solve_dp(
          city_id=city_id,
          start_cluster=cluster,
          start_hour=start_time,
          work_hours=work_hours,
          start_date=date
        )

        # Get cluster coordinates from CSV
        coords = self._get_zone_coordinates(cluster)

        cluster_scores.append(
          {
            "hexagon_id": cluster,
            "cluster_id": cluster,
            "score": expected_earnings,
            "expected_earnings": expected_earnings,
            "expected_hourly_rate": expected_earnings / work_hours if work_hours > 0 else 0,
            "lat": coords['lat_avg'],
            "lon": coords['lon_avg'],
            "lat_min": coords['lat_min'],
            "lat_max": coords['lat_max'],
            "lon_min": coords['lon_min'],
            "lon_max": coords['lon_max'],
            "work_hours": work_hours,
            "path_length": len(optimal_path),
          }
        )

      except Exception as e:
        print(f"Error analyzing cluster {cluster}: {e}")
        continue

    # Sort by expected earnings (descending)
    cluster_scores.sort(key=lambda x: x["score"], reverse=True)

    return cluster_scores

  async def get_best_zone_for_time(
    self,
    driver_id: str,
    start_time: int,
    remaining_hours: int,
    city_id: int,
    start_date: str = None,
  ) -> dict[str, Any]:
    """Get best cluster (zone) for a specific time using DP optimizer.

    Args:
        driver_id: Driver identifier.
        start_time: Start hour (0-23).
        remaining_hours: Continuous hours from start_time.
        city_id: City identifier.
        start_date: Date string (YYYY-MM-DD). If None, uses today.

    Returns:
        Best cluster with expected earnings, coordinates, and optimal path info.

    """
    # Parse or default the start date
    if start_date is None:
      date = datetime.now()
    else:
      try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
      except ValueError:
        date = datetime.now()

    # Validate city exists in graphs
    if city_id not in self.optimizer.graphs:
      return {
        "cluster_id": None,
        "score": 0.0,
        "expected_earnings": 0.0,
        "expected_hourly_rate": 0.0,
        "lat": 0.0,
        "lon": 0.0,
        "lat_min": 0.0,
        "lat_max": 0.0,
        "lon_min": 0.0,
        "lon_max": 0.0,
        "work_hours": remaining_hours,
        "error": f"City {city_id} not found in graphs"
      }

    # Use DP optimizer to find the best starting position
    try:
      best_positions = self.optimizer.analyze_best_starting_positions(
        city_id=city_id,
        start_hour=start_time,
        work_hours=remaining_hours,
        start_date=date,
        top_k=1  # Only need the best one
      )

      if best_positions:
        best_cluster, expected_earnings, optimal_path = best_positions[0]

        # Get cluster coordinates from CSV
        coords = self._get_zone_coordinates(best_cluster)

        return {
          "cluster_id": best_cluster,
          "score": expected_earnings,
          "expected_earnings": expected_earnings,
          "expected_hourly_rate": expected_earnings / remaining_hours if remaining_hours > 0 else 0,
          "lat": coords['lat_avg'],
          "lon": coords['lon_avg'],
          "lat_min": coords['lat_min'],
          "lat_max": coords['lat_max'],
          "lon_min": coords['lon_min'],
          "lon_max": coords['lon_max'],
          "work_hours": remaining_hours,
          "path_length": len(optimal_path),
          "optimal_path": optimal_path,
        }

    except Exception as e:
      print(f"Error finding best zone: {e}")
      pass

    # Fallback if no valid position found
    return {
      "cluster_id": None,
      "score": 0.0,
      "expected_earnings": 0.0,
      "expected_hourly_rate": 0.0,
      "lat": 0.0,
      "lon": 0.0,
      "lat_min": 0.0,
      "lat_max": 0.0,
      "lon_min": 0.0,
      "lon_max": 0.0,
      "work_hours": remaining_hours,
      "error": "Could not find optimal starting position"
    }

  # async def _get_city_zones(self, city_id: int) -> list[str]:
  #   """Get all zones for a city.

  #   TODO: Replace with actual database query or hexagon generation.

  #   Args:
  #       city_id: City identifier.

  #   Returns:
  #       List of hexagon IDs.

  #   """
  #   return [
  #     "89fb0333e75a7e5",
  #     "89fb0333e75a7e6",
  #     "89fb0333e75a7e7",
  #     "89fb0333e75a7e8",
  #     "89fb0333e75a7e9",
  #   ]

  def _get_zone_coordinates(self, cluster_id: str) -> dict[str, float]:
    """Get bounding box coordinates for a cluster from the CSV file.

    Args:
        cluster_id: Cluster identifier (e.g., 'c_1_0', 'c_2_1').

    Returns:
        Dictionary with lat_min, lat_max, lon_min, lon_max, lat_avg, lon_avg.
        Returns zeros if cluster not found.

    """
    # Load cluster coordinates from CSV if not already loaded
    if not hasattr(self, '_cluster_coords'):
      try:
        coords_df = pd.read_csv('/app/data/cluster_coordinates_stats.csv')
        self._cluster_coords = {}
        for _, row in coords_df.iterrows():
          self._cluster_coords[row['cluster']] = {
            'lat_min': float(row['lat_min']),
            'lat_max': float(row['lat_max']),
            'lat_avg': float(row['lat_avg']),
            'lon_min': float(row['lon_min']),
            'lon_max': float(row['lon_max']),
            'lon_avg': float(row['lon_avg']),
          }
      except Exception as e:
        print(f"Error loading cluster coordinates: {e}")
        self._cluster_coords = {}
    
    # Return coordinates for the cluster, or default if not found
    return self._cluster_coords.get(cluster_id, {
      'lat_min': 0.0,
      'lat_max': 0.0,
      'lat_avg': 0.0,
      'lon_min': 0.0,
      'lon_max': 0.0,
      'lon_avg': 0.0,
    })

  # def calculate_zone_center(
  #   self, hexagon_coordinates: list[tuple[float, float]]
  # ) -> tuple[float, float]:
  #   """Calculate center coordinate of a zone from hexagon coordinates.

  #   Args:
  #       hexagon_coordinates: List of (lat, lon) tuples for hexagons in zone.

  #   Returns:
  #       Tuple of (center_lat, center_lon).

  #   """
  #   if not hexagon_coordinates:
  #     return (0.0, 0.0)

  #   avg_lat = sum(lat for lat, _ in hexagon_coordinates) / len(hexagon_coordinates)
  #   avg_lon = sum(lon for _, lon in hexagon_coordinates) / len(hexagon_coordinates)
