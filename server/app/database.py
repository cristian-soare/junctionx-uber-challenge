"""Database connections and helpers for Redis and SQLite."""

import json
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
  """Base class for SQLAlchemy models."""

  pass


class DatabaseManager:
  """Manages Redis and SQLite connections."""

  def __init__(self) -> None:
    """Initialize database connections."""
    db_path = Path(__file__).parent.parent / "data" / "uber.db"
    db_path.parent.mkdir(exist_ok=True)
    self.sqlite_url = f"sqlite+aiosqlite:///{db_path}"
    self.engine = create_async_engine(self.sqlite_url, echo=False)
    self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    self.redis_client: redis.Redis | None = None

  async def init_redis(self) -> None:
    """Initialize Redis connection."""
    self.redis_client = await redis.from_url(
      "redis://localhost:6379",
      encoding="utf-8",
      decode_responses=True,
    )

  async def close_redis(self) -> None:
    """Close Redis connection."""
    if self.redis_client:
      await self.redis_client.close()

  async def init_sqlite(self) -> None:
    """Initialize SQLite tables."""
    async with self.engine.begin() as conn:
      await conn.run_sync(Base.metadata.create_all)

  @asynccontextmanager
  async def get_session(self):
    """Get SQLite async session."""
    async with self.async_session() as session:
      yield session

  # Redis helpers for real-time data
  async def set_driver_location(
    self,
    driver_id: str,
    lat: float,
    lon: float,
    status: str,
    timestamp: str,
  ) -> None:
    """Store driver location in Redis with TTL."""
    if not self.redis_client:
      return

    key = f"driver:location:{driver_id}"
    data = {
      "lat": lat,
      "lon": lon,
      "status": status,
      "timestamp": timestamp,
    }
    await self.redis_client.setex(
      key,
      timedelta(hours=1),  # Auto-expire after 1 hour
      json.dumps(data),
    )

  async def get_driver_location(self, driver_id: str) -> dict[str, Any] | None:
    """Get driver location from Redis."""
    if not self.redis_client:
      return None

    key = f"driver:location:{driver_id}"
    data = await self.redis_client.get(key)
    return json.loads(data) if data else None

  async def set_weather(self, city_id: int, weather: str, temperature: float | None) -> None:
    """Store current weather in Redis with TTL."""
    if not self.redis_client:
      return

    key = f"weather:city:{city_id}"
    data = {
      "weather": weather,
      "temperature": temperature,
    }
    await self.redis_client.setex(
      key,
      timedelta(minutes=30),  # Weather updates every 30 min
      json.dumps(data),
    )

  async def get_weather(self, city_id: int) -> dict[str, Any] | None:
    """Get current weather from Redis."""
    if not self.redis_client:
      return None

    key = f"weather:city:{city_id}"
    data = await self.redis_client.get(key)
    return json.loads(data) if data else None

  async def set_surge(self, city_id: int, hexagon_id: str, surge_multiplier: float) -> None:
    """Store surge multiplier in Redis with TTL."""
    if not self.redis_client:
      return

    key = f"surge:city:{city_id}:hex:{hexagon_id}"
    await self.redis_client.setex(
      key,
      timedelta(minutes=5),
      str(surge_multiplier),
    )

  async def get_surge(self, city_id: int, hexagon_id: str) -> float | None:
    """Get surge multiplier from Redis."""
    if not self.redis_client:
      return None

    key = f"surge:city:{city_id}:hex:{hexagon_id}"
    data = await self.redis_client.get(key)
    return float(data) if data else None

  async def get_all_surges_in_city(self, city_id: int) -> dict[str, float]:
    """Get all surge multipliers for a city."""
    if not self.redis_client:
      return {}

    pattern = f"surge:city:{city_id}:hex:*"
    surges = {}
    async for key in self.redis_client.scan_iter(match=pattern):
      hex_id = key.split(":")[-1]
      value = await self.redis_client.get(key)
      if value:
        surges[hex_id] = float(value)
    return surges

  async def add_trip_request(
    self,
    request_id: str,
    rider_id: str,
    pickup_lat: float,
    pickup_lon: float,
    timestamp: str,
  ) -> None:
    """Add trip request to Redis sorted set for demand tracking."""
    if not self.redis_client:
      return

    data = json.dumps({
      "request_id": request_id,
      "rider_id": rider_id,
      "pickup_lat": pickup_lat,
      "pickup_lon": pickup_lon,
    })
    await self.redis_client.zadd("trip:requests:recent", {data: float(timestamp)})

    cutoff = float(timestamp) - 3600
    await self.redis_client.zremrangebyscore("trip:requests:recent", "-inf", cutoff)

  async def get_recent_trip_requests(self, limit: int = 100) -> list[dict[str, Any]]:
    """Get recent trip requests from Redis."""
    if not self.redis_client:
      return []

    data = await self.redis_client.zrevrange("trip:requests:recent", 0, limit - 1)
    return [json.loads(item) for item in data]

  async def set_active_drivers_in_hex(self, city_id: int, hexagon_id: str, count: int) -> None:
    """Cache active driver count per hexagon."""
    if not self.redis_client:
      return

    key = f"drivers:active:city:{city_id}:hex:{hexagon_id}"
    await self.redis_client.setex(
      key,
      timedelta(minutes=2),  # Update frequently
      str(count),
    )

  async def get_active_drivers_in_hex(self, city_id: int, hexagon_id: str) -> int | None:
    """Get cached active driver count."""
    if not self.redis_client:
      return None

    key = f"drivers:active:city:{city_id}:hex:{hexagon_id}"
    data = await self.redis_client.get(key)
    return int(data) if data else None


# Global database manager instance
db_manager = DatabaseManager()
