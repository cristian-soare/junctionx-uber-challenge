"""Internal schemas for service-to-service communication."""

from datetime import datetime

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
  """Geographic coordinate with latitude and longitude."""

  lat: float = Field(..., ge=-90, le=90, description="Latitude")
  lon: float = Field(..., ge=-180, le=180, description="Longitude")


class Hexagon(BaseModel):
  """Hexagon with ID and coordinate."""

  hex_id: str = Field(..., description="H3 hexagon identifier (9 characters)")
  coordinate: Coordinate = Field(..., description="Center coordinate of hexagon")


class Zone(BaseModel):
  """Zone containing multiple hexagons."""

  zone_id: str = Field(..., description="Zone identifier")
  hexagons: list[Hexagon] = Field(..., description="List of hexagons in zone")
  center: Coordinate = Field(..., description="Center coordinate of zone")


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


class ZoneRecommendation(BaseModel):
  """Recommendation for optimal hexagon zone."""

  hexagon_id: str = Field(..., description="H3 hexagon identifier")
  predicted_demand: float = Field(..., ge=0.0, description="Predicted demand score")
  predicted_earnings_per_hour: float = Field(..., ge=0.0, description="Predicted EPH (EUR/hr)")
  distance_km: float = Field(..., ge=0.0, description="Distance from current location (km)")
  confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
  lat: float = Field(..., ge=-90, le=90, description="Zone center latitude")
  lon: float = Field(..., ge=-180, le=180, description="Zone center longitude")
