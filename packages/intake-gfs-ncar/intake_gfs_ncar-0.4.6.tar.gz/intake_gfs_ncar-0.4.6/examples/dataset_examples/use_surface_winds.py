#!/usr/bin/env python3
"""
Example script demonstrating how to use the gfs_surface_winds dataset from the GFS catalog.

This script:
1. Loads the pre-configured surface winds dataset from the catalog
2. Calculates wind speed and direction from U and V components
3. Creates a simple visualization of the wind field
4. Saves the processed data to a NetCDF file
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import cartopy.crs as ccrs
import intake
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def calculate_wind_speed_direction(u, v):
    """Calculate wind speed and direction from U and V components.

    Args:
        u: U-component of wind (m/s)
        v: V-component of wind (m/s)

    Returns:
        tuple: (wind_speed, wind_direction) where:
            - wind_speed is in m/s
            - wind_direction is in degrees (meteorological convention: 0° = N, 90° = E, etc.)
    """
    # Calculate wind speed (magnitude)
    wind_speed = np.sqrt(u**2 + v**2)

    # Calculate wind direction (meteorological convention: 0° = N, 90° = E, etc.)
    wind_dir = np.mod(270 - np.rad2deg(np.arctan2(v, u)), 360)

    return wind_speed, wind_dir


def plot_wind_field(ds, forecast_step=0, output_dir="gfs_output"):
    """Create a simple plot of wind vectors and speed.

    Args:
        ds: Dataset containing wind data
        forecast_step: Index of forecast step to plot
        output_dir: Directory to save the plot

    Returns:
        str: Path to the saved plot file
    """
    os.makedirs(output_dir, exist_ok=True)

    # Select the specified forecast step
    if "step" in ds.dims and ds.dims["step"] > 1:
        step_ds = ds.isel(step=forecast_step)
        step_value = ds.step.values[forecast_step]
        step_hours = step_value.astype("timedelta64[h]").astype(int)
        step_str = f"f{step_hours:03d}"
    else:
        step_ds = ds
        step_str = "f000"

    # Create the figure and map projection
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.coastlines()
    ax.gridlines(
        draw_labels=True, linewidth=0.5, color="gray", alpha=0.5, linestyle=":"
    )
    ax.set_global()

    # Subsample the data for cleaner vector plot (every 10th point)
    lats = step_ds.latitude.values
    lons = step_ds.longitude.values
    u = step_ds.u10.values
    v = step_ds.v10.values
    speed = step_ds.wind_speed.values

    # Subsample for plotting vectors
    stride = 10
    lats_sub = lats[::stride]
    lons_sub = lons[::stride]
    u_sub = u[::stride, ::stride]
    v_sub = u_sub.copy()  # Create properly sized array

    # Create meshgrid for the subsampled points
    lon_grid, lat_grid = np.meshgrid(lons_sub, lats_sub)

    # Plot wind speed as a filled contour
    speed_levels = np.arange(0, 30, 2)
    cs = ax.contourf(
        lons,
        lats,
        speed,
        levels=speed_levels,
        transform=ccrs.PlateCarree(),
        cmap="viridis",
        extend="max",
    )

    # Plot wind vectors
    q = ax.quiver(
        lon_grid,
        lat_grid,
        u_sub,
        v_sub,
        scale=700,
        transform=ccrs.PlateCarree(),
        color="white",
        alpha=0.6,
    )

    # Add a key for the wind vectors
    plt.quiverkey(q, 0.9, 0.9, 20, "20 m/s", labelpos="E", coordinates="figure")

    # Add colorbar
    cbar = plt.colorbar(cs, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("Wind Speed (m/s)")

    # Add title
    valid_time = step_ds.valid_time.values if "valid_time" in step_ds else "Unknown"
    plt.title(f"GFS Surface Wind (10m) - {valid_time}\nForecast Step: {step_str}")

    # Save the figure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"gfs_wind_map_{timestamp}_{step_str}.png")
    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Wind field plot saved to: {output_file}")
    return output_file


def main():
    """Main function to demonstrate using the gfs_surface_winds dataset."""
    try:
        logger.info("=== GFS Surface Wind Dataset Example ===")

        # Create output directory
        output_dir = "gfs_output"
        os.makedirs(output_dir, exist_ok=True)

        # Get the path to the catalog file
        catalog_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "intake_gfs_ncar",
            "gfs_catalog.yaml",
        )

        logger.info(f"Loading catalog from: {catalog_path}")
        cat = intake.open_catalog(catalog_path)

        # Use a recent date (3 days ago) to ensure data availability
        target_date = datetime.now(timezone.utc) - timedelta(days=3)
        # Round to nearest 6-hour cycle (00, 06, 12, 18Z)
        hour = (target_date.hour // 6) * 6
        target_cycle = target_date.replace(
            hour=hour, minute=0, second=0, microsecond=0
        ).isoformat()

        logger.info(f"Using cycle: {target_cycle}")

        # Get the surface winds dataset from the catalog
        # Note: This dataset is pre-configured with the appropriate filter keys
        source = cat.gfs_surface_winds(
            cycle=target_cycle, max_lead_time=24  # Get 24 hours of forecast data
        )

        logger.info("Reading surface wind data...")
        ds = source.read()

        if ds is None:
            raise ValueError("No data was returned from the source")

        logger.info(f"Successfully read data with variables: {list(ds.data_vars)}")
        logger.info(f"Coordinates: {list(ds.coords)}")
        logger.info(f"Dimensions: {dict(ds.dims)}")

        # Calculate wind speed and direction
        logger.info("Calculating wind speed and direction...")
        ds["wind_speed"], ds["wind_direction"] = calculate_wind_speed_direction(
            ds["u10"], ds["v10"]
        )

        # Add attributes
        ds["wind_speed"].attrs = {
            "long_name": "10m wind speed",
            "units": "m s-1",
            "standard_name": "wind_speed",
        }

        ds["wind_direction"].attrs = {
            "long_name": "10m wind direction",
            "units": "degrees",
            "standard_name": "wind_from_direction",
            "comment": "Meteorological convention: 0° = N, 90° = E, 180° = S, 270° = W",
        }

        # Create a plot for the initial time step (analysis)
        logger.info("Creating wind field visualization...")
        plot_file = plot_wind_field(ds, forecast_step=0, output_dir=output_dir)

        # Save the processed data to NetCDF
        try:
            cycle_dt = datetime.fromisoformat(target_cycle)
            date_str = cycle_dt.strftime("%Y%m%d")
            hour_str = cycle_dt.strftime("%H")
        except (ValueError, TypeError):
            # If parsing fails, use current time as fallback
            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y%m%d")
            hour_str = now.strftime("%H")
            logger.warning(
                f"Could not parse cycle datetime: {target_cycle}, using current time"
            )

        output_file = os.path.join(
            output_dir, f"gfs_surface_winds_{date_str}_{hour_str}z.nc"
        )

        logger.info(f"Saving processed data to {output_file}")
        encoding = {var: {"zlib": True, "complevel": 4} for var in ds.data_vars}

        ds.to_netcdf(
            output_file,
            encoding=encoding,
            format="NETCDF4",
            engine="netcdf4",
            mode="w",
        )

        logger.info(f"\nSuccess! Dataset saved to: {os.path.abspath(output_file)}")
        logger.info(f"Wind field visualization saved to: {os.path.abspath(plot_file)}")

        # Display a sample of the data
        if "step" in ds.dims and ds.dims["step"] > 1:
            logger.info("\nWind speed statistics by forecast step:")
            for step_idx in range(min(3, ds.dims["step"])):  # Show first 3 steps
                step_val = ds.step.values[step_idx].astype("timedelta64[h]").astype(int)
                step_ds = ds.isel(step=step_idx)
                logger.info(
                    f"  Step f{step_val:03d}: Wind speed {float(step_ds['wind_speed'].min().values):.2f} to "
                    f"{float(step_ds['wind_speed'].max().values):.2f} m/s, mean: "
                    f"{float(step_ds['wind_speed'].mean().values):.2f} m/s"
                )
        else:
            logger.info(
                f"\nWind speed range: {float(ds['wind_speed'].min().values):.2f} to "
                f"{float(ds['wind_speed'].max().values):.2f} m/s, mean: "
                f"{float(ds['wind_speed'].mean().values):.2f} m/s"
            )

    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
