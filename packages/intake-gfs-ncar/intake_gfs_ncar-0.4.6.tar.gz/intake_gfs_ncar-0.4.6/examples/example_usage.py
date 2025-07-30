#!/usr/bin/env python3
"""
Example usage of the GFS intake driver.

This script demonstrates how to use the GFS intake driver to access GFS forecast data.
"""

import logging
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone

import cfgrib
import fsspec
import xarray as xr

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Add a file handler to save logs to a file
log_file = "gfs_download.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.info(f"Logging to {os.path.abspath(log_file)}")


def download_file(url, output_path):
    """Download a file from a URL to the specified path."""
    logger.info(f"Downloading {url} to {output_path}")
    with (
        urllib.request.urlopen(url, timeout=60) as response,
        open(output_path, "wb") as out_file,
    ):
        # Get file size from headers if available
        file_size = int(response.headers.get("Content-Length", 0))
        if file_size > 0:
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")

        # Download in chunks to show progress
        chunk_size = 1024 * 1024  # 1MB chunks
        downloaded = 0
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if file_size > 0:
                progress = (downloaded / file_size) * 100
                logger.info(
                    f"Downloaded {downloaded / (1024*1024):.1f} MB ({progress:.1f}%)"
                )

    # Verify the downloaded file
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise IOError(f"Downloaded file is empty or does not exist: {output_path}")

    logger.info(
        f"Successfully downloaded {os.path.getsize(output_path) / (1024*1024):.2f} MB"
    )
    return output_path


