"""API request schemas (input)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.internal import Coordinate


class NewDriverRequest(BaseModel):
  """New driver registration request."""

  driver_id: str = Field(..., description="Unique identifier for the driver")
  city_id: int = Field(..., description="City identifier where the driver operates")
  timestamp: datetime = Field(..., description="Timestamp of registration")


class DriverCoordinateRequest(BaseModel):
  """Driver coordinate update request."""

  driver_id: str = Field(..., description="Driver identifier")
  coordinate: Coordinate = Field(..., description="Current coordinate")
  status: str = Field(..., description="Driver status: online/offline/engaged")
  timestamp: datetime = Field(..., description="Timestamp when coordinate was captured")


class TripRequestInput(BaseModel):
  """Trip request input."""

  rider_id: str = Field(..., description="Rider identifier")
  city_id: int = Field(..., description="City identifier")
  pickup: Coordinate = Field(..., description="Pickup coordinate")
  drop: Coordinate | None = Field(None, description="Drop-off coordinate")
  timestamp: datetime = Field(..., description="Timestamp when trip was requested")


class WeatherUpdateRequest(BaseModel):
  """Weather update request."""

  city_id: int = Field(..., description="City identifier")
  weather: str = Field(..., description="Weather condition: clear/rain/snow")
  temperature: float | None = Field(None, description="Temperature in Celsius")
  timestamp: datetime = Field(..., description="Timestamp of weather observation")


class SurgeUpdateRequest(BaseModel):
  """Surge pricing update request."""

  city_id: int = Field(..., description="City identifier")
  hexagon_id: str = Field(..., description="Hexagon zone identifier")
  surge_multiplier: float = Field(..., ge=1.0, description="Surge multiplier")
  timestamp: datetime = Field(..., description="Timestamp of surge calculation")


class CompletedTripRequest(BaseModel):
  """Completed trip data."""

  driver_id: str = Field(..., description="Driver identifier")
  trip_id: str = Field(..., description="Trip identifier")
  city_id: int = Field(..., description="City identifier")
  pickup_hex: str = Field(..., description="Pickup hexagon")
  drop_hex: str = Field(..., description="Drop-off hexagon")
  distance_km: float = Field(..., ge=0, description="Distance in kilometers")
  duration_mins: int = Field(..., ge=0, description="Duration in minutes")
  earnings: float = Field(..., ge=0, description="Earnings in EUR")
  tips: float = Field(default=0.0, ge=0, description="Tips in EUR")
  surge_multiplier: float = Field(default=1.0, ge=1.0, description="Surge multiplier")
  timestamp: datetime = Field(..., description="Timestamp when trip was completed")


class WorkingHoursRequest(BaseModel):
  """Driver working hours preferences."""

  earliest_start_time: str = Field(
    ...,
    description="Earliest start time in HH:MM format (00:01 to 23:59)",
    pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
  )
  latest_start_time: str = Field(
    ...,
    description="Latest start time in HH:MM format (00:01 to 23:59)",
    pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
  )
  nr_hours: int = Field(..., ge=1, le=24, description="Number of hours the driver intends to work")


class TimeSelectionRequest(BaseModel):
  """Driver time selection."""

  time: int = Field(..., ge=0, le=23, description="Selected hour (0-23)")
