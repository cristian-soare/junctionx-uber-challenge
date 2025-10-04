"""Advanced Dynamic Programming Analysis Tools

This module provides additional tools for analyzing and visualizing the results
of the dynamic programming optimizer for driver earnings.
"""

import json

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from dynamic_programming_optimizer import MobilityOptimizer


class AdvancedAnalyzer:
  """Advanced analysis tools for mobility optimization results."""

  def __init__(self, optimizer: MobilityOptimizer):
    self.optimizer = optimizer

  def compare_work_schedules(
    self, city_id: int, start_cluster: str, start_date: datetime, schedules: list[tuple[int, int]]
  ) -> pd.DataFrame:
    """Compare different work schedules (start_hour, work_hours) for the same starting position.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster
        start_date: Starting date
        schedules: List of (start_hour, work_hours) tuples to compare

    Returns:
        DataFrame with comparison results

    """
    results = []

    for start_hour, work_hours in schedules:
      try:
        earnings, path = self.optimizer.solve_dp(
          city_id, start_cluster, start_hour, work_hours, start_date
        )

        hourly_rate = earnings / work_hours if work_hours > 0 else 0

        results.append(
          {
            "start_hour": start_hour,
            "work_hours": work_hours,
            "total_earnings": earnings,
            "hourly_rate": hourly_rate,
            "schedule": f"{start_hour:02d}:00-{(start_hour + work_hours) % 24:02d}:00",
            "optimal_path": " -> ".join(path[:3]) + ("..." if len(path) > 3 else ""),
          }
        )
      except Exception as e:
        print(f"Error analyzing schedule {start_hour:02d}:00 for {work_hours}h: {e}")

    df = pd.DataFrame(results)
    return df.sort_values("total_earnings", ascending=False)

  def weekly_analysis(
    self, city_id: int, start_cluster: str, start_hour: int, work_hours: int, start_date: datetime
  ) -> pd.DataFrame:
    """Analyze earnings for a full week starting from a given date.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster
        start_hour: Starting hour each day
        work_hours: Hours to work each day
        start_date: Starting date (will analyze 7 consecutive days)

    Returns:
        DataFrame with daily analysis

    """
    results = []

    for day_offset in range(7):
      current_date = start_date + timedelta(days=day_offset)
      day_name = current_date.strftime("%A")

      try:
        earnings, path = self.optimizer.solve_dp(
          city_id, start_cluster, start_hour, work_hours, current_date
        )

        # Get weather for the day
        weather_mult = self.optimizer.get_weather_multiplier(city_id, current_date)
        weather_condition = None
        for condition, mult in self.optimizer.weather_multipliers.items():
          if abs(mult - weather_mult) < 0.01:
            weather_condition = condition
            break

        results.append(
          {
            "date": current_date.date(),
            "day_of_week": day_name,
            "total_earnings": earnings,
            "hourly_rate": earnings / work_hours,
            "weather_condition": weather_condition or "unknown",
            "weather_multiplier": weather_mult,
            "optimal_start": path[0] if path else start_cluster,
            "path_diversity": len(set(path)),  # Number of unique clusters visited
          }
        )
      except Exception as e:
        print(f"Error analyzing {day_name} ({current_date.date()}): {e}")

    return pd.DataFrame(results)

  def surge_sensitivity_analysis(
    self,
    city_id: int,
    start_cluster: str,
    start_hour: int,
    work_hours: int,
    start_date: datetime,
    surge_multipliers: list[float],
  ) -> pd.DataFrame:
    """Analyze how sensitive earnings are to different surge multiplier scenarios.

    Args:
        city_id: City identifier
        start_cluster: Starting cluster
        start_hour: Starting hour
        work_hours: Work duration
        start_date: Starting date
        surge_multipliers: List of uniform surge multipliers to test

    Returns:
        DataFrame with sensitivity analysis

    """
    # Backup original surge data
    original_surge = self.optimizer.surge_lookup.copy()

    results = []

    try:
      for multiplier in surge_multipliers:
        # Override all surge multipliers with the test value
        for key in self.optimizer.surge_lookup:
          self.optimizer.surge_lookup[key] = multiplier

        earnings, path = self.optimizer.solve_dp(
          city_id, start_cluster, start_hour, work_hours, start_date
        )

        results.append(
          {
            "surge_multiplier": multiplier,
            "total_earnings": earnings,
            "hourly_rate": earnings / work_hours,
            "earnings_vs_baseline": earnings / results[0]["total_earnings"] if results else 1.0,
          }
        )

    finally:
      # Restore original surge data
      self.optimizer.surge_lookup = original_surge

    return pd.DataFrame(results)

  def cluster_popularity_analysis(self, city_id: int, hour: int) -> pd.DataFrame:
    """Analyze which clusters are most popular as destinations at a specific hour.

    Args:
        city_id: City identifier
        hour: Hour of day (0-23)

    Returns:
        DataFrame with cluster popularity metrics

    """
    if city_id not in self.optimizer.graphs:
      raise ValueError(f"City {city_id} not found")

    graph = self.optimizer.graphs[city_id]
    nodes = list(graph.nodes())

    results = []

    for cluster in nodes:
      # Calculate incoming and outgoing trip counts for this hour
      incoming_trips = 0
      outgoing_trips = 0
      incoming_avg_fare = 0
      outgoing_avg_fare = 0
      incoming_count = 0
      outgoing_count = 0

      # Incoming trips (ending at this cluster)
      for source in nodes:
        if graph.has_edge(source, cluster):
          edge_data = graph[source][cluster]
          hourly_trips = edge_data.get("hourly_trips", {})
          hourly_fares = edge_data.get("hourly_avg_price", {})

          trips = hourly_trips.get(hour, 0)
          fare = hourly_fares.get(hour, edge_data.get("avg_price", 0))

          incoming_trips += trips
          if trips > 0:
            incoming_avg_fare += fare * trips
            incoming_count += trips

      # Outgoing trips (starting from this cluster)
      for dest in nodes:
        if graph.has_edge(cluster, dest):
          edge_data = graph[cluster][dest]
          hourly_trips = edge_data.get("hourly_trips", {})
          hourly_fares = edge_data.get("hourly_avg_price", {})

          trips = hourly_trips.get(hour, 0)
          fare = hourly_fares.get(hour, edge_data.get("avg_price", 0))

          outgoing_trips += trips
          if trips > 0:
            outgoing_avg_fare += fare * trips
            outgoing_count += trips

      # Calculate averages
      incoming_avg_fare = incoming_avg_fare / incoming_count if incoming_count > 0 else 0
      outgoing_avg_fare = outgoing_avg_fare / outgoing_count if outgoing_count > 0 else 0

      # Get earning rate for this cluster at this hour
      earning_rate = self.optimizer.compute_earning_rate(
        graph,
        cluster,
        hour,
        city_id,
        datetime(2023, 1, 15),  # Use sample date
      )

      results.append(
        {
          "cluster": cluster,
          "incoming_trips": incoming_trips,
          "outgoing_trips": outgoing_trips,
          "net_flow": incoming_trips - outgoing_trips,
          "total_activity": incoming_trips + outgoing_trips,
          "incoming_avg_fare": incoming_avg_fare,
          "outgoing_avg_fare": outgoing_avg_fare,
          "earning_rate": earning_rate,
        }
      )

    df = pd.DataFrame(results)
    return df.sort_values("earning_rate", ascending=False)

  def export_results_to_json(
    self, city_id: int, analysis_results: dict, filename: str = "dp_analysis_results.json"
  ):
    """Export analysis results to JSON for further processing or visualization.

    Args:
        city_id: City identifier
        analysis_results: Dictionary containing various analysis results
        filename: Output filename

    """
    # Convert pandas DataFrames to dictionaries for JSON serialization
    json_results = {}

    for key, value in analysis_results.items():
      if isinstance(value, pd.DataFrame):
        json_results[key] = value.to_dict("records")
      elif isinstance(value, np.ndarray):
        json_results[key] = value.tolist()
      else:
        json_results[key] = value

    # Add metadata
    json_results["metadata"] = {
      "city_id": city_id,
      "analysis_timestamp": datetime.now().isoformat(),
      "optimizer_parameters": {
        "epsilon": self.optimizer.epsilon,
        "gamma": self.optimizer.gamma,
        "lambda_floor": self.optimizer.lambda_floor,
      },
    }

    with open(filename, "w") as f:
      json.dump(json_results, f, indent=2, default=str)

    print(f"✓ Results exported to {filename}")


