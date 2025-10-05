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

  cluster_id: str = Field(..., description="Cluster identifier")
  score: float = Field(..., description="Predicted score")
  expected_earnings: float = Field(..., description="Expected total earnings")
  expected_hourly_rate: float = Field(..., description="Expected earnings per hour")
  lat: float = Field(..., description="Zone center latitude")
  lon: float = Field(..., description="Zone center longitude")
  lat_min: float = Field(..., description="Zone minimum latitude (bounding box)")
  lat_max: float = Field(..., description="Zone maximum latitude (bounding box)")
  lon_min: float = Field(..., description="Zone minimum longitude (bounding box)")
  lon_max: float = Field(..., description="Zone maximum longitude (bounding box)")
  work_hours: int = Field(..., description="Work hours used in calculation")
  remaining_hours: int = Field(..., description="Remaining hours used in calculation")
  path_length: int = Field(..., description="Length of optimal path")


class ZoneScoresResponse(BaseModel):
  """Ranked zones by score."""

  zones: list[ZoneScore] = Field(..., description="Zones ranked by score (descending)")


class BestZoneResponse(BaseModel):
  """Best zone for current/selected time."""

  cluster_id: str | None = Field(None, description="Best zone cluster ID")
  score: float = Field(..., description="Zone score")
  expected_earnings: float = Field(..., description="Expected total earnings")
  expected_hourly_rate: float = Field(..., description="Expected earnings per hour")
  lat: float = Field(..., description="Zone center latitude")
  lon: float = Field(..., description="Zone center longitude")
  lat_min: float = Field(..., description="Zone minimum latitude (bounding box)")
  lat_max: float = Field(..., description="Zone maximum latitude (bounding box)")
  lon_min: float = Field(..., description="Zone minimum longitude (bounding box)")
  lon_max: float = Field(..., description="Zone maximum longitude (bounding box)")
  work_hours: int = Field(..., description="Work hours used in calculation")
  path_length: int | None = Field(None, description="Length of optimal path")
  optimal_path: list[str] | None = Field(None, description="Optimal path through clusters")
  error: str | None = Field(None, description="Error message if any")


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
  zone_corners: list[Coordinate] = Field(..., description="Corner coordinates of hexagon zone")
