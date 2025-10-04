#!/usr/bin/env python3
"""Command-line interface for the Dynamic Programming Optimizer

This script provides a simple command-line interface to the DP optimizer,
allowing users to quickly analyze different scenarios without writing code.

Usage examples:
    python3 dp_cli.py --city 3 --cluster c_3_2 --hour 8 --duration 8 --date 2023-01-15
    python3 dp_cli.py --city 1 --best-positions --hour 10 --duration 6 --date 2023-02-01
    python3 dp_cli.py --city 3 --compare-schedules --cluster c_3_2 --date 2023-01-15
"""

import argparse
import sys

from datetime import datetime, timedelta

from advanced_analysis import AdvancedAnalyzer
from dynamic_programming_optimizer import MobilityOptimizer


def parse_date(date_str: str) -> datetime:
  """Parse date string in YYYY-MM-DD format."""
  try:
    return datetime.strptime(date_str, "%Y-%m-%d")
  except ValueError:
    raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
  parser = argparse.ArgumentParser(
    description="Dynamic Programming Optimizer for Ride-sharing Driver Earnings",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Optimize 8-hour shift starting at 8 AM from cluster c_3_2
  python3 dp_cli.py --city 3 --cluster c_3_2 --hour 8 --duration 8 --date 2023-01-15
  
  # Find best starting positions for a 6-hour shift at 10 AM
  python3 dp_cli.py --city 1 --best-positions --hour 10 --duration 6 --date 2023-02-01
  
  # Compare different work schedules for cluster c_3_2
  python3 dp_cli.py --city 3 --compare-schedules --cluster c_3_2 --date 2023-01-15
  
  # Analyze weekly earnings pattern
  python3 dp_cli.py --city 3 --weekly --cluster c_3_2 --hour 8 --duration 8 --date 2023-01-15
        """,
  )

  # Required arguments
  parser.add_argument("--city", type=int, required=True, help="City ID (1-5)")
  parser.add_argument(
    "--date", type=parse_date, required=True, help="Start date in YYYY-MM-DD format"
  )

  # Analysis type (mutually exclusive)
  analysis_group = parser.add_mutually_exclusive_group(required=True)
  analysis_group.add_argument(
    "--cluster", type=str, help="Analyze specific starting cluster (e.g., c_3_2)"
  )
  analysis_group.add_argument(
    "--best-positions", action="store_true", help="Find best starting positions"
  )
  analysis_group.add_argument(
    "--compare-schedules", action="store_true", help="Compare different work schedules"
  )
  analysis_group.add_argument("--weekly", action="store_true", help="Weekly earnings analysis")
  analysis_group.add_argument(
    "--cluster-popularity", action="store_true", help="Analyze cluster popularity"
  )

  # Optional parameters
  parser.add_argument("--hour", type=int, default=8, help="Starting hour (0-23, default: 8)")
  parser.add_argument("--duration", type=int, default=8, help="Work duration in hours (default: 8)")
  parser.add_argument(
    "--top-k", type=int, default=5, help="Number of top results to show (default: 5)"
  )

  # Optimizer parameters
  parser.add_argument(
    "--epsilon", type=float, default=0.1, help="Laplace smoothing parameter (default: 0.1)"
  )
  parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor (default: 0.95)")
  parser.add_argument(
    "--lambda-floor", type=float, default=0.5, help="Minimum demand rate (default: 0.5)"
  )

  # Output options
  parser.add_argument("--json", type=str, help="Export results to JSON file")
  parser.add_argument("--verbose", action="store_true", help="Verbose output")

  args = parser.parse_args()

  # Validate arguments
  if args.hour < 0 or args.hour > 23:
    print("Error: Hour must be between 0 and 23")
    sys.exit(1)

  if args.duration < 1 or args.duration > 24:
    print("Error: Duration must be between 1 and 24 hours")
    sys.exit(1)

  # Initialize optimizer
  print(
    f"Initializing optimizer (ε={args.epsilon}, γ={args.gamma}, λ_floor={args.lambda_floor})..."
  )
  optimizer = MobilityOptimizer(
    epsilon=args.epsilon, gamma=args.gamma, lambda_floor=args.lambda_floor
  )

  analyzer = AdvancedAnalyzer(optimizer)

  # Check if city exists
  if args.city not in optimizer.graphs:
    print(f"Error: City {args.city} not found. Available cities: {list(optimizer.graphs.keys())}")
    sys.exit(1)

  results = {}

  try:
    # Execute analysis based on selected type
    if args.cluster:
      print(f"\n=== CLUSTER ANALYSIS: {args.cluster} ===")
      print(f"City: {args.city}, Date: {args.date.date()}")
      print(f"Schedule: {args.hour:02d}:00 for {args.duration} hours")
      print("-" * 50)

      earnings, path = optimizer.solve_dp(
        args.city, args.cluster, args.hour, args.duration, args.date
      )

      print(f"Expected total earnings: €{earnings:.2f}")
      print(f"Expected hourly rate: €{earnings / args.duration:.2f}/hour")
      print(f"Optimal path: {' -> '.join(path)}")

      if args.verbose:
        print("\n=== DETAILED PATH TIMING ANALYSIS ===")
        timing_analysis = optimizer.analyze_path_timing(args.city, path, args.hour, args.date)

        if timing_analysis:
          print(
            f"{'Step':<4} {'From':<8} {'To':<8} {'Hour':<5} {'Fare':<8} {'Travel':<7} {'Wait':<6} {'Total':<7} {'Cum.Time':<8} {'Cum.€':<8} {'Rate':<8}"
          )
          print("-" * 80)

          for step_info in timing_analysis:
            print(
              f"{step_info['step']:<4} "
              f"{step_info['from_cluster']:<8} "
              f"{step_info['to_cluster']:<8} "
              f"{int(step_info['hour']):02d}:00{'':<1} "
              f"€{step_info['final_fare']:.2f}{'':<3} "
              f"{step_info['travel_time_minutes']:.1f}min{'':<1} "
              f"{step_info['wait_time_minutes']:.1f}m{'':<2} "
              f"{step_info['total_step_time']:.1f}min{'':<1} "
              f"{step_info['cumulative_hours']:.1f}h{'':<4} "
              f"€{step_info['cumulative_earnings']:.2f}{'':<3} "
              f"€{step_info['current_hourly_rate']:.1f}/h"
            )

          total_time_hours = timing_analysis[-1]["cumulative_hours"]
          total_earnings = timing_analysis[-1]["cumulative_earnings"]
          print(
            f"\nSummary: €{total_earnings:.2f} earned in {total_time_hours:.1f} hours (€{total_earnings / total_time_hours:.2f}/hour)"
          )
        else:
          print("No transitions found in path (single cluster strategy)")

          # Show single cluster earning rate for each hour
          print(f"Single cluster ({path[0]}) hourly rates:")
          for t in range(min(args.duration, len(path))):
            hour = (args.hour + t) % 24
            current_date = args.date + timedelta(hours=t)

            earning_rate = optimizer.compute_earning_rate(
              optimizer.graphs[args.city], path[0], hour, args.city, current_date
            )
            surge = optimizer.get_surge_multiplier(args.city, hour)
            weather = optimizer.get_weather_multiplier(args.city, current_date)

            print(
              f"Hour {t + 1:2d} ({hour:02d}:00): €{earning_rate:.2f}/h "
              f"(surge: {surge:.2f}x, weather: {weather:.2f}x)"
            )

      results["cluster_analysis"] = {
        "cluster": args.cluster,
        "total_earnings": earnings,
        "hourly_rate": earnings / args.duration,
        "optimal_path": path,
      }

    elif args.best_positions:
      print("\n=== BEST STARTING POSITIONS ===")
      print(f"City: {args.city}, Date: {args.date.date()}")
      print(f"Schedule: {args.hour:02d}:00 for {args.duration} hours")
      print("-" * 50)

      best_positions = analyzer.optimizer.analyze_best_starting_positions(
        args.city, args.hour, args.duration, args.date, args.top_k
      )

      for i, (cluster, earnings, path) in enumerate(best_positions, 1):
        print(f"{i:2d}. {cluster}: €{earnings:.2f} (€{earnings / args.duration:.2f}/h)")
        if args.verbose:
          print(f"    Path: {' -> '.join(path)}")

      results["best_positions"] = [
        {"rank": i, "cluster": cluster, "earnings": earnings, "path": path}
        for i, (cluster, earnings, path) in enumerate(best_positions, 1)
      ]

    elif args.compare_schedules:
      if not hasattr(args, "cluster") or not args.cluster:
        # Need cluster for schedule comparison
        cluster_arg = input("Enter starting cluster (e.g., c_3_2): ").strip()
        if not cluster_arg:
          print("Error: Cluster required for schedule comparison")
          sys.exit(1)
      else:
        cluster_arg = args.cluster

      print("\n=== SCHEDULE COMPARISON ===")
      print(f"City: {args.city}, Cluster: {cluster_arg}, Date: {args.date.date()}")
      print("-" * 70)

      schedules = [
        (6, 8),
        (8, 8),
        (10, 8),
        (14, 8),
        (18, 8),
        (22, 8),
        (8, 4),
        (8, 6),
        (8, 10),
        (8, 12),
      ]

      schedule_results = analyzer.compare_work_schedules(
        args.city, cluster_arg, args.date, schedules
      )

      print(schedule_results.to_string(index=False, float_format="%.2f"))
      results["schedule_comparison"] = schedule_results.to_dict("records")

    elif args.weekly:
      if not hasattr(args, "cluster") or not args.cluster:
        cluster_arg = input("Enter starting cluster (e.g., c_3_2): ").strip()
        if not cluster_arg:
          print("Error: Cluster required for weekly analysis")
          sys.exit(1)
      else:
        cluster_arg = args.cluster

      print("\n=== WEEKLY ANALYSIS ===")
      print(f"City: {args.city}, Cluster: {cluster_arg}")
      print(f"Schedule: {args.hour:02d}:00 for {args.duration} hours daily")
      print(f"Week starting: {args.date.date()}")
      print("-" * 70)

      weekly_results = analyzer.weekly_analysis(
        args.city, cluster_arg, args.hour, args.duration, args.date
      )

      print(weekly_results.to_string(index=False, float_format="%.2f"))

      weekly_avg = weekly_results["total_earnings"].mean()
      weekly_total = weekly_results["total_earnings"].sum()
      print("\nWeekly Summary:")
      print(f"Total weekly earnings: €{weekly_total:.2f}")
      print(f"Average daily earnings: €{weekly_avg:.2f}")
      print(
        f"Best day: {weekly_results.loc[weekly_results['total_earnings'].idxmax(), 'day_of_week']}"
      )
      print(
        f"Worst day: {weekly_results.loc[weekly_results['total_earnings'].idxmin(), 'day_of_week']}"
      )

      results["weekly_analysis"] = weekly_results.to_dict("records")

    elif args.cluster_popularity:
      print("\n=== CLUSTER POPULARITY ===")
      print(f"City: {args.city}, Hour: {args.hour:02d}:00")
      print("-" * 70)

      popularity_results = analyzer.cluster_popularity_analysis(args.city, args.hour)
      print(popularity_results.to_string(index=False, float_format="%.2f"))

      results["cluster_popularity"] = popularity_results.to_dict("records")

    # Export to JSON if requested
    if args.json:
      analyzer.export_results_to_json(args.city, results, args.json)

  except Exception as e:
    print(f"Error during analysis: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
