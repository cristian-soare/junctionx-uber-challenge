"""API endpoints for driver optimization and real-time data."""

from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.schemas.input import (
  CompletedTripRequest,
  DriverLocationRequest,
  DriverRecommendationRequest,
  SurgeUpdateRequest,
  TripRequestInput,
  WeatherUpdateRequest,
)
from app.service import DataService

router = APIRouter()
data_service = DataService()


@router.post(
  "/drivers/location",
  status_code=status.HTTP_201_CREATED,
  summary="Update driver location",
  description="Store real-time driver location and status in Redis and SQLite",
  response_description="Location update confirmation with timestamp",
  tags=["drivers"],
)
async def update_driver_location(request: DriverLocationRequest) -> dict[str, Any]:
  """
  Update driver location in real-time.

  Stores driver's current location, status, and timestamp in:
  - Redis: For fast real-time queries (1h TTL)
  - SQLite: For historical state change analysis

  Args:
    request: Driver location update with ID, location (lat/lon/city), and status

  Returns:
    Success response with stored driver location data

  Raises:
    HTTPException: 500 if storage fails
  """
  try:
    result = await data_service.store_driver_location(
      request.driver_id,
      request.location,
      request.status,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store driver location: {e!s}",
    ) from e


@router.post(
  "/drivers/recommendation",
  status_code=status.HTTP_200_OK,
  summary="Get driver recommendation",
  description="ML-based recommendation for driver state change and optimal zone",
  response_description="State change recommendation and optimal hexagon zone",
  tags=["drivers", "ml-inference"],
)
async def get_driver_recommendation(request: DriverRecommendationRequest) -> dict[str, Any]:
  """
  Get ML-based recommendation for driver optimization.

  Uses ML inference to determine:
  1. Should driver change state (offline → idle, idle → online, etc.)
  2. Which hexagon zone to move to for optimal earnings

  Input features considered:
  - Current driver status and location
  - Weather conditions
  - Surge pricing in area
  - Time since last state change
  - Historical ride patterns and earnings
  - Current demand heatmap

  Args:
    request: Driver ID, current state, and location

  Returns:
    Success response with state_recommendation and zone_recommendation

  Raises:
    HTTPException: 500 if inference fails
  """
  try:
    result = await data_service.get_driver_recommendation(
      request.driver_id,
      request.current_state,
      request.current_location,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get driver recommendation: {e!s}",
    ) from e


@router.post(
  "/trips/request",
  status_code=status.HTTP_201_CREATED,
  summary="Create trip request",
  description="Store trip request for real-time demand tracking and historical analysis",
  response_description="Trip request confirmation with ID and timestamp",
  tags=["trips"],
)
async def create_trip_request(request: TripRequestInput) -> dict[str, Any]:
  """
  Store trip request for demand analysis.

  Stores in:
  - Redis: Recent requests (last hour) for real-time demand tracking
  - SQLite: Historical demand patterns for ML training

  Args:
    request: Rider ID, pickup location, and optional drop-off location

  Returns:
    Success response with request_id and stored trip data

  Raises:
    HTTPException: 500 if storage fails
  """
  try:
    result = await data_service.store_trip_request(
      request.rider_id,
      request.pickup,
      request.drop,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to process trip request: {e!s}",
    ) from e


@router.post(
  "/weather/update",
  status_code=status.HTTP_201_CREATED,
  summary="Update weather",
  description="Store current weather conditions for a city",
  response_description="Weather update confirmation",
  tags=["context"],
)
async def update_weather(request: WeatherUpdateRequest) -> dict[str, Any]:
  """
  Update weather conditions for a city.

  Stores in:
  - Redis: Current weather (30min TTL) for real-time ML inference
  - SQLite: Historical weather patterns for demand analysis

  Args:
    request: City ID, weather condition, and optional temperature

  Returns:
    Success response with stored weather data

  Raises:
    HTTPException: 500 if storage fails
  """
  try:
    result = await data_service.store_weather_update(
      request.city_id,
      request.weather,
      request.temperature,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store weather update: {e!s}",
    ) from e


