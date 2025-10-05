"""
Cluster Analysis Module

This module provides clustering functionality for ride-sharing data.
It uses DBSCAN with haversine distance to cluster pickup and dropoff points per city.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


def cluster_pickups_and_dropoffs_by_city(
    df: pd.DataFrame,
    *,
    city_col: str = "city_id",
    plat_col: str = "pickup_lat",
    plon_col: str = "pickup_lon",
    dlat_col: str = "drop_lat",
    dlon_col: str = "drop_lon",
    eps_m: float = 250.0,
    min_samples: int = 10,
    save_dir: Path | str = "city_cluster_plots",
    label_noise_as: str = "noise",  # or "-1" if you prefer
):
    """Cluster rides per city, using BOTH pickup and dropoff points.

    For each city:
      - Build one point set by stacking pickup and dropoff points (valid coords only).
      - Run DBSCAN with haversine distance.
      - Assign each row two labels:
          pickup_cluster  -> "c_<city>_<clusterID>" or "c_<city>_noise"
          dropoff_cluster -> "c_<city>_<clusterID>" or "c_<city>_noise"
      - Save one scatter plot per city (all points colored by cluster).

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing ride trip data
    city_col : str, default "city_id"
        Column name for city identifier
    plat_col : str, default "pickup_lat"
        Column name for pickup latitude
    plon_col : str, default "pickup_lon"
        Column name for pickup longitude
    dlat_col : str, default "drop_lat"
        Column name for dropoff latitude
    dlon_col : str, default "drop_lon"
        Column name for dropoff longitude
    eps_m : float, default 250.0
        Maximum distance (in meters) between two samples for them to be considered neighbors
    min_samples : int, default 10
        Minimum number of samples in a neighborhood for a point to be considered a core point
    save_dir : Path | str, default "city_cluster_plots"
        Directory path where cluster plots will be saved
    label_noise_as : str, default "noise"
        Label to use for noise points (can use "-1" if preferred)

    Returns
    -------
    out_df : pd.DataFrame
        A copy of df with new string columns: 'pickup_cluster', 'dropoff_cluster'.
    plot_paths : dict
        Dictionary mapping city values to PNG file paths: { city_value: path_to_png }

    Raises
    ------
    ValueError
        If required columns are missing from the DataFrame or no valid city ids exist

    """
    # Validate required columns
    for c in (city_col, plat_col, plon_col, dlat_col, dlon_col):
        if c not in df.columns:
            raise ValueError(f"Missing required column '{c}'. Columns present: {list(df.columns)}")

    out = df.copy()

    # Prepare output columns
    out["pickup_cluster"] = pd.NA
    out["dropoff_cluster"] = pd.NA

    # Keep only rows with valid city id
    valid_city_mask = out[city_col].notna()
    if not valid_city_mask.any():
        raise ValueError("No rows with a valid city id.")

    # Setup plotting output
    save_dir = Path(save_dir) if save_dir is not None else None
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)

    # eps (meters) -> radians for haversine
    eps_rad = eps_m / 6_371_000.0  # Earth radius in meters

    plot_paths = {}
    all_cities = np.sort(out.loc[valid_city_mask, city_col].unique())

    for city in all_cities:
        city_idx = out.index[out[city_col] == city]

        # Build coordinate arrays for pickups and dropoffs (valid only)
        pick_mask = out.loc[city_idx, plat_col].between(-90, 90) & out.loc[city_idx, plon_col].between(
            -180, 180
        )
        drop_mask = out.loc[city_idx, dlat_col].between(-90, 90) & out.loc[city_idx, dlon_col].between(
            -180, 180
        )

        pick_idx = city_idx[pick_mask.values]
        drop_idx = city_idx[drop_mask.values]

        # Nothing to cluster?
        if len(pick_idx) == 0 and len(drop_idx) == 0:
            continue

        # Stack both sets (each trip may contribute up to 2 points)
        parts = []
        if len(pick_idx) > 0:
            parts.append(out.loc[pick_idx, [plat_col, plon_col]].to_numpy(dtype=float))
        if len(drop_idx) > 0:
            parts.append(out.loc[drop_idx, [dlat_col, dlon_col]].to_numpy(dtype=float))

        coords_deg = np.vstack(parts)  # shape (N_total_points, 2)
        coords_rad = np.radians(coords_deg)

        # Fit DBSCAN on the union of points
        db = DBSCAN(
            eps=eps_rad,
            min_samples=min_samples,
            metric="haversine",
            algorithm="ball_tree",
        )
        labels_all = db.fit_predict(coords_rad)  # -1 = noise

        # Split labels back to pickup/dropoff sets in their original row indices
        n_pick = len(pick_idx)
        pick_labels = labels_all[:n_pick] if n_pick > 0 else np.array([], dtype=int)
        drop_labels = labels_all[n_pick:] if len(drop_idx) > 0 else np.array([], dtype=int)

        # Helper to stringify labels per spec c_<city>_<clusterID/noise>
        def fmt(lbl: int) -> str:
            if lbl == -1:
                tag = label_noise_as
            else:
                tag = str(lbl)
            return f"c_{city}_{tag}"

        # Write pickup cluster labels
        if n_pick > 0:
            out.loc[pick_idx, "pickup_cluster"] = [fmt(int(x)) for x in pick_labels]

        # Write dropoff cluster labels
        if len(drop_idx) > 0:
            out.loc[drop_idx, "dropoff_cluster"] = [fmt(int(x)) for x in drop_labels]

        # Plot one figure per city with ALL points, colored by cluster
        if save_dir is not None:
            plt.figure(figsize=(8, 8))
            unique_labels = np.unique(labels_all)

            # Pickup points first
            if n_pick > 0:
                for ul in unique_labels:
                    mask_ul = pick_labels == ul
                    if mask_ul.any():
                        pts = coords_deg[:n_pick][mask_ul]
                        lbl_name = "noise" if ul == -1 else f"cluster {ul}"
                        plt.scatter(pts[:, 1], pts[:, 0], s=6, label=f"pickup {lbl_name}")

            # Dropoff points next
            if len(drop_idx) > 0:
                offs = coords_deg[n_pick:]
                for ul in unique_labels:
                    mask_ul = drop_labels == ul
                    if mask_ul.any():
                        pts = offs[mask_ul]
                        lbl_name = "noise" if ul == -1 else f"cluster {ul}"
                        # no explicit color; matplotlib cycles but same label text differs
                        plt.scatter(pts[:, 1], pts[:, 0], s=6, marker="x", label=f"dropoff {lbl_name}")

            plt.title(
                f"DBSCAN clusters on pickup+dropoff (eps={eps_m}m, min_samples={min_samples}) — {city_col}={city}"
            )
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")

            # Keep legend readable if not too many entries
            handles, labels_txt = plt.gca().get_legend_handles_labels()
            if len(labels_txt) <= 24:
                plt.legend(markerscale=2, fontsize=8, loc="best")

            plt.tight_layout()
            png_path = save_dir / f"city_{city}_clusters_pick_drop.png"
            plt.savefig(png_path, dpi=150)
            plt.close()
            plot_paths[city] = str(png_path)

    return out, plot_paths


if __name__ == "__main__":
    # Example usage
    trips = pd.read_csv(Path("data/ride_trips.csv"), low_memory=False)

    labeled, plots = cluster_pickups_and_dropoffs_by_city(
        trips,
        city_col="city_id",
        plat_col="pickup_lat",
        plon_col="pickup_lon",
        dlat_col="drop_lat",
        dlon_col="drop_lon",
        eps_m=250,  # adjust to your city scale
        min_samples=10,  # lower if you want smaller clusters
        save_dir=Path("data/city_cluster_plots"),  # folder with per-city PNGs
    )

    # Save results
    labeled.to_csv("data/ride_trips_with_clusters.csv", index=False)
    print(f"Clustering complete. Plots saved: {plots}")
    print(f"\nFirst few rows with cluster labels:")
    print(labeled[["pickup_cluster", "dropoff_cluster"]].head())
