"""API response schemas (output)."""

from typing import Any

from pydantic import BaseModel, Field


class DriverRecommendationOutput(BaseModel):
  """Driver recommendation response."""

  driver_id: str = Field(..., description="Driver identifier")
  timestamp: str = Field(..., description="Recommendation timestamp")
  state_recommendation: dict[str, Any] = Field(..., description="State change recommendation")
  zone_recommendation: dict[str, Any] = Field(..., description="Optimal zone recommendation")
