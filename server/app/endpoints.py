"""API endpoints for driver optimization and real-time data."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.input import (
  CompletedTripRequest,
  DriverCoordinateRequest,
  NewDriverRequest,
  SurgeUpdateRequest,
  TimeSelectionRequest,
  TripRequestInput,
  WeatherUpdateRequest,
  WorkingHoursRequest,
)
from app.schemas.output import (
  BestZoneResponse,
  DriverSelectionsResponse,
  OptimalTimeResponse,
  StartDrivingResponse,
  TimeScoresResponse,
  ZoneScoresResponse,
)
from app.service import DataService

router = APIRouter()
data_service = DataService()


@router.post(
  "/drivers/register",
  status_code=status.HTTP_201_CREATED,
  summary="Register new driver",
  description="Register a new driver in the system",
  response_description="Driver registration confirmation",
  tags=["drivers"],
)
async def register_driver(request: NewDriverRequest) -> dict[str, Any]:
  """Register a new driver.

  Args:
    request: Driver ID, city ID, and timestamp

  Returns:
    Success response with driver_id and city_id

  Raises:
    HTTPException: 500 if registration fails

  """
  try:
    result = await data_service.register_driver(
      request.driver_id, request.city_id, request.timestamp
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to register driver: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}",
  status_code=status.HTTP_200_OK,
  summary="Get driver",
  description="Get driver information by ID",
  tags=["drivers"],
)
async def get_driver(driver_id: str) -> dict[str, Any]:
  """Get driver information.

  Args:
    driver_id: Driver identifier

  Returns:
    Success response with driver data

  Raises:
    HTTPException: 404 if driver not found

  """
  try:
    result = await data_service.get_driver(driver_id)
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Failed to get driver: {e!s}",
    ) from e


@router.put(
  "/drivers/{driver_id}/city",
  status_code=status.HTTP_200_OK,
  summary="Update driver city",
  description="Update the city of an existing driver",
  tags=["drivers"],
)
async def update_driver_city(driver_id: str, city_id: int) -> dict[str, Any]:
  """Update the city of an existing driver.

  Args:
    driver_id: Driver identifier.
    city_id: New city identifier.

  Returns:
    Success response with updated driver data.

  Raises:
    HTTPException: 404 if driver not found

  """
  try:
    result = await data_service.update_driver_city(driver_id, city_id)
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Failed to update driver city: {e!s}",
    ) from e


@router.post(
  "/drivers/coordinates",
  status_code=status.HTTP_201_CREATED,
  summary="Update driver coordinates",
  description="Store real-time driver coordinates and status in Redis and SQLite",
  response_description="Coordinate update confirmation with timestamp",
  tags=["drivers"],
)
async def update_driver_coordinates(request: DriverCoordinateRequest) -> dict[str, Any]:
  """Update driver coordinates in real-time.

  Stores driver's current coordinates, status, and timestamp in:
  - Redis: For fast real-time queries (1h TTL)
  - SQLite: For historical state change analysis

  Args:
    request: Driver coordinate update with ID, coordinates (lat/lon), and status

  Returns:
    Success response with stored driver coordinate data

  Raises:
    HTTPException: 500 if storage fails

  """
  try:
    result = await data_service.store_driver_coordinates(
      request.driver_id,
      request.coordinate,
      request.status,
      request.timestamp,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store driver coordinates: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/coordinates",
  status_code=status.HTTP_200_OK,
  summary="Get driver coordinates",
  description="Get real-time driver coordinates from Redis",
  response_description="Driver coordinates with status and timestamp",
  tags=["drivers"],
)
async def get_driver_coordinates(driver_id: str) -> dict[str, Any]:
  """Get driver coordinates from Redis.

  Args:
    driver_id: Driver identifier

  Returns:
    Success response with driver coordinates, status, and timestamp

  Raises:
    HTTPException: 404 if driver coordinates not found

  """
  try:
    result = await data_service.get_driver_coordinates(driver_id)
    if not result:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Coordinates not found for driver {driver_id}",
      )
    return {"status": "success", "data": result}
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get driver coordinates: {e!s}",
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
  """Store trip request for demand analysis.

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
      request.city_id,
      request.pickup,
      request.drop,
      request.timestamp,
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
  """Update weather conditions for a city.

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
      request.timestamp,
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
  """Update surge pricing for a zone.

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
      request.timestamp,
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
  """Store completed trip for historical analysis.

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
  """Get driver's state change history.

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
  limit: int = Query(100, description="Maximum number of requests", ge=1, le=1000),
) -> dict[str, Any]:
  """Get recent trip requests.

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


@router.post(
  "/drivers/{driver_id}/preferences",
  status_code=status.HTTP_201_CREATED,
  summary="Set driver working hours",
  description="Store driver's preferred working hours",
  response_description="Working hours confirmation",
  tags=["drivers", "preferences"],
)
async def set_working_hours(driver_id: str, request: WorkingHoursRequest) -> dict[str, Any]:
  """Set driver's working hours preferences.

  Args:
    driver_id: Driver identifier
    request: Working hours (earliest_start_time, latest_start_time, nr_hours)

  Returns:
    Success response with stored preferences

  Raises:
    HTTPException: 500 if storage fails

  """
  try:
    result = await data_service.store_working_hours(
      driver_id=driver_id,
      earliest_start_time=request.earliest_start_time,
      latest_start_time=request.latest_start_time,
      nr_hours=request.nr_hours,
    )
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to store working hours: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/preferences",
  status_code=status.HTTP_200_OK,
  summary="Get driver working hours",
  description="Retrieve driver's working hours preferences",
  response_description="Driver working hours preferences",
  tags=["drivers", "preferences"],
)
async def get_working_hours(driver_id: str) -> dict[str, Any]:
  """Get driver's working hours preferences.

  Args:
    driver_id: Driver identifier

  Returns:
    Success response with working hours preferences

  Raises:
    HTTPException: 500 if query fails

  """
  try:
    result = await data_service.get_working_hours(driver_id)
    return {"status": "success", "data": result}
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get working hours: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/recommendations/optimal-time",
  status_code=status.HTTP_200_OK,
  summary="Get optimal start time",
  description="Get best start time from driver's working hours range",
  response_description="Optimal time with score and remaining hours",
  response_model=OptimalTimeResponse,
  tags=["drivers", "recommendations"],
)
async def get_optimal_time(driver_id: str) -> OptimalTimeResponse:
  """Get optimal start time for driver.

  Computes scores for all possible start times within working hours
  and returns the time with highest score.

  Args:
    driver_id: Driver identifier

  Returns:
    Optimal time with score and remaining hours

  Raises:
    HTTPException: 400 if no preferences set, 500 if computation fails

  """
  try:
    result = await data_service.get_optimal_time(driver_id)
    return OptimalTimeResponse(**result)
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get optimal time: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/recommendations/time-scores",
  status_code=status.HTTP_200_OK,
  summary="Get all time scores",
  description="Get scores for all possible start times in working hours range",
  response_description="List of time scores",
  response_model=TimeScoresResponse,
  tags=["drivers", "recommendations"],
)
async def get_time_scores(driver_id: str) -> TimeScoresResponse:
  """Get scores for all possible start times.

  Returns score for each hour in driver's working hours range,
  with corresponding remaining hours.

  Args:
    driver_id: Driver identifier

  Returns:
    List of time scores sorted by time

  Raises:
    HTTPException: 400 if no preferences set, 500 if computation fails

  """
  try:
    scores = await data_service.get_all_time_scores(driver_id)
    return TimeScoresResponse(scores=scores)
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get time scores: {e!s}",
    ) from e


@router.post(
  "/drivers/{driver_id}/selections/time",
  status_code=status.HTTP_201_CREATED,
  summary="Select start time",
  description="Select a start time and store it with calculated remaining hours",
  response_description="Selection confirmation with remaining hours",
  tags=["drivers", "selections"],
)
async def select_time(driver_id: str, request: TimeSelectionRequest) -> dict[str, Any]:
  """Select a start time.

  Validates time is within working hours and stores it with
  calculated remaining hours in Redis.

  Args:
    driver_id: Driver identifier
    request: Selected time

  Returns:
    Success response with selected time and remaining hours

  Raises:
    HTTPException: 400 if invalid time or no preferences set, 500 if storage fails

  """
  try:
    result = await data_service.select_time(driver_id, request.time)
    return {"status": "success", "data": result}
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to select time: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/recommendations/zone-scores",
  status_code=status.HTTP_200_OK,
  summary="Get zone scores for selected time",
  description="Get all zones ranked by score for driver's selected time",
  response_description="List of zones ranked by score (descending)",
  response_model=ZoneScoresResponse,
  tags=["drivers", "recommendations"],
)
async def get_zone_scores(driver_id: str) -> ZoneScoresResponse:
  """Get ranked zones for selected time.

  Returns all zones sorted by score (descending) for the
  driver's previously selected time.

  Args:
    driver_id: Driver identifier

  Returns:
    List of zones with scores and coordinates

  Raises:
    HTTPException: 400 if no time selected, 500 if computation fails

  """
  try:
    zones = await data_service.get_zone_scores(driver_id)
    return ZoneScoresResponse(zones=zones)
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get zone scores: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/recommendations/best-zone",
  status_code=status.HTTP_200_OK,
  summary="Get best zone",
  description="Get best zone for current time or selected time",
  response_description="Best zone with score and coordinates",
  response_model=BestZoneResponse,
  tags=["drivers", "recommendations"],
)
async def get_best_zone(
  driver_id: str,
  current_time: int | None = Query(
    None, description="Current hour (0-23), or None for selected time", ge=0, le=23
  ),
) -> BestZoneResponse:
  """Get best zone for time.

  If current_time provided, calculates remaining hours and returns
  best zone for that time. Otherwise uses driver's selected time.

  Args:
    driver_id: Driver identifier
    current_time: Optional current hour (0-23)

  Returns:
    Best zone with score and coordinates

  Raises:
    HTTPException: 400 if invalid time or no selection, 500 if computation fails

  """
  try:
    zone = await data_service.get_best_zone(driver_id, current_time)
    return BestZoneResponse(**zone)
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get best zone: {e!s}",
    ) from e


@router.get(
  "/drivers/{driver_id}/selections",
  status_code=status.HTTP_200_OK,
  summary="Get driver selections",
  description="Get driver's current time and zone selections",
  response_description="Driver selections",
  response_model=DriverSelectionsResponse,
  tags=["drivers", "selections"],
)
async def get_selections(driver_id: str) -> DriverSelectionsResponse:
  """Get driver's current selections.

  Returns driver's selected time, remaining hours, and selected zone
  from Redis cache.

  Args:
    driver_id: Driver identifier

  Returns:
    Driver selections (may be null if not set)

  Raises:
    HTTPException: 500 if query fails

  """
  try:
    selections = await data_service.get_driver_selections(driver_id)
    return DriverSelectionsResponse(**selections)
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to get selections: {e!s}",
    ) from e


@router.post(
  "/drivers/{driver_id}/start-driving",
  status_code=status.HTTP_200_OK,
  summary="Start driving",
  description="Get optimal zone center when driver starts driving",
  response_description="Optimal zone with center coordinate",
  response_model=StartDrivingResponse,
  tags=["drivers", "actions"],
)
async def start_driving(
  driver_id: str,
  current_time: int = Query(..., description="Current hour (0-23)", ge=0, le=23),
) -> StartDrivingResponse:
  """Get optimal zone center when driver starts driving.

  Calculates remaining hours from working hours preferences,
  finds best zone for current time, and returns zone center coordinate.

  Args:
    driver_id: Driver identifier
    current_time: Current hour (0-23)

  Returns:
    Optimal zone with center coordinate and score

  Raises:
    HTTPException: 400 if no preferences or invalid time, 500 if computation fails

  """
  try:
    result = await data_service.start_driving(driver_id, current_time)
    return StartDrivingResponse(**result)
  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=str(e),
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to start driving: {e!s}",
    ) from e


# AI Agent endpoints
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.ai_agent import AIAgentService, ChatMessage

ai_agent_service = AIAgentService()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    chat_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    timestamp: str


class SuggestionsResponse(BaseModel):
    """Proactive suggestions response model."""
    suggestions: List[str]


@router.post(
    "/ai/chat/{driver_id}",
    response_model=ChatResponse,
    summary="Chat with AI Assistant",
    description="Send a message to the AI assistant and get driving advice",
    tags=["ai-agent"],
)
async def chat_with_ai(
    driver_id: str = Path(..., description="Driver ID"),
    request: ChatRequest = ...,
) -> ChatResponse:
    """Chat with the AI assistant for driving advice.
    
    Args:
        driver_id: Driver identifier
        request: Chat message and history
        
    Returns:
        AI response with timestamp
        
    Raises:
        HTTPException: 500 if AI service fails
    """
    try:
        response_text = await ai_agent_service.chat(
            driver_id=driver_id,
            message=request.message,
            chat_history=request.chat_history
        )
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI chat failed: {str(e)}"
        ) from e


@router.get(
    "/ai/suggestions/{driver_id}",
    response_model=SuggestionsResponse,
    summary="Get proactive suggestions",
    description="Get AI-generated proactive suggestions based on current conditions",
    tags=["ai-agent"],
)
async def get_proactive_suggestions(
    driver_id: str = Path(..., description="Driver ID")
) -> SuggestionsResponse:
    """Get proactive AI suggestions for the driver.
    
    Args:
        driver_id: Driver identifier
        
    Returns:
        List of proactive suggestions
        
    Raises:
        HTTPException: 500 if AI service fails
    """
    try:
        suggestions = await ai_agent_service.get_proactive_suggestions(driver_id)
        
        return SuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        ) from e


@router.get(
    "/ai/wellness/{driver_id}",
    summary="Get wellness reminder",
    description="Get wellness reminder based on driving time",
    tags=["ai-agent"],
)
async def get_wellness_reminder(
    driver_id: str = Path(..., description="Driver ID"),
    hours_driven: float = Query(..., description="Number of hours driven", ge=0, le=24)
) -> dict[str, Any]:
    """Get wellness reminder based on driving time.
    
    Args:
        driver_id: Driver identifier
        hours_driven: Number of hours the driver has been driving
        
    Returns:
        Wellness reminder message if applicable
        
    Raises:
        HTTPException: 500 if AI service fails
    """
    try:
        reminder = await ai_agent_service.generate_wellness_reminder(driver_id, hours_driven)
        
        return {
            "wellness_reminder": reminder,
            "should_take_break": hours_driven >= 4.5,
            "hours_driven": hours_driven
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wellness reminder: {str(e)}"
        ) from e
