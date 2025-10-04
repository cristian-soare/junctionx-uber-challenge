"""Database connections and helpers for Redis and SQLite."""

import json
import os

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import redis.asyncio as redis

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
  """Base class for SQLAlchemy models."""


class DatabaseManager:
  """Manages Redis and SQLite connections."""

  def __init__(self) -> None:
    """Initialize database connections."""
    db_path = Path(__file__).parent.parent / "data" / "uber.db"
    db_path.parent.mkdir(exist_ok=True)
    self.sqlite_url = f"sqlite+aiosqlite:///{db_path}"
    self.engine = create_async_engine(self.sqlite_url, echo=False)
    self.async_session = async_sessionmaker(
      self.engine, class_=AsyncSession, expire_on_commit=False
    )

    self.redis_client: redis.Redis | None = None

  async def init_redis(self) -> None:
    """Initialize Redis connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    self.redis_client = await redis.from_url(
      redis_url,
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
  async def get_session(self) -> AsyncIterator[AsyncSession]:
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

    data = json.dumps(
      {
        "request_id": request_id,
        "rider_id": rider_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
      }
    )
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

  async def set_driver_selections(
    self,
    driver_id: str,
    selected_time: int | None = None,
    remaining_hours: int | None = None,
    selected_zone: str | None = None,
  ) -> None:
    """Store driver's time and zone selections in Redis."""
    if not self.redis_client:
      return

    key = f"driver:selections:{driver_id}"
    data = {
      "selected_time": selected_time,
      "remaining_hours": remaining_hours,
      "selected_zone": selected_zone,
    }
    await self.redis_client.setex(
      key,
      timedelta(hours=24),  # Selections expire after 24 hours
      json.dumps(data),
    )

  async def get_driver_selections(self, driver_id: str) -> dict[str, Any] | None:
    """Get driver's time and zone selections from Redis."""
    if not self.redis_client:
      return None

    key = f"driver:selections:{driver_id}"
    data = await self.redis_client.get(key)
    return json.loads(data) if data else None

  async def publish_optimal_time_notification(
    self,
    driver_id: str,
    optimal_time: int,
    score: float,
    remaining_hours: int,
  ) -> None:
    """Publish optimal time notification to Redis pub/sub channel.

    Clients can subscribe to "driver:notifications:{driver_id}" to receive
    optimal time recommendations.

    Args:
        driver_id: Driver identifier.
        optimal_time: Optimal start hour (0-23).
        score: Score for optimal time.
        remaining_hours: Continuous hours from optimal time.

    """
    if not self.redis_client:
      return

    channel = f"driver:notifications:{driver_id}"
    message = json.dumps(
      {
        "type": "optimal_time",
        "driver_id": driver_id,
        "optimal_time": optimal_time,
        "score": score,
        "remaining_hours": remaining_hours,
        "timestamp": datetime.now(UTC).isoformat(),
      }
    )

    await self.redis_client.publish(channel, message)

  # DP Computation Caching
  async def set_dp_result(
    self,
    cache_key: str,
    earnings: float,
    path: list[str],
    ttl_seconds: int = 3600,
  ) -> None:
    """Cache DP computation result in Redis.

    Args:
        cache_key: Unique key for this DP computation
        earnings: Expected total earnings
        path: Optimal path (list of cluster IDs)
        ttl_seconds: Time to live in seconds (default: 1 hour)

    """
    if not self.redis_client:
      return

    data = {
      "earnings": earnings,
      "path": path,
      "cached_at": datetime.now(UTC).isoformat(),
    }
    await self.redis_client.setex(
      f"cache:dp:{cache_key}",
      timedelta(seconds=ttl_seconds),
      json.dumps(data),
    )

  async def get_dp_result(self, cache_key: str) -> dict[str, Any] | None:
    """Get cached DP computation result from Redis.

    Args:
        cache_key: Unique key for this DP computation

    Returns:
        Dict with earnings and path, or None if not cached

    """
    if not self.redis_client:
      return None

    data = await self.redis_client.get(f"cache:dp:{cache_key}")
    return json.loads(data) if data else None

  async def set_best_starting_positions(
    self,
    city_id: int,
    start_hour: int,
    work_hours: int,
    date: str,
    positions: list[tuple[str, float, list[str]]],
    ttl_seconds: int = 3600,
  ) -> None:
    """Cache best starting positions result.

    Args:
        city_id: City identifier
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work
        date: Date string (YYYY-MM-DD)
        positions: List of (cluster, earnings, path) tuples
        ttl_seconds: Time to live in seconds (default: 1 hour)

    """
    if not self.redis_client:
      return

    key = f"cache:best_positions:{city_id}:{start_hour}:{work_hours}:{date}"
    # Convert tuples to serializable format
    serializable = [
      {"cluster": cluster, "earnings": earnings, "path": path}
      for cluster, earnings, path in positions
    ]
    data = {
      "positions": serializable,
      "cached_at": datetime.now(UTC).isoformat(),
    }
    await self.redis_client.setex(
      key,
      timedelta(seconds=ttl_seconds),
      json.dumps(data),
    )

  async def get_best_starting_positions(
    self, city_id: int, start_hour: int, work_hours: int, date: str
  ) -> list[tuple[str, float, list[str]]] | None:
    """Get cached best starting positions.

    Args:
        city_id: City identifier
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work
        date: Date string (YYYY-MM-DD)

    Returns:
        List of (cluster, earnings, path) tuples, or None if not cached

    """
    if not self.redis_client:
      return None

    key = f"cache:best_positions:{city_id}:{start_hour}:{work_hours}:{date}"
    data = await self.redis_client.get(key)
    if not data:
      return None

    parsed = json.loads(data)
    # Convert back to tuples
    return [
      (item["cluster"], item["earnings"], item["path"]) for item in parsed["positions"]
    ]

  async def invalidate_dp_cache(self, pattern: str = "cache:dp:*") -> int:
    """Invalidate DP cache entries matching pattern.

    Args:
        pattern: Redis key pattern to match (default: all DP caches)

    Returns:
        Number of keys deleted

    """
    if not self.redis_client:
      return 0

    deleted = 0
    async for key in self.redis_client.scan_iter(match=pattern):
      await self.redis_client.delete(key)
      deleted += 1
    return deleted


# Global database manager instance
db_manager = DatabaseManager()