def download_gfs_2m_temperature(
    date_str, model_run_time=0, forecast_hour=0, output_dir="."
):
    """
    Download and process GFS 2m temperature data.

    Args:
        date_str: Date string in YYYYMMDD format
        model_run_time: Model run time (0-23)
        forecast_hour: Forecast hour (0-384)
        output_dir: Directory to save the output files
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Format the base URL for NCAR THREDDS server
        base_url = "https://thredds.rda.ucar.edu/thredds/dodsC/files/g/d084001"
        model_run_str = f"{model_run_time:02d}"  # Zero-padded to 2 digits
        forecast_str = f"{forecast_hour:03d}"  # Zero-padded to 3 digits

        # Construct the GRIB2 file URL for NCAR THREDDS
        grib_url = f"{base_url}/{date_str[:4]}/{date_str}/gfs.0p25.{date_str}{model_run_str}.f{forecast_str}.grib2"

        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory(prefix="gfs_") as temp_dir:
            # Download the GRIB file
            grib_file = os.path.join(
                temp_dir, f"gfs.t{model_run_str}z.pgrb2.0p25.f{forecast_str}"
            )
            download_file(grib_url, grib_file)

            # Open the GRIB file with cfgrib to extract 2m temperature
            logger.info("Opening GRIB file with cfgrib...")

            # First, let's see what's in the file
            try:
                # Try to open with specific filter for 2m temperature
                filter_params = {
                    "typeOfLevel": "heightAboveGround",
                    "level": 2,
                    "shortName": "2t",  # 2m temperature
                }

                logger.info(f"Reading 2m temperature data with filter: {filter_params}")

                # Open the dataset with cfgrib
                ds = xr.open_dataset(
                    grib_file,
                    engine="cfgrib",
                    backend_kwargs={
                        "filter_by_keys": filter_params,
                        "errors": "ignore",  # Ignore warnings about multiple messages
                    },
                )

                # Check if we got any data
                if not ds.data_vars:
                    logger.warning(
                        "No variables found in the dataset. Trying to list available variables..."
                    )

                    # If no data, try to list available variables
                    available_vars = {}
                    with fsspec.open(grib_file, "rb") as f:
                        for msg in cfgrib.open_file(f):
                            var_name = msg.get("shortName", "unknown")
                            level_type = msg.get("typeOfLevel", "unknown")
                            level = msg.get("level", "unknown")

                            if level_type not in available_vars:
                                available_vars[level_type] = {}
                            if var_name not in available_vars[level_type]:
                                available_vars[level_type][var_name] = []
                            available_vars[level_type][var_name].append(level)

                    # Log available variables
                    logger.info("Available variables in the GRIB file:")
                    for level_type, vars_dict in available_vars.items():
                        for var_name, levels in vars_dict.items():
                            logger.info(f"  {level_type}.{var_name}: {sorted(levels)}")

                    raise ValueError("No 2m temperature data found in the GRIB file")

                # Log dataset info
                logger.info("Successfully opened dataset:")
                logger.info(f"Variables: {list(ds.data_vars.keys())}")
                logger.info(f"Dimensions: {dict(ds.dims)}")

                # Convert temperature from Kelvin to Celsius
                if "t2m" in ds:
                    # Create a new variable for Celsius
                    ds["t2m_celsius"] = ds["t2m"] - 273.15
                    ds["t2m_celsius"].attrs = {
                        "long_name": "2m Temperature",
                        "units": "°C",
                        "standard_name": "air_temperature",
                        "description": "2m temperature in Celsius",
                    }

                    # Add original Kelvin data as well
                    ds["t2m_kelvin"] = ds["t2m"]

                # Add global attributes
                ds.attrs.update(
                    {
                        "title": "GFS 2m Temperature Forecast",
                        "source": "NOAA NCEP GFS",
                        "history": f'Generated on {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")}',
                        "conventions": "CF-1.8",
                        "source_url": grib_url,
                        "processing": "Converted from GRIB2 to NetCDF with xarray and cfgrib",
                    }
                )

                # Save to NetCDF
                output_file = os.path.join(
                    output_dir,
                    f"gfs_2m_temperature_{date_str}_{model_run_str}z_f{forecast_str}.nc",
                )

                # Configure encoding for better compression
                encoding = {
                    var: {
                        "zlib": True,
                        "complevel": 4,
                        "dtype": "float32" if var != "time" else "int32",
                    }
                    for var in ds.data_vars
                }

                # Save the dataset
                logger.info(f"Saving to {output_file}")
                ds.to_netcdf(
                    output_file,
                    encoding=encoding,
                    format="NETCDF4",
                    engine="netcdf4",
                    mode="w",
                )

                # Print file info
                file_size = os.path.getsize(output_file) / (1024 * 1024)  # in MB
                logger.info(f"Successfully saved {file_size:.2f} MB to {output_file}")

                return output_file

            except Exception as e:
                logger.error(f"Error processing GRIB file: {e}", exc_info=True)
                raise

    except Exception as e:
        logger.error(f"Error in download_gfs_2m_temperature: {e}", exc_info=True)
        raise


def main():
    """Main function to demonstrate GFS 2m temperature data download."""
    try:
        # Use a date from 3 days ago to ensure data is available
        date_str = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y%m%d")
        model_run_time = 0  # 00Z run
        forecast_hour = 0  # Analysis (0-hour forecast)

        logger.info(
            f"Starting GFS 2m temperature data download for {date_str} {model_run_time:02d}Z"
        )

        # Create an output directory for this run
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "gfs_output"
        )
        os.makedirs(output_dir, exist_ok=True)

        # Download and process the data
        output_file = download_gfs_2m_temperature(
            date_str=date_str,
            model_run_time=model_run_time,
            forecast_hour=forecast_hour,
            output_dir=output_dir,
        )

        logger.info(f"Processing complete. Output file: {output_file}")

        # Open and display info about the saved file
        if output_file and os.path.exists(output_file):
            logger.info("\nContents of the saved NetCDF file:")
            with xr.open_dataset(output_file) as ds:
                logger.info(ds)

                # Print summary of variables
                logger.info("\nVariables in the dataset:")
                for var_name, var in ds.data_vars.items():
                    logger.info(f"\n{var_name}:")
                    logger.info(f"  Dimensions: {var.dims}")
                    logger.info(f"  Shape: {var.shape}")
                    logger.info(f"  Attributes: {var.attrs}")

                    # Print min/max values if it's a data variable (not a coordinate)
                    if var_name not in ds.coords:
                        try:
                            logger.info(
                                f"  Min: {float(var.min().values):.2f} {var.attrs.get('units', '')}"
                            )
                            logger.info(
                                f"  Max: {float(var.max().values):.2f} {var.attrs.get('units', '')}"
                            )
                        except Exception as e:
                            logger.warning(f"  Could not compute min/max: {e}")

        return output_file

    except Exception as e:
        logger.error(f"An error occurred in main: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    try:
        output_file = main()
        if output_file and os.path.exists(output_file):
            logger.info(
                f"\nSuccess! Output file saved to: {os.path.abspath(output_file)}"
            )

            # Print file info
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # in MB
            logger.info(f"File size: {file_size:.2f} MB")

            # Show the first few lines of the log file
            try:
                with open("gfs_download.log", "r") as f:
                    log_lines = f.readlines()
                    logger.info("\n=== Log File Summary ===")
                    logger.info("".join(log_lines[-20:]))  # Show last 20 lines of log
            except Exception as e:
                logger.warning(f"Could not read log file: {e}")

        else:
            logger.error(
                "Processing completed with errors. Check the log file for details."
            )

        logger.info("Done!")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up any open resources
        logger.info("Cleanup completed")
