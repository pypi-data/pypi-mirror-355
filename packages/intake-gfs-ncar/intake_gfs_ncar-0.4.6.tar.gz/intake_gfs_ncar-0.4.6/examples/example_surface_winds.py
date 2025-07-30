#!/usr/bin/env python3
"""
Example script to download and process GFS surface wind data (10m U and V components).

This script demonstrates how to:
1. Use the GFS intake catalog to access surface wind data
2. Download U and V wind components at 10m height
3. Calculate wind speed and direction
4. Save the results to a NetCDF file
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import intake
import numpy as np
import xarray as xr

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gfs_surface_winds.log"),
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
    # Note: Data should already be loaded into memory by the intake driver
    # No need to explicitly call load() again

    # Calculate wind speed (magnitude)
    wind_speed = np.sqrt(u**2 + v**2)

    # Calculate wind direction (meteorological convention: 0° = N, 90° = E, etc.)
    wind_dir = np.mod(270 - np.rad2deg(np.arctan2(v, u)), 360)

    return wind_speed, wind_dir


def get_surface_winds(
    cycle, forecast_hour="f000", output_dir="gfs_output", include_all_steps=True
):
    """Download and process GFS surface wind data.

    Args:
        cycle: ISO datetime string (YYYY-MM-DDTHH:MM:SS) or 'latest'
               Represents the model cycle time (e.g., '2025-01-01T00:00:00' for 00Z run)
        forecast_hour: Forecast hour (e.g., 'f000' for analysis, 'f003' for 3-hour forecast)
            Only used for output filename if include_all_steps=False
        output_dir: Directory to save output files
        include_all_steps: If True, include all available forecast steps up to max_lead_time

    Returns:
        str: Path to the output NetCDF file
    """
    try:
        logger.info(
            f"Processing surface wind data for cycle {cycle}, forecast hour {forecast_hour}"
        )

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Get the path to the catalog file
        catalog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "intake_gfs_ncar",
            "gfs_catalog.yaml",
        )

        logger.info(f"Loading catalog from: {catalog_path}")
        cat = intake.open_catalog(catalog_path)

        # Get the GFS forecast source
        # Use NetcdfSubset access method for better performance and variable filtering
        source = cat.gfs_forecast(
            cycle=cycle,
            access_method="ncss",  # Use NetcdfSubset for better performance
            cfgrib_filter_by_keys={
                "typeOfLevel": "heightAboveGround",
                "level": 10,  # 10m height
                "shortName": ["10u", "10v"],  # U and V components at 10m
            },
            max_lead_time=3,
        )

        logger.info("GFS source created with filter_by_keys:")
        for key, value in source.cfgrib_filter_by_keys.items():
            logger.info(f"  {key}: {value}")

        logger.info("Reading data...")
        ds = source.read()

        if ds is None:
            raise ValueError("No data was returned from the source")

        logger.info(f"Successfully read data. Variables: {list(ds.data_vars)}")

        # Calculate wind speed and direction
        # Handle different variable naming conventions
        u_var = None
        v_var = None
        
        # Check for NetCDF variable names (from NetcdfSubset)
        if "u-component_of_wind_height_above_ground" in ds and "v-component_of_wind_height_above_ground" in ds:
            u_var = ds["u-component_of_wind_height_above_ground"]
            v_var = ds["v-component_of_wind_height_above_ground"]
            logger.info("Found NetCDF wind variables: u-component_of_wind_height_above_ground, v-component_of_wind_height_above_ground")
        # Check for GRIB variable names (from fileServer/cfgrib)
        elif "u10" in ds and "v10" in ds:
            u_var = ds["u10"]
            v_var = ds["v10"]
            logger.info("Found GRIB wind variables: u10, v10")
        
        if u_var is not None and v_var is not None:
            logger.info("Calculating wind speed and direction...")
            ds["wind_speed"], ds["wind_direction"] = calculate_wind_speed_direction(
                u_var, v_var
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

            # Add global attributes
            ds.attrs.update(
                {
                    "title": "GFS 10m Surface Winds",
                    "source": "NOAA NCEP GFS",
                    "history": f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    "conventions": "CF-1.8",
                    "processing": "Calculated wind speed and direction from U and V components",
                }
            )

            # For filename, use the actual date we're processing
            if isinstance(cycle, str) and cycle.lower() == "latest":
                date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            elif isinstance(cycle, str):
                try:
                    date_str = datetime.fromisoformat(cycle).strftime("%Y%m%d")
                except ValueError:
                    # If not a valid ISO format, use the original date_str
                    date_str = cycle
            else:
                # Assume it's a datetime object
                date_str = cycle.strftime("%Y%m%d")

            # Save to NetCDF - if we have multiple forecast steps, include that in the filename
            if "step" in ds.coords and hasattr(ds.step, "size") and ds.step.size > 1:
                output_file = os.path.join(
                    output_dir,
                    f"gfs_surface_winds_{date_str}_f000-f{int(ds.step.max().values.astype('timedelta64[h]').astype(int)):03d}.nc",
                )
            else:
                output_file = os.path.join(
                    output_dir, f"gfs_surface_winds_{date_str}_{forecast_hour}.nc"
                )

            encoding = {var: {"zlib": True, "complevel": 4} for var in ds.data_vars}

            logger.info(f"Saving to {output_file}")
            ds.to_netcdf(
                output_file,
                encoding=encoding,
                format="NETCDF4",
                engine="netcdf4",
                mode="w",
            )

            logger.info("\nDataset summary:")
            logger.info(f"Variables: {list(ds.data_vars)}")
            logger.info(f"Dimensions: {dict(ds.dims)}")

            # If we have multiple steps, show statistics for each
            if "step" in ds.dims and ds.dims["step"] > 1:
                logger.info("Wind statistics by forecast step:")
                for step_idx in range(ds.dims["step"]):
                    step_val = (
                        ds.step.values[step_idx].astype("timedelta64[h]").astype(int)
                    )
                    step_ds = ds.isel(step=step_idx)
                    logger.info(
                        f"  Step f{step_val:03d}: Wind speed {float(step_ds['wind_speed'].min().values):.2f} to "
                        f"{float(step_ds['wind_speed'].max().values):.2f} m/s, "
                        f"Direction {float(step_ds['wind_direction'].min().values):.1f} to "
                        f"{float(step_ds['wind_direction'].max().values):.1f}°"
                    )
            else:
                logger.info(
                    f"Wind speed range: {float(ds['wind_speed'].min().values):.2f} to {float(ds['wind_speed'].max().values):.2f} m/s"
                )
                logger.info(
                    f"Wind direction range: {float(ds['wind_direction'].min().values):.1f} to {float(ds['wind_direction'].max().values):.1f}°"
                )

            return output_file

        else:
            available_vars = list(ds.data_vars.keys())
            logger.error(f"Available variables in dataset: {available_vars}")
            raise ValueError(
                "Required wind variables not found in the dataset. "
                "Expected either (u10, v10) or (u-component_of_wind_height_above_ground, v-component_of_wind_height_above_ground). "
                f"Available variables: {available_vars}"
            )

    except Exception as e:
        logger.error(f"Error processing surface wind data: {e}", exc_info=True)
        raise


def main():
    """Main function to run the example."""
    try:
        logger.info("=== GFS Surface Wind Data Example ===")

        # Use data from 7 days ago to ensure it's available (based on diagnostic testing)
        target_date = datetime.now(timezone.utc) - timedelta(days=7)
        # Round to nearest 00, 06, 12, 18Z cycle
        hour = (target_date.hour // 6) * 6
        target_cycle = target_date.replace(
            hour=hour, minute=0, second=0, microsecond=0
        ).isoformat()
        forecast_hour = "f000"  # Analysis time

        logger.info(f"Processing cycle: {target_cycle}, forecast hour: {forecast_hour}")

        # Get surface wind data with all available steps
        output_file = get_surface_winds(
            cycle=target_cycle,
            forecast_hour=forecast_hour,
            output_dir="gfs_output",
            include_all_steps=True,
        )

        logger.info(f"\nSuccess! Output saved to: {os.path.abspath(output_file)}")
        logger.info("\nTo load this data in Python, use:")
        logger.info(f"import xarray as xr")
        logger.info(f"ds = xr.open_dataset('{output_file}')")
        logger.info(f"# To access data for a specific forecast step:")
        logger.info(f"# step_data = ds.sel(step=ds.step[0])  # First forecast step")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
