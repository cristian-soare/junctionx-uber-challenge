"""Service layer for real-time operational data and inference."""

from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.compute import ComputeService
from app.database import db_manager
from app.models import (
  CompletedTrip,
  DriverStateHistory,
  SurgeHistory,
  TripRequestHistory,
  WeatherHistory,
)
from app.schemas.input import CompletedTripRequest
from app.schemas.internal import DriverLocation, Location, TripRequest


class DataService:
  """Service for managing real-time operational data."""

  def __init__(self) -> None:
    """Initialize the data service."""
    self.compute_service = ComputeService()

  async def store_driver_location(
    self,
    driver_id: str,
    location: Location,
    status: str,
  ) -> dict[str, Any]:
    """
    Store real-time driver location in database.

    Args:
        driver_id: Driver identifier.
        location: Geographic location with city.
        status: Driver status (online/offline/engaged).

    Returns:
        Confirmation with stored data.
    """
    timestamp = datetime.now()

    # Create DriverLocation model
    driver_location = DriverLocation(
      driver_id=driver_id,
      location=location,
      status=status,
      timestamp=timestamp,
    )

    # Redis: Store current location for real-time queries
    await db_manager.set_driver_location(
      driver_id=driver_id,
      lat=location.lat,
      lon=location.lon,
      status=status,
      timestamp=timestamp.isoformat(),
    )

    # SQLite: Store state change history for ML training
    # TODO: Only insert if state changed from previous
    async with db_manager.get_session() as session:
      state_record = DriverStateHistory(
        driver_id=driver_id,
        state=status,
        city_id=location.city_id,
        lat=location.lat,
        lon=location.lon,
        timestamp=timestamp,
      )
      session.add(state_record)
      await session.commit()

    return {
      "driver_id": driver_id,
      "location": location.model_dump(),
      "status": status,
      "timestamp": timestamp.isoformat(),
    }

  async def get_driver_recommendation(
    self,
    driver_id: str,
    current_state: str,
    current_location: Location,
  ) -> dict[str, Any]:
    """
    Get ML-based recommendation for driver.

    Determines:
    1. Should driver change state (offline -> idle, etc.)
    2. Which hexagon zone to move to for optimal earnings

    Args:
        driver_id: Driver identifier.
        current_state: Current driver state (offline/idle/engaged).
        current_location: Current geographic location with city.

    Returns:
        Recommendation with state change and optimal zone.
    """
    # Get recommendation from compute service
    recommendation = await self.compute_service.get_driver_recommendation(
      driver_id=driver_id,
      current_state=current_state,
      current_location=current_location,
    )

    return recommendation

  async def store_trip_request(
    self,
    rider_id: str,
    pickup: Location,
    drop: Location | None = None,
  ) -> dict[str, Any]:
    """
    Store trip request in database.

    Args:
        rider_id: Rider identifier.
        pickup: Pickup location.
        drop: Drop-off location (optional).

    Returns:
        Trip request data.
    """
    timestamp = datetime.now()
    request_id = f"req_{int(timestamp.timestamp() * 1000)}"

    # Create TripRequest model
    trip_request = TripRequest(
      request_id=request_id,
      rider_id=rider_id,
      pickup=pickup,
      drop=drop,
      timestamp=timestamp,
    )

    # Redis: Store for real-time demand tracking (last hour)
    await db_manager.add_trip_request(
      request_id=request_id,
      rider_id=rider_id,
      pickup_lat=pickup.lat,
      pickup_lon=pickup.lon,
      timestamp=str(timestamp.timestamp()),
    )

    # SQLite: Store for historical demand analysis
    async with db_manager.get_session() as session:
      trip_record = TripRequestHistory(
        request_id=request_id,
        rider_id=rider_id,
        city_id=pickup.city_id,
        pickup_lat=pickup.lat,
        pickup_lon=pickup.lon,
        pickup_hex="",  # TODO: Calculate hex from lat/lon
        timestamp=timestamp,
      )
      session.add(trip_record)
      await session.commit()

    return {
      "request_id": request_id,
      "rider_id": rider_id,
      "pickup": pickup.model_dump(),
      "drop": drop.model_dump() if drop else None,
      "timestamp": timestamp.isoformat(),
    }

  async def store_weather_update(
    self,
    city_id: int,
    weather: str,
    temperature: float | None = None,
  ) -> dict[str, Any]:
    """
    Store weather update for a city.

    Args:
        city_id: City identifier.
        weather: Weather condition (clear/rain/snow).
        temperature: Temperature in Celsius (optional).

    Returns:
        Confirmation with stored data.
    """
    timestamp = datetime.now()

    # Redis: Store current weather for real-time access
    await db_manager.set_weather(
      city_id=city_id,
      weather=weather,
      temperature=temperature,
    )

    # SQLite: Store for historical weather pattern analysis
    async with db_manager.get_session() as session:
      weather_record = WeatherHistory(
        city_id=city_id,
        weather=weather,
        temperature=temperature,
        timestamp=timestamp,
      )
      session.add(weather_record)
      await session.commit()

    return {
      "city_id": city_id,
      "weather": weather,
      "temperature": temperature,
      "timestamp": timestamp.isoformat(),
    }

  async def store_surge_update(
    self,
    city_id: int,
    hexagon_id: str,
    surge_multiplier: float,
  ) -> dict[str, Any]:
    """
    Store surge pricing update for a zone.

    Args:
        city_id: City identifier.
        hexagon_id: Hexagon zone identifier.
        surge_multiplier: Current surge multiplier.

    Returns:
        Confirmation with stored data.
    """
    timestamp = datetime.now()

    # Redis: Store current surge for fast access (expires in 5 min)
    await db_manager.set_surge(
      city_id=city_id,
      hexagon_id=hexagon_id,
      surge_multiplier=surge_multiplier,
    )

    # SQLite: Store for surge pattern analysis
    async with db_manager.get_session() as session:
      surge_record = SurgeHistory(
        city_id=city_id,
        hexagon_id=hexagon_id,
        surge_multiplier=surge_multiplier,
        timestamp=timestamp,
      )
      session.add(surge_record)
      await session.commit()

    return {
      "city_id": city_id,
      "hexagon_id": hexagon_id,
      "surge_multiplier": surge_multiplier,
      "timestamp": timestamp.isoformat(),
    }

  async def store_completed_trip(
    self,
    trip_request: CompletedTripRequest,
  ) -> dict[str, Any]:
    """
    Store completed trip for historical analysis.

    Args:
        trip_request: Completed trip request data.

    Returns:
        Confirmation with stored data.
    """
    timestamp = datetime.now()

    # SQLite: Store completed trip for driver performance analysis
    async with db_manager.get_session() as session:
      trip_record = CompletedTrip(
        driver_id=trip_request.driver_id,
        trip_id=trip_request.trip_id,
        city_id=trip_request.city_id,
        pickup_hex=trip_request.pickup_hex,
        drop_hex=trip_request.drop_hex,
        distance_km=trip_request.distance_km,
        duration_mins=trip_request.duration_mins,
        earnings=trip_request.earnings,
        tips=trip_request.tips,
        surge_multiplier=trip_request.surge_multiplier,
        timestamp=timestamp,
      )
      session.add(trip_record)
      await session.commit()

    return {
      "driver_id": trip_request.driver_id,
      "trip_id": trip_request.trip_id,
      "timestamp": timestamp.isoformat(),
    }

  async def get_active_drivers(self, city_id: int) -> list[dict[str, Any]]:
    """
    Get all active drivers in a city.

    Args:
        city_id: City identifier.

    Returns:
        List of active driver locations.
    """
    # TODO: Query Redis for all active driver locations by city
    # Use pattern matching on driver:location:* keys
    return []

  async def get_recent_requests(self, limit: int = 100) -> list[dict[str, Any]]:
    """
    Get recent trip requests.

    Args:
        limit: Maximum number of requests to return.

    Returns:
        List of recent trip requests.
    """
    # Redis: Get recent requests from sorted set (last hour)
    return await db_manager.get_recent_trip_requests(limit)

  async def get_driver_state_history(
    self,
    driver_id: str,
    hours: int = 24,
  ) -> list[dict[str, Any]]:
    """
    Get driver's state change history.

    Args:
        driver_id: Driver identifier.
        hours: Number of hours to look back.

    Returns:
        List of state changes with timestamps.
    """
    # SQLite: Query historical state changes
    cutoff_time = datetime.now().timestamp() - (hours * 3600)
    cutoff_datetime = datetime.fromtimestamp(cutoff_time)

    async with db_manager.get_session() as session:
      stmt = (
        select(DriverStateHistory)
        .where(DriverStateHistory.driver_id == driver_id)
        .where(DriverStateHistory.timestamp >= cutoff_datetime)
        .order_by(DriverStateHistory.timestamp.desc())
      )
      result = await session.execute(stmt)
      records = result.scalars().all()

      return [
        {
          "state": record.state,
          "city_id": record.city_id,
          "lat": record.lat,
          "lon": record.lon,
          "timestamp": record.timestamp.isoformat(),
        }
        for record in records
      ]