@router.post(
  "/surge/update",
  status_code=status.HTTP_201_CREATED,
  summary="Update surge pricing",
  description="Store surge multiplier for a hexagon zone",
  response_description="Surge update confirmation",
  tags=["context"],
)
async def update_surge(request: SurgeUpdateRequest) -> dict[str, Any]:
  """
  Update surge pricing for a zone.

  Stores in:
  - Redis: Current surge (5min TTL) for real-time pricing decisions
  - SQLite: Historical surge patterns for analysis

  Args:
    request: City ID, hexagon ID, and surge multiplier

  Returns:
    Success response with stored surge data

  Raises:
    HTTPException: 500 if storage fails
  """
  try:
    result = await data_service.store_surge_update(
      request.city_id,
      request.hexagon_id,
      request.surge_multiplier,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store surge update: {e!s}",
    ) from e


@router.post(
  "/trips/completed",
  status_code=status.HTTP_201_CREATED,
  summary="Store completed trip",
  description="Store completed trip data for driver performance analysis",
  response_description="Trip storage confirmation",
  tags=["trips"],
)
async def store_completed_trip(request: CompletedTripRequest) -> dict[str, Any]:
  """
  Store completed trip for historical analysis.

  Stores in SQLite for:
  - Driver performance tracking per zone
  - Personalized ML recommendations
  - Earnings history analysis

  Args:
    request: Complete trip data (driver, trip_id, zones, earnings, etc.)

  Returns:
    Success response with trip_id and timestamp

  Raises:
    HTTPException: 500 if storage fails
  """
  try:
    result = await data_service.store_completed_trip(request)
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store completed trip: {e!s}",
    ) from e


@router.get(
  "/drivers/active/{city_id}",
  status_code=status.HTTP_200_OK,
  summary="Get active drivers",
  description="Retrieve all active drivers in a city from Redis",
  response_description="List of active driver locations",
  tags=["drivers"],
)
async def get_active_drivers(
  city_id: int = Path(..., description="City identifier", ge=1)
) -> dict[str, Any]:
  """
  Get all active drivers in a city.

  Queries Redis for drivers with non-expired location data.

  Args:
    city_id: City identifier

  Returns:
    Success response with list of active driver locations

  Raises:
    HTTPException: 500 if query fails
  """
  try:
    drivers = await data_service.get_active_drivers(city_id)
    return {"status": "success", "data": drivers}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get active drivers: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/state-history",
  status_code=status.HTTP_200_OK,
  summary="Get driver state history",
  description="Retrieve driver's state change history from SQLite",
  response_description="List of state changes with timestamps",
  tags=["drivers"],
)
async def get_driver_state_history(
  driver_id: str,
  hours: int = Query(24, description="Hours to look back", ge=1, le=168),
) -> dict[str, Any]:
  """
  Get driver's state change history.

  Queries SQLite for historical state transitions.
  Used to calculate time_in_state for ML features.

  Args:
    driver_id: Driver identifier
    hours: Number of hours to look back (default: 24, max: 168/1 week)

  Returns:
    Success response with list of state changes

  Raises:
    HTTPException: 500 if query fails
  """
  try:
    history = await data_service.get_driver_state_history(driver_id, hours)
    return {"status": "success", "data": history}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get state history: {e!s}",
    ) from e


@router.get(
  "/trips/recent",
  status_code=status.HTTP_200_OK,
  summary="Get recent trip requests",
  description="Retrieve recent trip requests from Redis (last hour)",
  response_description="List of recent trip requests",
  tags=["trips"],
)
async def get_recent_requests(
  limit: int = Query(100, description="Maximum number of requests", ge=1, le=1000)
) -> dict[str, Any]:
  """
  Get recent trip requests.

  Queries Redis sorted set for requests from the last hour.
  Used for real-time demand analysis.

  Args:
    limit: Maximum number of requests to return (default: 100, max: 1000)

  Returns:
    Success response with list of recent requests

  Raises:
    HTTPException: 500 if query fails
  """
  try:
    requests = await data_service.get_recent_requests(limit)
    return {"status": "success", "data": requests}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get recent requests: {e!s}",
    ) from e
