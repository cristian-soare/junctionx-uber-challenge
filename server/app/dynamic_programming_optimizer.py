"""Dynamic Programming Optimizer for Driver Earnings

This module implements a dynamic programming solution to optimize driver earnings
over a given time horizon in a city-hour mobility graph system.

The algorithm uses backward induction to compute the optimal expected earnings
for a driver starting at a specific cluster and hour, planning to work for L hours.

PERFORMANCE OPTIMIZATIONS:
- Singleton pattern to prevent graph rebuilding
- Graph serialization to pickle/Redis for fast loading
- Transition probability caching per (city, hour)
- DP result memoization with configurable TTL
"""

from datetime import datetime, timedelta
from typing import ClassVar
import pickle
from pathlib import Path

import networkx as nx
import pandas as pd

from app.graph_builder import build_city_graphs, rides
from app.weather_predictor import get_weather_for_date

# Import db_manager for Redis caching (lazy import to avoid circular dependency)
_db_manager = None


def get_db_manager():
  """Get database manager instance (lazy import)."""
  global _db_manager
  if _db_manager is None:
    from app.database import db_manager

    _db_manager = db_manager
  return _db_manager


class MobilityOptimizer:
  """Dynamic Programming optimizer for ride-sharing driver earnings.

  This class implements the city-hour mobility graph concept where:
  - Nodes represent pickup/dropoff clusters
  - Edges store hourly statistics (trip counts, fares, durations)
  - DP computes optimal L-hour strategies starting from any cluster/hour

  SINGLETON PATTERN: Only one instance is created to avoid rebuilding graphs.
  """

  _instance: ClassVar["MobilityOptimizer | None"] = None
  _initialized: ClassVar[bool] = False

  def __new__(cls, *args, **kwargs):
    """Implement singleton pattern to prevent multiple graph loads."""
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(
    self,
    epsilon: float = 0.1,
    gamma: float = 0.95,
    lambda_floor: float = 0.5,
    weather_multipliers: dict[str, float] | None = None,
    use_cache: bool = True,
  ):
    """Initialize the optimizer with parameters.

    Args:
        epsilon: Laplace smoothing parameter for transition probabilities
        gamma: Discount factor for future earnings (0 < gamma <= 1)
        lambda_floor: Minimum demand rate to prevent division by zero
        weather_multipliers: Dictionary mapping weather conditions to multipliers
        use_cache: Whether to use cached graphs (default: True)

    """
    # Only initialize once (singleton pattern)
    if MobilityOptimizer._initialized:
      return

    self.epsilon = epsilon
    self.gamma = gamma
    self.lambda_floor = lambda_floor
    self.use_cache = use_cache

    # Caches for intermediate results
    self._transition_prob_cache: dict = {}  # (city_id, hour) -> transition_probs
    self._dp_cache: dict = {}  # For in-memory DP result caching

    # Load data (with caching)
    self._load_data()

    MobilityOptimizer._initialized = True

  def _get_cache_path(self) -> Path:
    """Get path for cached graph pickle file."""
    cache_dir = Path(__file__).parent.parent / "data" / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "city_graphs.pkl"

  def _load_data(self):
    """Load graphs and surge data with caching support."""
    cache_path = self._get_cache_path()

    # Try to load from cache first
    if self.use_cache and cache_path.exists():
      try:
        print(f"Loading graphs from cache: {cache_path}")
        with open(cache_path, "rb") as f:
          cached_data = pickle.load(f)
          self.graphs = cached_data["graphs"]
          self.surge_lookup = cached_data["surge_lookup"]
        print(f"✓ Loaded {len(self.graphs)} cities from cache (fast path)")
        return
      except Exception as e:
        print(f"Cache load failed: {e}, rebuilding...")

    # Build from scratch
    print("Building mobility graphs from CSV...")
    self.graphs = build_city_graphs(rides)

    print("Loading surge pricing data...")
    self.surge_data = pd.read_csv("/app/data/surge_by_hour.csv")
    # Create surge lookup: (city_id, hour) -> multiplier
    self.surge_lookup = {}
    for _, row in self.surge_data.iterrows():
      self.surge_lookup[(int(row["city_id"]), int(row["hour"]))] = float(row["surge_multiplier"])

    print(f"✓ Loaded data for {len(self.graphs)} cities")

    # Save to cache for next time
    if self.use_cache:
      try:
        print(f"Caching graphs to {cache_path}...")
        with open(cache_path, "wb") as f:
          pickle.dump(
            {
              "graphs": self.graphs,
              "surge_lookup": self.surge_lookup,
            },
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
          )
        print("✓ Graph cache saved")
      except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

  def get_surge_multiplier(self, city_id: int, hour: int) -> float:
    """Get surge multiplier for a city and hour."""
    return self.surge_lookup.get((city_id, hour), 1.0)

  def compute_transition_probabilities(
    self, graph: nx.DiGraph, hour: int, city_id: int | None = None
  ) -> dict[str, dict[str, float]]:
    """Compute transition probabilities P_h(i->j) for a given hour.

    Uses Laplace smoothing: P_h(i->j) = (count_ij[h] + ε) / (Σ_k count_ik[h] + ε·|V|)

    OPTIMIZED: Caches results per (city_id, hour) to avoid recomputation.

    Args:
        graph: NetworkX graph for the city
        hour: Hour of day (0-23)
        city_id: Optional city ID for cache key

    Returns:
        Dictionary where P[i][j] = probability of going from cluster i to j

    """
    # Check cache first
    if city_id is not None:
      cache_key = (city_id, hour)
      if cache_key in self._transition_prob_cache:
        return self._transition_prob_cache[cache_key]

    nodes = list(graph.nodes())
    n_nodes = len(nodes)
    P = {}

    for i in nodes:
      P[i] = {}

      # Get all outgoing edges from node i at this hour
      total_outgoing = 0
      hourly_counts = {}

      for j in nodes:
        if graph.has_edge(i, j):
          edge_data = graph[i][j]
          hourly_trips = edge_data.get("hourly_trips", {})
          count_ij = hourly_trips.get(hour, 0)
        else:
          count_ij = 0

        hourly_counts[j] = count_ij
        total_outgoing += count_ij

      # Apply Laplace smoothing
      denominator = total_outgoing + self.epsilon * n_nodes

      for j in nodes:
        numerator = hourly_counts[j] + self.epsilon
        P[i][j] = numerator / denominator

    # Cache the result
    if city_id is not None:
      self._transition_prob_cache[cache_key] = P

    return P

  def compute_earning_rate(
    self, graph: nx.DiGraph, cluster: str, hour: int, city_id: int, date: datetime
  ) -> float:
    """Compute the earning rate (€/hour) for a driver at a specific cluster and hour.

    Args:
        graph: NetworkX graph for the city
        cluster: Starting cluster ID
        hour: Hour of day (0-23)
        city_id: City identifier
        date: Date for weather lookup

    Returns:
        Expected earning rate in €/hour

    """
    nodes = list(graph.nodes())

    # Get transition probabilities for this hour (with caching)
    P = self.compute_transition_probabilities(graph, hour, city_id)

    if cluster not in P:
      return 0.0  # Cluster not in graph

    # Get surge and weather multipliers
    surge_mult = self.get_surge_multiplier(city_id, hour)
    _, weather_mult = get_weather_for_date(city_id, date)

    # Compute expected fare from cluster
    expected_fare = 0.0
    expected_travel_time = 0.0
    total_outgoing_demand = 0.0

    for j in nodes:
      prob_ij = P[cluster][j]

      if graph.has_edge(cluster, j):
        edge_data = graph[cluster][j]
        hourly_fares = edge_data.get("hourly_avg_price", {})
        hourly_times = edge_data.get("hourly_avg_time", {})
        hourly_trips = edge_data.get("hourly_trips", {})

        fare_ij = hourly_fares.get(hour, edge_data.get("avg_price", 0))
        time_ij = hourly_times.get(hour, edge_data.get("avg_time", 0))
        trips_ij = hourly_trips.get(hour, 0)

        expected_fare += prob_ij * fare_ij * surge_mult * weather_mult
        expected_travel_time += prob_ij * time_ij
        total_outgoing_demand += trips_ij

    # Compute expected wait time
    demand_rate = max(total_outgoing_demand, self.lambda_floor)
    expected_wait_time = 60.0 / demand_rate  # minutes

    # Total expected time per trip
    total_time_minutes = expected_travel_time + expected_wait_time

    if total_time_minutes <= 0:
      return 0.0

    # Convert to earning rate (€/hour)
    earning_rate = expected_fare / (total_time_minutes / 60.0)

    return earning_rate

  def _get_dp_cache_key(
    self, city_id: int, start_cluster: str, start_hour: int, work_hours: int, start_date: datetime
  ) -> str:
    """Generate cache key for DP result.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster ID
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work
        start_date: Starting date

    Returns:
        Cache key string

    """
    date_str = start_date.strftime("%Y-%m-%d")
    return f"dp:{city_id}:{start_cluster}:{start_hour}:{work_hours}:{date_str}"

  async def solve_dp_async(
    self, city_id: int, start_cluster: str, start_hour: int, work_hours: int, start_date: datetime
  ) -> tuple[float, list[str]]:
    """Async version of solve_dp with Redis caching.

    Checks Redis cache before computing, stores result after computation.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster ID
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work (L)
        start_date: Starting date for weather lookup

    Returns:
        Tuple of (total_expected_earnings, optimal_strategy)

    """
    cache_key = self._get_dp_cache_key(city_id, start_cluster, start_hour, work_hours, start_date)

    # Check Redis cache first
    try:
      db = get_db_manager()
      cached = await db.get_dp_result(cache_key)
      if cached:
        return (cached["earnings"], cached["path"])
    except Exception as e:
      print(f"Redis cache read error: {e}")

    # Compute using sync method
    result = self.solve_dp(city_id, start_cluster, start_hour, work_hours, start_date)

    # Cache in Redis
    try:
      db = get_db_manager()
      await db.set_dp_result(cache_key, result[0], result[1], ttl_seconds=3600)
    except Exception as e:
      print(f"Redis cache write error: {e}")

    return result

  def solve_dp(
    self, city_id: int, start_cluster: str, start_hour: int, work_hours: int, start_date: datetime
  ) -> tuple[float, list[str]]:
    """Solve the dynamic programming problem for optimal L-hour strategy.

    Now includes time-aware transitions that track cumulative travel and wait times.

    V_t(i) = best over j: fare_ij + γ * V_{t+time_ij}(j)
    where time_ij includes both travel time and expected wait time

    OPTIMIZED: Results are cached in-memory to avoid recomputation.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster ID
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work (L)
        start_date: Starting date for weather lookup

    Returns:
        Tuple of (total_expected_earnings, optimal_strategy)

    """
    # Check in-memory cache first
    cache_key = self._get_dp_cache_key(city_id, start_cluster, start_hour, work_hours, start_date)
    if cache_key in self._dp_cache:
      return self._dp_cache[cache_key]

    if city_id not in self.graphs:
      raise ValueError(f"City {city_id} not found in graphs")

    graph = self.graphs[city_id]
    nodes = list(graph.nodes())

    if start_cluster not in nodes:
      raise ValueError(f"Cluster {start_cluster} not found in city {city_id}")

    # Convert work_hours to minutes for more precise tracking
    total_work_minutes = work_hours * 60

    # Initialize value function V[time_remaining_minutes][cluster]
    # Use 5-minute intervals to balance precision and computation
    time_intervals = list(range(0, total_work_minutes + 5, 5))

    V = {}
    strategy = {}  # Store optimal next cluster and transition time

    # Terminal condition: V[0][i] = 0 for all i (no time left)
    V[0] = dict.fromkeys(nodes, 0.0)

    # Forward building the value function
    for time_remaining in time_intervals[1:]:  # Skip 0, already initialized
      V[time_remaining] = {}
      strategy[time_remaining] = {}

      for i in nodes:
        best_value = 0.0  # Option to do nothing (earn 0)
        best_next_cluster = None
        best_transition_time = 0

        # Try all possible transitions from cluster i
        for j in nodes:
          if graph.has_edge(i, j):
            # Get current hour based on time elapsed
            minutes_elapsed = total_work_minutes - time_remaining
            current_hour = (start_hour + minutes_elapsed // 60) % 24
            current_date = start_date + timedelta(minutes=minutes_elapsed)

            edge_data = graph[i][j]
            hourly_fares = edge_data.get("hourly_avg_price", {})
            hourly_times = edge_data.get("hourly_avg_time", {})
            hourly_trips = edge_data.get("hourly_trips", {})

            # Get transition data for this hour
            base_fare = hourly_fares.get(current_hour, edge_data.get("avg_price", 0))
            travel_time = hourly_times.get(current_hour, edge_data.get("avg_time", 0))
            trips_count = hourly_trips.get(current_hour, 0)

            # Apply surge and weather multipliers
            surge_mult = self.get_surge_multiplier(city_id, current_hour)
            _, weather_mult = get_weather_for_date(city_id, current_date)
            fare = base_fare * surge_mult * weather_mult

            # Calculate wait time at destination j
            total_outgoing_demand_j = 0
            for k in nodes:
              if graph.has_edge(j, k):
                k_trips = graph[j][k].get("hourly_trips", {}).get(current_hour, 0)
                total_outgoing_demand_j += k_trips

            wait_time_j = 60.0 / max(total_outgoing_demand_j, self.lambda_floor)

            # Total transition time (travel + wait at destination)
            total_transition_time = travel_time + wait_time_j

            # Round to nearest 5-minute interval
            transition_minutes = int(round(total_transition_time / 5.0)) * 5

            # Check if we have enough time for this transition
            if transition_minutes <= time_remaining:
              remaining_after_transition = time_remaining - transition_minutes

              # Get future value from destination after transition
              future_value = V[remaining_after_transition].get(j, 0.0)

              # Total value = immediate fare + discounted future value
              total_value = fare + self.gamma * future_value

              if total_value > best_value:
                best_value = total_value
                best_next_cluster = j
                best_transition_time = transition_minutes

        V[time_remaining][i] = best_value
        strategy[time_remaining][i] = (best_next_cluster, best_transition_time)

    # Extract optimal strategy path by forward simulation
    optimal_path = []
    current_cluster = start_cluster
    time_remaining = total_work_minutes
    total_earnings = V[time_remaining][current_cluster]

    while time_remaining > 0:
      optimal_path.append(current_cluster)

      if current_cluster in strategy[time_remaining]:
        next_cluster, transition_time = strategy[time_remaining][current_cluster]

        if next_cluster is None or transition_time >= time_remaining:
          # No viable transition or not enough time
          break

        # Move to next state
        current_cluster = next_cluster
        time_remaining -= transition_time

        # Prevent infinite loops
        if len(optimal_path) > work_hours * 4:  # Reasonable upper bound
          break
      else:
        break

    # Cache the result before returning
    result = (total_earnings, optimal_path)
    self._dp_cache[cache_key] = result

    return result

  async def analyze_best_starting_positions_async(
    self, city_id: int, start_hour: int, work_hours: int, start_date: datetime, top_k: int = 5
  ) -> list[tuple[str, float, list[str]]]:
    """Async analyze best starting positions with Redis caching.

    Args:
        city_id: City identifier
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work
        start_date: Starting date
        top_k: Number of top positions to return

    Returns:
        List of (cluster, expected_earnings, optimal_path) tuples, sorted by earnings

    """
    date_str = start_date.strftime("%Y-%m-%d")

    # Check Redis cache first
    try:
      db = get_db_manager()
      cached = await db.get_best_starting_positions(city_id, start_hour, work_hours, date_str)
      if cached:
        return cached[:top_k]
    except Exception as e:
      print(f"Redis cache read error: {e}")

    # Compute using sync method
    results = self.analyze_best_starting_positions(
      city_id, start_hour, work_hours, start_date, top_k=100
    )  # Cache more than requested

    # Cache in Redis
    try:
      db = get_db_manager()
      await db.set_best_starting_positions(
        city_id, start_hour, work_hours, date_str, results, ttl_seconds=3600
      )
    except Exception as e:
      print(f"Redis cache write error: {e}")

    return results[:top_k]

  def analyze_best_starting_positions(
    self, city_id: int, start_hour: int, work_hours: int, start_date: datetime, top_k: int = 5
  ) -> list[tuple[str, float, list[str]]]:
    """Analyze the best starting positions for a given scenario.

    Args:
        city_id: City identifier
        start_hour: Starting hour (0-23)
        work_hours: Number of hours to work
        start_date: Starting date
        top_k: Number of top positions to return

    Returns:
        List of (cluster, expected_earnings, optimal_path) tuples, sorted by earnings

    """
    if city_id not in self.graphs:
      raise ValueError(f"City {city_id} not found in graphs")

    graph = self.graphs[city_id]
    nodes = list(graph.nodes())

    results = []

    print(f"Analyzing {len(nodes)} starting positions...")

    for cluster in nodes:
      try:
        earnings, path = self.solve_dp(city_id, cluster, start_hour, work_hours, start_date)
        results.append((cluster, earnings, path))
      except Exception as e:
        print(f"Error analyzing cluster {cluster}: {e}")
        continue

    # Sort by expected earnings (descending)
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]

  def analyze_path_timing(
    self, city_id: int, path: list[str], start_hour: int, start_date: datetime
  ) -> list[dict]:
    """Analyze the detailed timing and earnings for a given path.

    Args:
        city_id: City identifier
        path: List of cluster IDs representing the path
        start_hour: Starting hour
        start_date: Starting date

    Returns:
        List of dictionaries with detailed step information

    """
    if city_id not in self.graphs:
      raise ValueError(f"City {city_id} not found in graphs")

    graph = self.graphs[city_id]
    analysis = []
    cumulative_minutes = 0
    cumulative_earnings = 0.0

    for step, current_cluster in enumerate(path[:-1]):
      next_cluster = path[step + 1]

      # Calculate current time
      current_hour = (start_hour + cumulative_minutes // 60) % 24
      current_date = start_date + timedelta(minutes=cumulative_minutes)

      if graph.has_edge(current_cluster, next_cluster):
        edge_data = graph[current_cluster][next_cluster]
        hourly_fares = edge_data.get("hourly_avg_price", {})
        hourly_times = edge_data.get("hourly_avg_time", {})
        hourly_trips = edge_data.get("hourly_trips", {})

        # Get transition data
        base_fare = hourly_fares.get(current_hour, edge_data.get("avg_price", 0))
        travel_time = hourly_times.get(current_hour, edge_data.get("avg_time", 0))

        # Apply multipliers
        surge_mult = self.get_surge_multiplier(city_id, current_hour)
        _, weather_mult = get_weather_for_date(city_id, current_date)
        fare = base_fare * surge_mult * weather_mult

        # Calculate wait time at destination
        total_outgoing_demand = 0
        nodes = list(graph.nodes())
        for k in nodes:
          if graph.has_edge(next_cluster, k):
            k_trips = graph[next_cluster][k].get("hourly_trips", {}).get(current_hour, 0)
            total_outgoing_demand += k_trips

        wait_time = 60.0 / max(total_outgoing_demand, self.lambda_floor)
        total_time = travel_time + wait_time

        cumulative_minutes += total_time
        cumulative_earnings += fare

        analysis.append(
          {
            "step": step + 1,
            "from_cluster": current_cluster,
            "to_cluster": next_cluster,
            "hour": current_hour,
            "date": current_date.date(),
            "base_fare": base_fare,
            "surge_multiplier": surge_mult,
            "weather_multiplier": weather_mult,
            "final_fare": fare,
            "travel_time_minutes": travel_time,
            "wait_time_minutes": wait_time,
            "total_step_time": total_time,
            "cumulative_minutes": cumulative_minutes,
            "cumulative_hours": cumulative_minutes / 60.0,
            "cumulative_earnings": cumulative_earnings,
            "current_hourly_rate": cumulative_earnings / (cumulative_minutes / 60.0)
            if cumulative_minutes > 0
            else 0,
          }
        )

    return analysis


def example_usage():
  """Example of how to use the MobilityOptimizer."""
  print("=== DYNAMIC PROGRAMMING OPTIMIZER EXAMPLE ===\n")

  # Initialize optimizer
  optimizer = MobilityOptimizer(epsilon=0.1, gamma=0.95, lambda_floor=0.5)

  # Example scenario
  city_id = 3
  start_date = datetime(2023, 1, 15)  # Sunday
  start_hour = 8  # 8 AM
  work_hours = 8  # 8-hour shift

  print(
    f"Scenario: City {city_id}, {work_hours}h shift starting {start_hour}:00 on {start_date.date()}"
  )

  # Find best starting positions
  print("\nFinding best starting positions...")
  best_positions = optimizer.analyze_best_starting_positions(
    city_id=city_id, start_hour=start_hour, work_hours=work_hours, start_date=start_date, top_k=5
  )

  print("\n=== TOP 5 STARTING POSITIONS ===")
  for i, (cluster, earnings, path) in enumerate(best_positions, 1):
    print(f"{i}. Cluster {cluster}: €{earnings:.2f} expected earnings")
    print(f"   Optimal path: {' -> '.join(path[:5])}{'...' if len(path) > 5 else ''}")

  # Detailed analysis for best position
  if best_positions:
    best_cluster, best_earnings, best_path = best_positions[0]
    print("\n=== DETAILED ANALYSIS FOR BEST POSITION ===")
    print(f"Starting cluster: {best_cluster}")
    print(f"Expected total earnings: €{best_earnings:.2f}")
    print(f"Expected hourly rate: €{best_earnings / work_hours:.2f}/hour")
    print(f"Complete optimal path: {' -> '.join(best_path)}")

    # Hour-by-hour breakdown
    print("\n=== HOUR-BY-HOUR BREAKDOWN ===")
    for t, cluster in enumerate(best_path):
      hour = (start_hour + t) % 24
      current_date = start_date + timedelta(hours=t)

      earning_rate = optimizer.compute_earning_rate(
        optimizer.graphs[city_id], cluster, hour, city_id, current_date
      )
      surge = optimizer.get_surge_multiplier(city_id, hour)
      _, weather = get_weather_for_date(city_id, current_date)

      print(f"Hour {t + 1} ({hour:02d}:00): Cluster {cluster}")
      print(f"  Earning rate: €{earning_rate:.2f}/h, Surge: {surge:.2f}x, Weather: {weather:.2f}x")


if __name__ == "__main__":
  example_usage()
