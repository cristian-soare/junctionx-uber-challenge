"""API request schemas (input)."""

from typing import Any

from pydantic import BaseModel, Field


class Location(BaseModel):
  """Geographic location with lat/lon coordinates."""

  lat: float = Field(..., ge=-90, le=90, description="Latitude")
  lon: float = Field(..., ge=-180, le=180, description="Longitude")
  city_id: int = Field(..., description="City identifier")


class DriverLocationRequest(BaseModel):
  """Driver location update request."""

  driver_id: str = Field(..., description="Driver identifier")
  location: Location = Field(..., description="Current location")
  status: str = Field(..., description="Driver status: online/offline/engaged")


class DriverRecommendationRequest(BaseModel):
  """Request for driver recommendation."""

  driver_id: str = Field(..., description="Driver identifier")
  current_state: str = Field(..., description="Current state: offline/idle/engaged")
  current_location: Location = Field(..., description="Current location")


class TripRequestInput(BaseModel):
  """Trip request input."""

  rider_id: str = Field(..., description="Rider identifier")
  pickup: Location = Field(..., description="Pickup location")
  drop: Location | None = Field(None, description="Drop-off location")


class WeatherUpdateRequest(BaseModel):
  """Weather update request."""

  city_id: int = Field(..., description="City identifier")
  weather: str = Field(..., description="Weather condition: clear/rain/snow")
  temperature: float | None = Field(None, description="Temperature in Celsius")


class SurgeUpdateRequest(BaseModel):
  """Surge pricing update request."""

  city_id: int = Field(..., description="City identifier")
  hexagon_id: str = Field(..., description="Hexagon zone identifier")
  surge_multiplier: float = Field(..., ge=1.0, description="Surge multiplier")


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
