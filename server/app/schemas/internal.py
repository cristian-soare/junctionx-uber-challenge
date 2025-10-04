"""Internal schemas for service-to-service communication."""

from datetime import datetime

from pydantic import BaseModel, Field


class Location(BaseModel):
  """Geographic location with lat/lon coordinates."""

  lat: float = Field(..., ge=-90, le=90, description="Latitude")
  lon: float = Field(..., ge=-180, le=180, description="Longitude")
  city_id: int = Field(..., description="City identifier")


class DriverLocation(BaseModel):
  """Real-time driver location data."""

  driver_id: str = Field(..., description="Driver identifier")
  location: Location = Field(..., description="Geographic location")
  timestamp: datetime = Field(..., description="Timestamp of location update")
  status: str = Field(..., description="Driver status (online/offline/engaged)")


class TripRequest(BaseModel):
  """Incoming trip request data."""

  request_id: str = Field(..., description="Unique request identifier")
  rider_id: str = Field(..., description="Rider identifier")
  pickup: Location = Field(..., description="Pickup location")
  drop: Location | None = Field(None, description="Drop-off location")
  timestamp: datetime = Field(..., description="Request timestamp")


class DriverStateRecommendation(BaseModel):
  """Recommendation for driver state change."""

  should_change_state: bool = Field(..., description="Whether driver should change state")
  recommended_state: str | None = Field(None, description="Recommended state to transition to")
  confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
  reasoning: dict[str, float] = Field(..., description="Factor scores contributing to decision")


class ZoneRecommendation(BaseModel):
  """Recommendation for optimal hexagon zone."""

  hexagon_id: str = Field(..., description="H3 hexagon identifier")
  predicted_demand: float = Field(..., ge=0.0, description="Predicted demand score")
  predicted_earnings_per_hour: float = Field(..., ge=0.0, description="Predicted EPH (EUR/hr)")
  distance_km: float = Field(..., ge=0.0, description="Distance from current location (km)")
  confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
