"""API response schemas (output)."""

from pydantic import BaseModel, Field


class TimeScore(BaseModel):
  """Score for a specific start time."""

  time: int = Field(..., description="Start hour (0-23)")
  score: float = Field(..., description="Predicted score")
  remaining_hours: int = Field(..., description="Continuous hours from this start time")


class OptimalTimeResponse(BaseModel):
  """Optimal start time recommendation."""

  optimal_time: int = Field(..., description="Best start hour (0-23)")
  score: float = Field(..., description="Score for optimal time")
  remaining_hours: int = Field(..., description="Continuous hours from optimal time")


class TimeScoresResponse(BaseModel):
  """All time scores."""

  scores: list[TimeScore] = Field(..., description="Scores for all possible start times")


class ZoneScore(BaseModel):
  """Score for a specific zone."""

  hexagon_id: str = Field(..., description="H3 hexagon identifier")
  score: float = Field(..., description="Predicted score")
  lat: float = Field(..., description="Zone center latitude")
  lon: float = Field(..., description="Zone center longitude")
  remaining_hours: int = Field(..., description="Remaining hours used in calculation")


class ZoneScoresResponse(BaseModel):
  """Ranked zones by score."""

  zones: list[ZoneScore] = Field(..., description="Zones ranked by score (descending)")


class BestZoneResponse(BaseModel):
  """Best zone for current/selected time."""

  hexagon_id: str = Field(..., description="Best zone hexagon ID")
  score: float = Field(..., description="Zone score")
  lat: float = Field(..., description="Zone center latitude")
  lon: float = Field(..., description="Zone center longitude")
  remaining_hours: int = Field(..., description="Remaining hours from selected time")


class DriverSelectionsResponse(BaseModel):
  """Current driver selections."""

  selected_time: int | None = Field(None, description="Selected start hour")
  remaining_hours: int | None = Field(None, description="Remaining hours from selected time")
  selected_zone: str | None = Field(None, description="Selected zone hexagon ID")


class Coordinate(BaseModel):
  """Geographic coordinate."""

  lat: float = Field(..., description="Latitude")
  lon: float = Field(..., description="Longitude")


class StartDrivingResponse(BaseModel):
  """Response when driver starts driving."""

  zone_id: str = Field(..., description="Optimal zone ID")
  zone_center: Coordinate = Field(..., description="Center coordinate of optimal zone")
  score: float = Field(..., description="Zone score")
  current_time: int = Field(..., description="Current hour (0-23)")
  remaining_hours: int = Field(..., description="Remaining working hours")
