# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p16_geospatial/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs geospatial analysis by identifying latitude and
#          longitude columns to prepare data for map visualization.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List, Tuple

# Import geospatial libraries, but handle potential ImportError
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEO_LIBRARIES_AVAILABLE = True
except ImportError:
    GEO_LIBRARIES_AVAILABLE = False


def _find_lat_lon_columns(columns: List[str]) -> Optional[Tuple[str, str]]:
    """Helper function to find likely latitude and longitude columns."""
    lat_names = ['latitude', 'lat', 'lat_dd', 'y']
    lon_names = ['longitude', 'lon', 'long', 'lng', 'lon_dd', 'x']

    lat_col, lon_col = None, None

    for col in columns:
        if col.lower() in lat_names:
            lat_col = col
            break
    for col in columns:
        if col.lower() in lon_names:
            lon_col = col
            break

    if lat_col and lon_col:
        return lat_col, lon_col
    return None


def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Identifies geospatial columns and prepares data for mapping.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, can be used for coloring points on map.

    Returns:
        A dictionary containing geospatial data ready for plotting.
    """
    print("     -> Performing geospatial analysis...")

    if not GEO_LIBRARIES_AVAILABLE:
        message = "Skipping geospatial analysis. Install with 'pip install \"decyphr[geo]\"' to enable."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Geospatial analysis requires 'column_details' from the overview plugin."}

    # --- 1. Find Latitude and Longitude columns ---
    lat_lon_pair = _find_lat_lon_columns(list(ddf.columns))
    if not lat_lon_pair:
        message = "Skipping geospatial analysis. No suitable latitude/longitude columns found."
        print(f"     ... {message}")
        return {"message": message}

    lat_col, lon_col = lat_lon_pair
    print(f"     ... Found potential geospatial columns: '{lat_col}' and '{lon_col}'.")

    try:
        # --- 2. Prepare data for plotting ---
        # We need the lat/lon columns and optionally the target column for coloring
        plot_cols = [lat_col, lon_col]
        if target_column:
            plot_cols.append(target_column)

        # Geospatial plotting is best with a sample of the data
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        SAMPLE_SIZE = 25000
        print(f"     ... Using a sample of up to {SAMPLE_SIZE} rows for map visualization.")
        if total_rows > SAMPLE_SIZE:
            geo_df = ddf[plot_cols].sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            geo_df = ddf[plot_cols].compute()

        geo_df = geo_df.dropna(subset=[lat_col, lon_col])

        if geo_df.empty:
            return {"message": "No valid geospatial data points after dropping NaNs."}

        results = {
            "geo_dataframe": geo_df.to_dict('list'),
            "lat_col": lat_col,
            "lon_col": lon_col,
            "target_col": target_column if target_column else None
        }

        print("     ... Geospatial analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during geospatial analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}