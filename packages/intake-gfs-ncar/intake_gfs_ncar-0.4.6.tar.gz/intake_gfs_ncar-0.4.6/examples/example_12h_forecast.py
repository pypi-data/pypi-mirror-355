#!/usr/bin/env python3
"""
Example using Intake to get 12 hours of GFS forecast surface wind data.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import intake
import numpy as np
import xarray as xr

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Create logs directory if it doesn't exist
logs_dir = os.path.join(script_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(
    logs_dir,
    f'gfs_12h_forecast_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.log',
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)],
)
logger = logging.getLogger(__name__)


def calculate_wind_speed_direction(u, v):
    """Calculate wind speed and direction from U and V components.

    Args:
        u: U-component of wind (m/s) - can be xarray DataArray or numpy array
        v: V-component of wind (m/s) - can be xarray DataArray or numpy array

    Returns:
        tuple: (wind_speed, wind_direction) where:
            - wind_speed is in m/s
            - wind_direction is in degrees (meteorological convention: 0° = N, 90° = E, etc.)
    """
    # Ensure we're working with numpy arrays
    u_data = u.values if hasattr(u, "values") else u
    v_data = v.values if hasattr(v, "values") else v

    # Calculate wind speed (magnitude)
    wind_speed = np.sqrt(u_data**2 + v_data**2)

    # Calculate wind direction (meteorological convention: 0° = N, 90° = E, etc.)
    wind_dir = np.mod(270 - np.rad2deg(np.arctan2(v_data, u_data)), 360)

    return wind_speed, wind_dir


def get_12h_forecast_winds(date_str, model_run="00"):
    """Get 12-hour forecast wind data for the specified date and model run.

    Args:
        date_str: Date string in YYYYMMDD format or 'latest'
        model_run: Model run time ('00', '06', '12', or '18')

    Returns:
        xarray.Dataset: Dataset containing wind data or None if an error occurs
    """
    try:
        logger.info(
            f"Getting 12h forecast wind data for {date_str}, model run {model_run}Z"
        )

        # Load the catalog
        catalog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "intake_gfs_ncar",
            "gfs_catalog.yaml",
        )
        logger.info(f"Loading catalog from: {catalog_path}")

        # Open the catalog
        try:
            cat = intake.open_catalog(catalog_path)
            logger.info(f"Available sources: {list(cat)}")
        except Exception as e:
            logger.error(f"Failed to open catalog: {e}")
            return None

        # Get the source for GFS forecast data
        try:
            logger.info("Creating GFS forecast source...")
            source = cat.gfs_forecast(
                date_str=date_str,
                model_run_time=model_run,
                max_lead_time_fXXX="f012",  # 12-hour forecast
                cfgrib_filter_by_keys={
                    "typeOfLevel": "heightAboveGround",
                    "level": 10,  # 10m height
                    "shortName": ["10u", "10v"],  # U and V components at 10m
                },
            )
            logger.info("Source created successfully")

            # Read the data with explicit loading into memory
            logger.info("Reading and loading data into memory...")

            try:
                # Read the data into memory
                logger.info("Reading data...")

                # Read the data directly into memory
                ds = source.read()

                if ds is None:
                    logger.error("No data was returned from the source")
                    return None

                logger.info(f"Successfully read data. Variables: {list(ds.data_vars)}")

                # Create a new dataset with numpy arrays to ensure data is in memory
                logger.info("Creating new dataset with numpy arrays...")
                new_data_vars = {}

                try:
                    # Process each variable
                    for var_name in ds.data_vars:
                        try:
                            logger.info(f"Processing {var_name}...")
                            var = ds[var_name]

                            # Convert to numpy array to ensure data is in memory
                            data = np.asarray(var.values, dtype=var.dtype)

                            # Get coordinates for this variable
                            coords = {}
                            for dim in var.dims:
                                if dim in ds.coords:
                                    coords[dim] = np.asarray(ds[dim].values)

                            # Create new DataArray with the same metadata
                            new_data_vars[var_name] = xr.DataArray(
                                data=data, dims=var.dims, coords=coords, attrs=var.attrs
                            )
                            logger.info(f"  {var_name} processed successfully")

                        except Exception as e:
                            logger.error(
                                f"Error processing {var_name}: {e}", exc_info=True
                            )
                            raise

                    # Create new dataset with the loaded data
                    ds = xr.Dataset(data_vars=new_data_vars, attrs=ds.attrs)

                    logger.info("All data loaded into memory successfully")

                except Exception as e:
                    logger.error(
                        f"Error creating in-memory dataset: {e}", exc_info=True
                    )
                    return None

            except Exception as e:
                logger.error(f"Error loading data into memory: {e}", exc_info=True)
                return None

            # At this point, all data should already be in memory as numpy arrays
            logger.info("Verifying data is in memory...")
            for var in ds.data_vars:
                if not isinstance(ds[var].values, np.ndarray):
                    logger.error(f"Variable {var} is not a numpy array!")
                    return None

            logger.info("All data verified to be in memory")

            # Calculate wind speed and direction if we have the required variables
            if "u10" in ds and "v10" in ds:
                logger.info("Calculating wind speed and direction...")

                try:
                    # Get the data (should already be numpy arrays)
                    u10 = ds["u10"].values
                    v10 = ds["v10"].values

                    # Calculate wind speed and direction
                    logger.info("Calculating wind speed...")
                    wind_speed = np.sqrt(u10**2 + v10**2)

                    logger.info("Calculating wind direction...")
                    wind_dir = np.mod(270 - np.rad2deg(np.arctan2(v10, u10)), 360)

                    # Create new DataArrays with the same coordinates as u10
                    logger.info("Creating wind speed DataArray...")
                    wind_speed_da = xr.DataArray(
                        data=wind_speed,
                        dims=ds["u10"].dims,
                        coords={dim: ds[dim] for dim in ds["u10"].dims},
                        attrs={
                            "long_name": "10m wind speed",
                            "units": "m s-1",
                            "standard_name": "wind_speed",
                        },
                    )

                    logger.info("Creating wind direction DataArray...")
                    wind_dir_da = xr.DataArray(
                        data=wind_dir,
                        dims=ds["u10"].dims,
                        coords={dim: ds[dim] for dim in ds["u10"].dims},
                        attrs={
                            "long_name": "10m wind direction",
                            "units": "degrees",
                            "standard_name": "wind_from_direction",
                            "comment": "Meteorological convention: 0° = N, 90° = E, 180° = S, 270° = W",
                            "valid_range": [0, 360],
                        },
                    )

                    # Add to dataset
                    logger.info("Adding wind fields to dataset...")
                    ds["wind_speed"] = wind_speed_da
                    ds["wind_direction"] = wind_dir_da

                    # Ensure data is in memory
                    ds["wind_speed"].load()
                    ds["wind_direction"].load()

                    logger.info("Wind calculations completed successfully")

                except Exception as e:
                    logger.error(f"Error calculating wind fields: {e}", exc_info=True)
                    return None

            return ds

        except Exception as e:
            logger.error(f"Error processing data: {e}", exc_info=True)
            return None

    except Exception as e:
        logger.error(f"Unexpected error in get_12h_forecast_winds: {e}", exc_info=True)
        return None


def main():
    """Main function to demonstrate fetching and processing GFS 12-hour forecast data."""
    try:
        logger.info("=== GFS 12-Hour Forecast Wind Data ===\n")

        # Get data for 3 days ago to ensure it's available
        target_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime(
            "%Y%m%d"
        )
        model_run = "00"  # 00Z model run

        logger.info(f"Date: {target_date}, Model run: {model_run}Z")

        # Get the data
        logger.info("Fetching GFS forecast data...")
        try:
            ds = get_12h_forecast_winds(date_str=target_date, model_run=model_run)

            if ds is None or not isinstance(ds, xr.Dataset):
                logger.error("Failed to retrieve valid GFS forecast data")
                return 1

            logger.info("\n=== Data Summary ===")
            logger.info(f"Dataset dimensions: {dict(ds.dims)}")
            logger.info(f"Coordinates: {list(ds.coords)}")
            logger.info(f"Variables: {list(ds.data_vars)}")

            # Print statistics for each variable
            for var in ds.data_vars:
                try:
                    var_data = ds[var]
                    logger.info(f"\n{var}:")
                    logger.info(f"  Shape: {var_data.shape}")
                    logger.info(f"  Dtype: {var_data.dtype}")

                    # Safely calculate statistics
                    try:
                        min_val = float(var_data.min().values)
                        max_val = float(var_data.max().values)
                        mean_val = float(var_data.mean().values)
                        logger.info(f"  Min: {min_val:.2f}")
                        logger.info(f"  Max: {max_val:.2f}")
                        logger.info(f"  Mean: {mean_val:.2f}")
                    except Exception as e:
                        logger.warning(f"  Could not calculate statistics: {e}")

                    # Log units if available
                    if hasattr(var_data, "attrs") and "units" in var_data.attrs:
                        logger.info(f"  Units: {var_data.attrs['units']}")

                except Exception as e:
                    logger.warning(f"  Could not process variable {var}: {e}")

            logger.info("\n=== Example Data ===")
            # Print a small sample of the data
            try:
                if "latitude" in ds and "longitude" in ds:
                    # Get a central point
                    lat_mid = len(ds.latitude) // 2
                    lon_mid = len(ds.longitude) // 2

                    logger.info(f"\nData at point (lat[{lat_mid}], lon[{lon_mid}]):")
                    point_data = ds.isel(latitude=lat_mid, longitude=lon_mid)

                    for var in point_data.data_vars:
                        try:
                            var_data = point_data[var]
                            logger.info(f"{var}: {var_data.values}")
                        except Exception as e:
                            logger.warning(f"  Could not read {var}: {e}")
                else:
                    logger.warning(
                        "Could not find latitude/longitude coordinates for sample data"
                    )

            except Exception as e:
                logger.warning(f"Could not generate sample data: {e}")

            return 0

        except Exception as e:
            logger.error(f"Error processing GFS data: {e}", exc_info=True)
            return 1

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
