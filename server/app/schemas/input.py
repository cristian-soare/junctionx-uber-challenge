"""API request schemas (input)."""

from datetime import datetime

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
  """Geographic coordinate."""

  lat: float = Field(..., ge=-90, le=90, description="Latitude")
  lon: float = Field(..., ge=-180, le=180, description="Longitude")


class Location(BaseModel):
  """Geographic location with coordinate and city."""

  coordinate: Coordinate = Field(..., description="Geographic coordinate")
  city_id: int = Field(..., description="City identifier")

  @property
  def lat(self) -> float:
    """Get latitude from coordinate."""
    return self.coordinate.lat

  @property
  def lon(self) -> float:
    """Get longitude from coordinate."""
    return self.coordinate.lon


class DriverLocationRequest(BaseModel):
  """Driver location update request."""

  driver_id: str = Field(..., description="Driver identifier")
  location: Location = Field(..., description="Current location")
  status: str = Field(..., description="Driver status: online/offline/engaged")
  timestamp: datetime = Field(..., description="Timestamp when location was captured")


class TripRequestInput(BaseModel):
  """Trip request input."""

  rider_id: str = Field(..., description="Rider identifier")
  pickup: Location = Field(..., description="Pickup location")
  drop: Location | None = Field(None, description="Drop-off location")
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

  start_hour: int = Field(..., ge=0, le=23, description="Start hour (0-23)")
  end_hour: int = Field(..., ge=0, le=23, description="End hour (0-23)")
  city_id: int = Field(..., description="City identifier")


class TimeSelectionRequest(BaseModel):
  """Driver time selection."""

  time: int = Field(..., ge=0, le=23, description="Selected hour (0-23)")
