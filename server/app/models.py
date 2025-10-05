"""SQLAlchemy models for historical data storage."""

from datetime import datetime

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DriverStateHistory(Base):
  """Historical record of driver state changes."""

  __tablename__ = "driver_state_history"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  driver_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
  state: Mapped[str] = mapped_column(String(20), nullable=False)
  city_id: Mapped[int] = mapped_column(Integer, nullable=False)
  lat: Mapped[float] = mapped_column(Float, nullable=False)
  lon: Mapped[float] = mapped_column(Float, nullable=False)
  timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)


class CompletedTrip(Base):
  """Historical record of completed trips."""

  __tablename__ = "completed_trips"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  driver_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
  trip_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  city_id: Mapped[int] = mapped_column(Integer, nullable=False)
  pickup_hex: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
  drop_hex: Mapped[str] = mapped_column(String(20), nullable=False)
  distance_km: Mapped[float] = mapped_column(Float, nullable=False)
  duration_mins: Mapped[int] = mapped_column(Integer, nullable=False)
  earnings: Mapped[float] = mapped_column(Float, nullable=False)
  tips: Mapped[float] = mapped_column(Float, default=0.0)
  surge_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
  timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)


class WeatherHistory(Base):
  """Historical weather data."""

  __tablename__ = "weather_history"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  city_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
  weather: Mapped[str] = mapped_column(String(20), nullable=False)
  temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
  timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)


class TripRequestHistory(Base):
  """Historical trip requests for demand analysis."""

  __tablename__ = "trip_request_history"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  rider_id: Mapped[str] = mapped_column(String(50), nullable=False)
  city_id: Mapped[int] = mapped_column(Integer, nullable=False)
  pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
  pickup_lon: Mapped[float] = mapped_column(Float, nullable=False)
  pickup_hex: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
  timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)


class SurgeHistory(Base):
  """Historical surge pricing data."""

  __tablename__ = "surge_history"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  city_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
  hexagon_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
  surge_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
  timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)


class Driver(Base):
  __tablename__ = "drivers"

  driver_id: Mapped[str] = mapped_column(String(50), primary_key=True)
  city_id: Mapped[int] = mapped_column(Integer, nullable=False)
  created_at: Mapped[datetime] = mapped_column(nullable=False)
  updated_at: Mapped[datetime] = mapped_column(nullable=False)


class DriverPreferences(Base):
  """Driver working hours preferences."""

  __tablename__ = "driver_preferences"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  driver_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
  earliest_start_time: Mapped[str] = mapped_column(String(5), nullable=False)
  latest_start_time: Mapped[str] = mapped_column(String(5), nullable=False)
  nr_hours: Mapped[int] = mapped_column(Integer, nullable=False)
  updated_at: Mapped[datetime] = mapped_column(nullable=False, index=True)


class DrivingSession(Base):
  """Track driver's active driving sessions for hours calculation."""

  __tablename__ = "driving_sessions"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  driver_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
  session_start: Mapped[datetime] = mapped_column(nullable=False, index=True)
  session_end: Mapped[datetime | None] = mapped_column(nullable=True)
  hours_driven: Mapped[float | None] = mapped_column(Float, nullable=True)
  is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
