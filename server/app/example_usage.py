"""Simple example of how to use the graph builder."""

import pickle

from graph_builder import build_city_graphs, rides, save_graphs


def main():
  """Example usage of the simplified graph builder."""
  print("=== GRAPH BUILDER EXAMPLE ===\n")

  # 1. Build graphs from CSV data
  print("Building graphs...")
  graphs = build_city_graphs(rides)

  # 2. Save graphs
  print("Saving graphs...")
  save_graphs(graphs)

  # 3. Display summary
  total_trips = sum(
    sum(d.get("total_trips", 0) for _, _, d in g.edges(data=True)) for g in graphs.values()
  )

  print("\n=== SUMMARY ===")
  print(f"Built graphs for {len(graphs)} cities")
  print(f"Total trips analyzed: {total_trips:,}")

  for city_id, graph in graphs.items():
    city_trips = sum(d.get("total_trips", 0) for _, _, d in graph.edges(data=True))
    print(f"\nCity {city_id}:")
    print(f"  - {len(graph.nodes)} clusters")
    print(f"  - {len(graph.edges)} routes")
    print(f"  - {city_trips:,} trips")

  # 4. Example: Access a specific graph
  if 3 in graphs:
    city_3_graph = graphs[3]
    print("\n=== CITY 3 GRAPH DETAILS ===")
    print(f"Nodes: {list(city_3_graph.nodes())}")
    print("First few edges:")
    for i, (u, v, data) in enumerate(city_3_graph.edges(data=True)):
      if i >= 3:
        break
      print(f"  {u} -> {v}: {data['total_trips']} trips, {data['avg_time']:.1f}min avg")

  # 5. Example: Load saved graphs
  print("\n=== LOADING SAVED GRAPHS ===")
  try:
    with open("graphs/city_graphs.pkl", "rb") as f:
      loaded_graphs = pickle.load(f)
    print(f"✓ Successfully loaded {len(loaded_graphs)} city graphs from file")
  except FileNotFoundError:
    print("✗ No saved graphs found")

  print("\n=== FILES CREATED ===")
  print("- graphs/city_graphs.pkl (Python pickle format)")

  print("\n=== DONE ===")


if __name__ == "__main__":
  main()
