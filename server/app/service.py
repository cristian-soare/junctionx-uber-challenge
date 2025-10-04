"""Service layer for real-time operational data and inference."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.compute import ComputeService
from app.database import db_manager
from app.exceptions import (
  CurrentTimeOutsideWorkingHoursError,
  DriverPreferencesNotSetError,
  TimeNotSelectedAndNoCurrentTimeError,
  TimeNotSelectedError,
  TimeOutsideWorkingHoursError,
)
from app.models import (
  CompletedTrip,
  DriverPreferences,
  DriverStateHistory,
  SurgeHistory,
  TripRequestHistory,
  WeatherHistory,
)
from app.schemas.input import CompletedTripRequest
from app.schemas.internal import Location


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
    timestamp: datetime,
  ) -> dict[str, Any]:
    """Store real-time driver location in database.

    Args:
        driver_id: Driver identifier.
        location: Geographic location with city.
        status: Driver status (online/offline/engaged).
        timestamp: Timestamp when location was captured.

    Returns:
        Confirmation with stored data.

    """
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

  async def store_trip_request(
    self,
    rider_id: str,
    pickup: Location,
    drop: Location | None,
    timestamp: datetime,
  ) -> dict[str, Any]:
    """Store trip request in database.

    Args:
        rider_id: Rider identifier.
        pickup: Pickup location.
        drop: Drop-off location (optional).
        timestamp: Timestamp when trip was requested.

    Returns:
        Trip request data.

    """
    request_id = f"req_{int(timestamp.timestamp() * 1000)}"

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
    temperature: float | None,
    timestamp: datetime,
  ) -> dict[str, Any]:
    """Store weather update for a city.

    Args:
        city_id: City identifier.
        weather: Weather condition (clear/rain/snow).
        temperature: Temperature in Celsius (optional).
        timestamp: Timestamp of weather observation.

    Returns:
        Confirmation with stored data.

    """
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
    timestamp: datetime,
  ) -> dict[str, Any]:
    """Store surge pricing update for a zone.

    Args:
        city_id: City identifier.
        hexagon_id: Hexagon zone identifier.
        surge_multiplier: Current surge multiplier.
        timestamp: Timestamp of surge calculation.

    Returns:
        Confirmation with stored data.

    """
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
    """Store completed trip for historical analysis.

    Args:
        trip_request: Completed trip request data.

    Returns:
        Confirmation with stored data.

    """
    timestamp = trip_request.timestamp

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

  async def get_recent_requests(self, limit: int = 100) -> list[dict[str, Any]]:
    """Get recent trip requests.

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
    """Get driver's state change history.

    Args:
        driver_id: Driver identifier.
        hours: Number of hours to look back.

    Returns:
        List of state changes with timestamps.

    """
    # SQLite: Query historical state changes
    cutoff_time = datetime.now(UTC).timestamp() - (hours * 3600)
    cutoff_datetime = datetime.fromtimestamp(cutoff_time, tz=UTC)

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

  async def store_working_hours(
    self,
    driver_id: str,
    start_hour: int,
    end_hour: int,
    city_id: int,
  ) -> dict[str, Any]:
    """Store driver's working hours preferences.

    Args:
        driver_id: Driver identifier.
        start_hour: Start hour (0-23).
        end_hour: End hour (0-23).
        city_id: City identifier.

    Returns:
        Confirmation with stored data.

    """
    timestamp = datetime.now(UTC)

    async with db_manager.get_session() as session:
      # Check if preferences already exist
      stmt = select(DriverPreferences).where(DriverPreferences.driver_id == driver_id)
      result = await session.execute(stmt)
      existing = result.scalar_one_or_none()

      if existing:
        # Update existing preferences
        existing.start_hour = start_hour
        existing.end_hour = end_hour
        existing.city_id = city_id
        existing.updated_at = timestamp
      else:
        # Create new preferences
        preferences = DriverPreferences(
          driver_id=driver_id,
          start_hour=start_hour,
          end_hour=end_hour,
          city_id=city_id,
          updated_at=timestamp,
        )
        session.add(preferences)

      await session.commit()

    return {
      "driver_id": driver_id,
      "start_hour": start_hour,
      "end_hour": end_hour,
      "city_id": city_id,
      "updated_at": timestamp.isoformat(),
    }

  async def get_working_hours(self, driver_id: str) -> dict[str, Any] | None:
    """Get driver's working hours preferences.

    Args:
      driver_id: Driver identifier.

    Returns:
      Working hours or None if not set.

    """
    async with db_manager.get_session() as session:
      stmt = select(DriverPreferences).where(DriverPreferences.driver_id == driver_id)
      result = await session.execute(stmt)
      preferences = result.scalar_one_or_none()

      if preferences:
        return {
          "driver_id": preferences.driver_id,
          "start_hour": preferences.start_hour,
          "end_hour": preferences.end_hour,
          "city_id": preferences.city_id,
          "updated_at": preferences.updated_at.isoformat(),
        }

      return None

  async def get_optimal_time(self, driver_id: str) -> dict[str, Any]:
    """Get optimal start time based on driver's working hours.

    Args:
        driver_id: Driver identifier.

    Returns:
        Optimal time with score and remaining hours.

    """
    # Get driver's working hours
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    # Calculate optimal time
    result = await self.compute_service.get_optimal_time(
      driver_id=driver_id,
      start_hour=preferences["start_hour"],
      end_hour=preferences["end_hour"],
      city_id=preferences["city_id"],
    )

    # Publish notification to Redis pub/sub
    await db_manager.publish_optimal_time_notification(
      driver_id=driver_id,
      optimal_time=result["optimal_time"],
      score=result["score"],
      remaining_hours=result["remaining_hours"],
    )

    return result

  async def get_all_time_scores(self, driver_id: str) -> list[dict[str, Any]]:
    """Get scores for all possible start times.

    Args:
        driver_id: Driver identifier.

    Returns:
        List of time scores.

    """
    # Get driver's working hours
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    # Get all time scores
    return await self.compute_service.get_all_time_scores(
      driver_id=driver_id,
      start_hour=preferences["start_hour"],
      end_hour=preferences["end_hour"],
      city_id=preferences["city_id"],
    )

  async def select_time(self, driver_id: str, time: int) -> dict[str, Any]:
    """Select a start time and store it.

    Args:
        driver_id: Driver identifier.
        time: Selected hour (0-23).

    Returns:
        Confirmation with selected time and remaining hours.

    """
    # Get driver's working hours to calculate remaining hours
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    start_hour = preferences["start_hour"]
    end_hour = preferences["end_hour"]

    # Calculate remaining hours
    if end_hour < start_hour:  # Wrap-around case
      if time >= start_hour:
        remaining_hours = 24 - time + end_hour
      else:
        remaining_hours = end_hour - time
    else:
      remaining_hours = end_hour - time

    if remaining_hours <= 0:
      raise TimeOutsideWorkingHoursError

    # Store selection in Redis
    await db_manager.set_driver_selections(
      driver_id=driver_id,
      selected_time=time,
      remaining_hours=remaining_hours,
    )

    return {
      "driver_id": driver_id,
      "selected_time": time,
      "remaining_hours": remaining_hours,
    }

  async def get_zone_scores(self, driver_id: str) -> list[dict[str, Any]]:
    """Get ranked zones for driver's selected time.

    Args:
        driver_id: Driver identifier.

    Returns:
        List of zone scores.

    """
    # Get driver's selections
    selections = await db_manager.get_driver_selections(driver_id)
    if not selections or selections.get("selected_time") is None:
      raise TimeNotSelectedError

    # Get working hours for city_id
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    # Get zone scores
    return await self.compute_service.get_all_zone_scores(
      driver_id=driver_id,
      start_time=selections["selected_time"],
      remaining_hours=selections["remaining_hours"],
      city_id=preferences["city_id"],
    )

  async def get_best_zone(self, driver_id: str, current_time: int | None = None) -> dict[str, Any]:
    """Get best zone for current or selected time.

    Args:
        driver_id: Driver identifier.
        current_time: Current hour (0-23), or None to use selected time.

    Returns:
        Best zone with score and coordinates.

    """
    # Get driver's preferences
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    # Determine time and remaining hours
    if current_time is not None:
      # Calculate remaining hours from current_time
      start_hour = preferences["start_hour"]
      end_hour = preferences["end_hour"]

      if end_hour < start_hour:  # Wrap-around case
        if current_time >= start_hour:
          remaining_hours = 24 - current_time + end_hour
        else:
          remaining_hours = end_hour - current_time
      else:
        remaining_hours = end_hour - current_time

      if remaining_hours <= 0:
        raise CurrentTimeOutsideWorkingHoursError

      time_to_use = current_time
    else:
      # Use selected time
      selections = await db_manager.get_driver_selections(driver_id)
      if not selections or selections.get("selected_time") is None:
        raise TimeNotSelectedAndNoCurrentTimeError()

      time_to_use = selections["selected_time"]
      remaining_hours = selections["remaining_hours"]

    # Get best zone
    return await self.compute_service.get_best_zone_for_time(
      driver_id=driver_id,
      start_time=time_to_use,
      remaining_hours=remaining_hours,
      city_id=preferences["city_id"],
    )

  async def get_driver_selections(self, driver_id: str) -> dict[str, Any]:
    """Get driver's current selections.

    Args:
        driver_id: Driver identifier.

    Returns:
        Driver selections (time, remaining_hours, zone).

    """
    selections = await db_manager.get_driver_selections(driver_id)

    if selections:
      return {
        "selected_time": selections.get("selected_time"),
        "remaining_hours": selections.get("remaining_hours"),
        "selected_zone": selections.get("selected_zone"),
      }

    return {
      "selected_time": None,
      "remaining_hours": None,
      "selected_zone": None,
    }

  async def start_driving(self, driver_id: str, current_time: int) -> dict[str, Any]:
    """Get optimal zone center for driver starting to drive.

    Args:
        driver_id: Driver identifier.
        current_time: Current hour (0-23).

    Returns:
        Optimal zone with center coordinate.

    """
    preferences = await self.get_working_hours(driver_id)
    if not preferences:
      raise DriverPreferencesNotSetError

    start_hour = preferences["start_hour"]
    end_hour = preferences["end_hour"]

    if end_hour < start_hour:
      if current_time >= start_hour:
        remaining_hours = 24 - current_time + end_hour
      else:
        remaining_hours = end_hour - current_time
    else:
      remaining_hours = end_hour - current_time

    if remaining_hours <= 0:
      raise CurrentTimeOutsideWorkingHoursError

    best_zone = await self.compute_service.get_best_zone_for_time(
      driver_id=driver_id,
      start_time=current_time,
      remaining_hours=remaining_hours,
      city_id=preferences["city_id"],
    )

    # TODO: Get actual hexagons for the zone and calculate center
    # For now, use the single hexagon coordinate as zone center
    zone_center = {
      "lat": best_zone["lat"],
      "lon": best_zone["lon"],
    }

    return {
      "zone_id": best_zone["hexagon_id"],
      "zone_center": zone_center,
      "score": best_zone["score"],
      "current_time": current_time,
      "remaining_hours": remaining_hours,
    }