def comprehensive_analysis_example():
  """Comprehensive analysis example showcasing various features."""
  print("=== COMPREHENSIVE DYNAMIC PROGRAMMING ANALYSIS ===\n")

  # Initialize optimizer and analyzer
  optimizer = MobilityOptimizer(epsilon=0.1, gamma=0.95, lambda_floor=0.5)
  analyzer = AdvancedAnalyzer(optimizer)

  # Analysis parameters
  city_id = 3
  start_cluster = "c_3_2"  # Best cluster from previous analysis
  start_date = datetime(2023, 1, 15)  # Sunday

  print(f"Analyzing City {city_id}, starting from cluster {start_cluster}")
  print(f"Base date: {start_date.date()}\n")

  # 1. Compare different work schedules
  print("1. COMPARING WORK SCHEDULES")
  print("=" * 50)
  schedules = [
    (6, 8),  # Early shift: 6 AM - 2 PM
    (8, 8),  # Morning shift: 8 AM - 4 PM
    (10, 8),  # Late morning: 10 AM - 6 PM
    (14, 8),  # Afternoon: 2 PM - 10 PM
    (18, 8),  # Evening: 6 PM - 2 AM
    (22, 8),  # Night: 10 PM - 6 AM
    (8, 4),  # Short morning: 8 AM - 12 PM
    (8, 12),  # Long day: 8 AM - 8 PM
  ]

  schedule_results = analyzer.compare_work_schedules(city_id, start_cluster, start_date, schedules)

  print(schedule_results.to_string(index=False, float_format="%.2f"))

  # 2. Weekly analysis
  print("\n\n2. WEEKLY EARNINGS ANALYSIS")
  print("=" * 50)
  weekly_results = analyzer.weekly_analysis(city_id, start_cluster, 8, 8, start_date)

  print(weekly_results.to_string(index=False, float_format="%.2f"))

  weekly_avg = weekly_results["total_earnings"].mean()
  weekly_std = weekly_results["total_earnings"].std()
  print("\nWeekly Summary:")
  print(f"Average daily earnings: €{weekly_avg:.2f}")
  print(f"Standard deviation: €{weekly_std:.2f}")
  print(
    f"Best day: {weekly_results.loc[weekly_results['total_earnings'].idxmax(), 'day_of_week']} (€{weekly_results['total_earnings'].max():.2f})"
  )
  print(
    f"Worst day: {weekly_results.loc[weekly_results['total_earnings'].idxmin(), 'day_of_week']} (€{weekly_results['total_earnings'].min():.2f})"
  )

  # 3. Surge sensitivity analysis
  print("\n\n3. SURGE PRICING SENSITIVITY")
  print("=" * 50)
  surge_multipliers = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0]

  surge_results = analyzer.surge_sensitivity_analysis(
    city_id, start_cluster, 8, 8, start_date, surge_multipliers
  )

  print(surge_results.to_string(index=False, float_format="%.2f"))

  # 4. Cluster popularity analysis
  print("\n\n4. CLUSTER POPULARITY AT PEAK HOUR (8 AM)")
  print("=" * 50)
  popularity_results = analyzer.cluster_popularity_analysis(city_id, 8)

  print(popularity_results.to_string(index=False, float_format="%.2f"))

  # 5. Export results
  print("\n\n5. EXPORTING RESULTS")
  print("=" * 50)

  all_results = {
    "schedule_comparison": schedule_results,
    "weekly_analysis": weekly_results,
    "surge_sensitivity": surge_results,
    "cluster_popularity": popularity_results,
  }

  analyzer.export_results_to_json(city_id, all_results, "comprehensive_analysis.json")

  # Summary insights
  print("\n\n=== KEY INSIGHTS ===")
  print(
    f"🏆 Best work schedule: {schedule_results.iloc[0]['schedule']} (€{schedule_results.iloc[0]['total_earnings']:.2f})"
  )
  print(f"📊 Average weekly earnings: €{weekly_avg * 7:.2f} per week")
  print(
    f"📈 Surge impact: 2x surge pricing increases earnings by {((surge_results[surge_results['surge_multiplier'] == 2.0]['earnings_vs_baseline'].iloc[0] - 1) * 100):.1f}%"
  )
  print(
    f"🎯 Best earning cluster: {popularity_results.iloc[0]['cluster']} (€{popularity_results.iloc[0]['earning_rate']:.2f}/h)"
  )


if __name__ == "__main__":
  comprehensive_analysis_example()
