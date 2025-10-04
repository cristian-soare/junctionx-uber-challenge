#!/usr/bin/env python3
"""
Hourly Rate Checker

A simple utility to check the hourly earning rate for any cluster at any hour
using the existing compute_earning_rate method from the DP optimizer.

Usage examples:
    python3 hourly_rate_checker.py --city 3 --cluster c_3_2 --hour 8 --date 2023-01-15
    python3 hourly_rate_checker.py --city 1 --cluster c_1_4 --hour 18 --date 2023-02-01 --verbose
    python3 hourly_rate_checker.py --city 3 --all-clusters --hour 16 --date 2023-01-15
"""

import argparse
from datetime import datetime
import sys
from dynamic_programming_optimizer import MobilityOptimizer
import pandas as pd


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def display_single_rate(optimizer: MobilityOptimizer, 
                       city_id: int, 
                       cluster: str, 
                       hour: int, 
                       date: datetime, 
                       verbose: bool = False):
    """Display earning rate for a single cluster at a specific hour."""
    
    if city_id not in optimizer.graphs:
        print(f"Error: City {city_id} not found. Available cities: {list(optimizer.graphs.keys())}")
        return
    
    graph = optimizer.graphs[city_id]
    
    if cluster not in graph.nodes():
        print(f"Error: Cluster {cluster} not found in city {city_id}")
        print(f"Available clusters: {list(graph.nodes())}")
        return
    
    # Calculate earning rate
    earning_rate = optimizer.compute_earning_rate(graph, cluster, hour, city_id, date)
    
    # Get multipliers
    surge_mult = optimizer.get_surge_multiplier(city_id, hour)
    weather_mult = optimizer.get_weather_multiplier(city_id, date)
    
    print(f"\n=== HOURLY RATE FOR {cluster} ===")
    print(f"City: {city_id}")
    print(f"Date: {date.date()} ({date.strftime('%A')})")
    print(f"Hour: {hour:02d}:00")
    print(f"Cluster: {cluster}")
    print("-" * 40)
    print(f"💰 Earning Rate: €{earning_rate:.2f}/hour")
    print(f"📈 Surge Multiplier: {surge_mult:.2f}x")
    print(f"🌤️  Weather Multiplier: {weather_mult:.2f}x")
    
    if verbose:
        print(f"\n=== DETAILED BREAKDOWN ===")
        
        # Get transition probabilities
        P = optimizer.compute_transition_probabilities(graph, hour)
        nodes = list(graph.nodes())
        
        expected_fare = 0.0
        expected_travel_time = 0.0
        total_demand = 0.0
        
        print(f"Transition probabilities from {cluster}:")
        for dest in nodes:
            prob = P[cluster][dest]
            if prob > 0.01:  # Only show significant probabilities
                if graph.has_edge(cluster, dest):
                    edge_data = graph[cluster][dest]
                    hourly_fares = edge_data.get('hourly_avg_price', {})
                    hourly_times = edge_data.get('hourly_avg_time', {})
                    hourly_trips = edge_data.get('hourly_trips', {})
                    
                    fare = hourly_fares.get(hour, edge_data.get('avg_price', 0))
                    time = hourly_times.get(hour, edge_data.get('avg_time', 0))
                    trips = hourly_trips.get(hour, 0)
                    
                    contribution_fare = prob * fare * surge_mult * weather_mult
                    contribution_time = prob * time
                    
                    expected_fare += contribution_fare
                    expected_travel_time += contribution_time
                    total_demand += trips
                    
                    print(f"  -> {dest}: P={prob:.3f}, fare=€{fare:.2f}, time={time:.1f}min, trips={trips}")
                    print(f"     Contributes: €{contribution_fare:.2f} to fare, {contribution_time:.1f}min to time")
        
        wait_time = 60.0 / max(total_demand, optimizer.lambda_floor)
        total_time = expected_travel_time + wait_time
        
        print(f"\nCalculation breakdown:")
        print(f"  Expected fare per trip: €{expected_fare:.2f}")
        print(f"  Expected travel time: {expected_travel_time:.1f} minutes")
        print(f"  Expected wait time: {wait_time:.1f} minutes")
        print(f"  Total time per trip: {total_time:.1f} minutes")
        print(f"  Earning rate: €{expected_fare:.2f} ÷ ({total_time:.1f}/60) = €{earning_rate:.2f}/hour")


def display_all_clusters(optimizer: MobilityOptimizer, 
                        city_id: int, 
                        hour: int, 
                        date: datetime):
    """Display earning rates for all clusters in a city at a specific hour."""
    
    if city_id not in optimizer.graphs:
        print(f"Error: City {city_id} not found. Available cities: {list(optimizer.graphs.keys())}")
        return
    
    graph = optimizer.graphs[city_id]
    nodes = list(graph.nodes())
    
    print(f"\n=== HOURLY RATES FOR ALL CLUSTERS ===")
    print(f"City: {city_id}")
    print(f"Date: {date.date()} ({date.strftime('%A')})")
    print(f"Hour: {hour:02d}:00")
    
    surge_mult = optimizer.get_surge_multiplier(city_id, hour)
    weather_mult = optimizer.get_weather_multiplier(city_id, date)
    print(f"Surge: {surge_mult:.2f}x, Weather: {weather_mult:.2f}x")
    print("-" * 50)
    
    # Calculate rates for all clusters
    results = []
    for cluster in nodes:
        earning_rate = optimizer.compute_earning_rate(graph, cluster, hour, city_id, date)
        results.append((cluster, earning_rate))
    
    # Sort by earning rate (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'Rank':<4} {'Cluster':<10} {'Earning Rate':<15}")
    print("-" * 30)
    
    for i, (cluster, rate) in enumerate(results, 1):
        print(f"{i:<4} {cluster:<10} €{rate:.2f}/hour")
    
    # Show top 3 with some stats
    if len(results) >= 3:
        best_rate = results[0][1]
        worst_rate = results[-1][1]
        avg_rate = sum(rate for _, rate in results) / len(results)
        
        print(f"\n📊 Summary:")
        print(f"Best cluster: {results[0][0]} (€{best_rate:.2f}/h)")
        print(f"Worst cluster: {results[-1][0]} (€{worst_rate:.2f}/h)")
        print(f"Average rate: €{avg_rate:.2f}/h")
        print(f"Rate spread: €{best_rate - worst_rate:.2f}/h")


