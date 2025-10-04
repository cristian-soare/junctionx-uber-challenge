"""Schemas package for JunctionX Uber Challenge."""

from app.schemas.input import (
  CompletedTripRequest,
  DriverLocationRequest,
  DriverRecommendationRequest,
  SurgeUpdateRequest,
  TripRequestInput,
  WeatherUpdateRequest,
)
from app.schemas.internal import (
  DriverLocation,
  DriverStateRecommendation,
  Location,
  TripRequest,
  ZoneRecommendation,
)
from app.schemas.output import DriverRecommendationOutput

__all__ = [
  # Input
  "DriverLocationRequest",
  "DriverRecommendationRequest",
  "TripRequestInput",
  "WeatherUpdateRequest",
  "SurgeUpdateRequest",
  "CompletedTripRequest",
  # Internal
  "Location",
  "DriverLocation",
  "TripRequest",
  "DriverStateRecommendation",
  "ZoneRecommendation",
  # Output
  "DriverRecommendationOutput",
]
