"""Graph building utilities for city-based ride data.

This module reads the ride trips CSV and constructs per-city directed graphs.
Nodes represent clusters from the ride data, and edges carry average duration and fare
between nodes (including self-edges). Utilities are provided to convert graphs
to Cytoscape elements for interactive UI rendering.
"""

import networkx as nx
import numpy as np
import pandas as pd

import os

CSV_PATH = "/workspace/server/data/ride_trips_with_clusters.csv"

# Read CSV
rides = pd.read_csv(CSV_PATH)

# Build graphs per city
def build_city_graphs(rides: pd.DataFrame) -> dict[int, nx.DiGraph]:
  """Build a directed graph per city where nodes are clusters and edges carry averages."""
  city_graphs: dict[int, nx.DiGraph] = {}
  for city_id in rides["city_id"].unique():
    city_df = rides[rides["city_id"] == city_id].copy()
    city_df["pickup_node"] = city_df["pickup_cluster"]
    city_df["dropoff_node"] = city_df["dropoff_cluster"]
    
    g: nx.DiGraph = nx.DiGraph()
    # Add nodes
    nodes = set(city_df["pickup_node"]).union(set(city_df["dropoff_node"]))

    # Store node positions (average lat/lon of all rides in this cluster) for UI positioning
    for node_id in nodes:
      # Get average coordinates for pickup clusters
      pickup_coords = city_df[city_df["pickup_cluster"] == node_id][["pickup_lat", "pickup_lon"]]
      dropoff_coords = city_df[city_df["dropoff_cluster"] == node_id][["drop_lat", "drop_lon"]]
      
      # Combine coordinates from both pickup and dropoff instances
      all_lats = []
      all_lons = []
      
      if not pickup_coords.empty:
        all_lats.extend(pickup_coords["pickup_lat"].tolist())
        all_lons.extend(pickup_coords["pickup_lon"].tolist())
      
      if not dropoff_coords.empty:
        all_lats.extend(dropoff_coords["drop_lat"].tolist())
        all_lons.extend(dropoff_coords["drop_lon"].tolist())
      
      # Calculate average position
      if all_lats and all_lons:
        avg_lat = np.mean(all_lats)
        avg_lon = np.mean(all_lons)
      else:
        avg_lat = avg_lon = 0.0
      
      g.add_node(node_id, lat=avg_lat, lon=avg_lon)

    # Add edges with average time and price, plus hourly statistics
    # First convert start_time to datetime and extract hour
    city_df["start_time"] = pd.to_datetime(city_df["start_time"])
    city_df["hour"] = city_df["start_time"].dt.hour
    
    # Group by pickup/dropoff nodes and calculate overall averages
    edge_stats = (
      city_df.groupby(["pickup_node", "dropoff_node"])
      .agg({
        "duration_mins": "mean", 
        "fare_amount": "mean",
        "ride_id": "count"  # total trips
      })
      .reset_index()
    )
    
    # Calculate hourly statistics for each edge
    hourly_stats = (
      city_df.groupby(["pickup_node", "dropoff_node", "hour"])
      .agg({
        "ride_id": "count",
        "duration_mins": "mean",
        "fare_amount": "mean"
      })
      .reset_index()
    )
    
    for _, row in edge_stats.iterrows():
      pickup_node = row["pickup_node"]
      dropoff_node = row["dropoff_node"]
      
      # Get hourly data for this edge
      edge_hourly = hourly_stats[
        (hourly_stats["pickup_node"] == pickup_node) & 
        (hourly_stats["dropoff_node"] == dropoff_node)
      ]
      
      # Create hourly maps
      hourly_trips = {}
      hourly_avg_time = {}
      hourly_avg_price = {}
      
      for _, hourly_row in edge_hourly.iterrows():
        hour = int(hourly_row["hour"])
        hourly_trips[hour] = int(hourly_row["ride_id"])
        hourly_avg_time[hour] = float(hourly_row["duration_mins"])
        hourly_avg_price[hour] = float(hourly_row["fare_amount"])
      
      g.add_edge(
        pickup_node,
        dropoff_node,
        avg_time=float(row["duration_mins"]),
        avg_price=float(row["fare_amount"]),
        total_trips=int(row["ride_id"]),
        hourly_trips=hourly_trips,
        hourly_avg_time=hourly_avg_time,
        hourly_avg_price=hourly_avg_price,
      )
    city_graphs[int(city_id)] = g
  return city_graphs


def graph_to_cytoscape_elements(g: nx.DiGraph) -> list[dict]:
  """Convert a NetworkX graph to Cytoscape elements list for interactive UI rendering."""
  elements: list[dict] = []
  # Compute bounds for positions
  lat_vals = [float(d.get("lat", 0.0)) for _, d in g.nodes(data=True)]
  lon_vals = [float(d.get("lon", 0.0)) for _, d in g.nodes(data=True)]
  if lat_vals and lon_vals:
    lat_min, lat_max = min(lat_vals), max(lat_vals)
    lon_min, lon_max = min(lon_vals), max(lon_vals)
    lat_span = max(lat_max - lat_min, 1e-9)
    lon_span = max(lon_max - lon_min, 1e-9)
  else:
    lat_min = lat_max = lon_min = lon_max = 0.0
    lat_span = lon_span = 1.0
  # Nodes
  for node_id, data in g.nodes(data=True):
    lat_val = float(data.get("lat", 0.0))
    lon_val = float(data.get("lon", 0.0))
    # Normalize to a fixed canvas size
    x_pos = (lon_val - lon_min) / lon_span * 1000.0
    y_pos = (lat_val - lat_min) / lat_span * 800.0
    elements.append(
      {
        "data": {
          "id": node_id,
          "label": node_id,
          "lat": lat_val,
          "lon": lon_val,
        },
        "position": {"x": x_pos, "y": y_pos},
      }
    )
  # Edges
  for u, v, data in g.edges(data=True):
    elements.append(
      {
        "data": {
          "id": f"{u}->{v}",
          "source": u,
          "target": v,
          "avg_time": float(data.get("avg_time", 0.0)),
          "avg_price": float(data.get("avg_price", 0.0)),
          "total_trips": int(data.get("total_trips", 0)),
          "hourly_trips": data.get("hourly_trips", {}),
          "hourly_avg_time": data.get("hourly_avg_time", {}),
          "hourly_avg_price": data.get("hourly_avg_price", {}),
        }
      }
    )
  return elements


def save_graphs(graphs, output_dir="graphs"):
  """Save graphs to pickle file."""
  import pickle
  os.makedirs(output_dir, exist_ok=True)
  
  pickle_path = os.path.join(output_dir, "city_graphs.pkl")
  with open(pickle_path, 'wb') as f:
    pickle.dump(graphs, f)
  print(f"✓ Saved graphs to {pickle_path}")
  return pickle_path

if __name__ == "__main__":
  graphs = build_city_graphs(rides)
  
  # Save graphs
  save_graphs(graphs)
  
  # Print summary
  total_trips = sum(
    sum(d.get('total_trips', 0) for _, _, d in g.edges(data=True))
    for g in graphs.values()
  )
  
  print(f"\n✓ Built graphs for {len(graphs)} cities")
  print(f"✓ Total trips: {total_trips:,}")
  
  for city, g in graphs.items():
    city_trips = sum(d.get('total_trips', 0) for _, _, d in g.edges(data=True))
    print(f"  City {city}: {len(g.nodes)} clusters, {len(g.edges)} routes, {city_trips:,} trips")