def compare_hours(optimizer: MobilityOptimizer, 
                 city_id: int, 
                 cluster: str, 
                 date: datetime, 
                 hours_to_compare: list = None):
    """Compare earning rates for a cluster across different hours."""
    
    if hours_to_compare is None:
        hours_to_compare = [6, 8, 12, 16, 18, 20, 22]  # Peak times
    
    if city_id not in optimizer.graphs:
        print(f"Error: City {city_id} not found. Available cities: {list(optimizer.graphs.keys())}")
        return
    
    graph = optimizer.graphs[city_id]
    
    if cluster not in graph.nodes():
        print(f"Error: Cluster {cluster} not found in city {city_id}")
        return
    
    print(f"\n=== HOURLY COMPARISON FOR {cluster} ===")
    print(f"City: {city_id}")
    print(f"Date: {date.date()} ({date.strftime('%A')})")
    print("-" * 50)
    
    results = []
    for hour in hours_to_compare:
        earning_rate = optimizer.compute_earning_rate(graph, cluster, hour, city_id, date)
        surge_mult = optimizer.get_surge_multiplier(city_id, hour)
        results.append((hour, earning_rate, surge_mult))
    
    # Sort by earning rate
    results.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'Rank':<4} {'Hour':<6} {'Earning Rate':<15} {'Surge':<8}")
    print("-" * 40)
    
    for i, (hour, rate, surge) in enumerate(results, 1):
        print(f"{i:<4} {hour:02d}:00{'':<1} €{rate:.2f}/hour{'':<4} {surge:.2f}x")
    
    best_hour = results[0][0]
    best_rate = results[0][1]
    print(f"\n🏆 Best hour: {best_hour:02d}:00 with €{best_rate:.2f}/hour")


def main():
    parser = argparse.ArgumentParser(
        description="Hourly Rate Checker - Display earning rates for specific clusters and hours",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check rate for specific cluster and hour
  python3 hourly_rate_checker.py --city 3 --cluster c_3_2 --hour 8 --date 2023-01-15
  
  # Check with detailed breakdown
  python3 hourly_rate_checker.py --city 3 --cluster c_3_2 --hour 8 --date 2023-01-15 --verbose
  
  # Check all clusters at specific hour
  python3 hourly_rate_checker.py --city 3 --all-clusters --hour 16 --date 2023-01-15
  
  # Compare cluster across different hours
  python3 hourly_rate_checker.py --city 3 --cluster c_3_2 --compare-hours --date 2023-01-15
        """
    )
    
    # Required arguments
    parser.add_argument('--city', type=int, required=True,
                       help='City ID (1-5)')
    parser.add_argument('--date', type=parse_date, required=True,
                       help='Date in YYYY-MM-DD format')
    
    # Analysis type (mutually exclusive)
    analysis_group = parser.add_mutually_exclusive_group(required=True)
    analysis_group.add_argument('--cluster', type=str,
                               help='Check specific cluster (e.g., c_3_2)')
    analysis_group.add_argument('--all-clusters', action='store_true',
                               help='Check all clusters at specific hour')
    analysis_group.add_argument('--compare-hours', action='store_true',
                               help='Compare cluster across different hours')
    
    # Optional parameters
    parser.add_argument('--hour', type=int, default=8,
                       help='Hour (0-23, default: 8). Required for --cluster and --all-clusters')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed breakdown')
    
    # Optimizer parameters
    parser.add_argument('--epsilon', type=float, default=0.1,
                       help='Laplace smoothing parameter (default: 0.1)')
    parser.add_argument('--gamma', type=float, default=0.95,
                       help='Discount factor (default: 0.95)')
    parser.add_argument('--lambda-floor', type=float, default=0.5,
                       help='Minimum demand rate (default: 0.5)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.hour < 0 or args.hour > 23:
        print("Error: Hour must be between 0 and 23")
        sys.exit(1)
    
    # Initialize optimizer
    print(f"Initializing optimizer (ε={args.epsilon}, γ={args.gamma}, λ_floor={args.lambda_floor})...")
    optimizer = MobilityOptimizer(
        epsilon=args.epsilon,
        gamma=args.gamma,
        lambda_floor=args.lambda_floor
    )
    
    try:
        if args.cluster:
            display_single_rate(optimizer, args.city, args.cluster, args.hour, args.date, args.verbose)
        elif args.all_clusters:
            display_all_clusters(optimizer, args.city, args.hour, args.date)
        elif args.compare_hours:
            # Need cluster for hour comparison
            cluster_input = input("Enter cluster to compare across hours (e.g., c_3_2): ").strip()
            if not cluster_input:
                print("Error: Cluster required for hour comparison")
                sys.exit(1)
            compare_hours(optimizer, args.city, cluster_input, args.date)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()