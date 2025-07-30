#!/usr/bin/env python3
"""
Test script for the GFS Intake driver and catalog.

This script demonstrates how to use the GFS intake catalog to access and work with
GFS forecast data. It shows how to:
1. Load the catalog
2. List available data sources
3. Access GFS forecast data
4. Read and process the data

Example:
    python test_intake_driver.py
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import intake
import xarray as xr

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_catalog():
    """Load the GFS intake catalog."""
    try:
        # Get the path to the catalog file
        catalog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "intake_gfs_ncar",
            "gfs_catalog.yaml",
        )

        logger.info(f"Loading catalog from: {catalog_path}")

        # Load the catalog
        cat = intake.open_catalog(catalog_path)

        # List available sources
        logger.info("Available sources in catalog:")
        for name in cat:
            logger.info(f"  - {name}")

        return cat

    except Exception as e:
        logger.error(f"Failed to load catalog: {e}")
        raise


def test_gfs_forecast_source(cat, date_str=None, lead_time="f000"):
    """Test the GFS forecast data source.

    Args:
        cat: The intake catalog
        date_str: Date string in YYYYMMDD format or 'latest'
        lead_time: Forecast lead time (e.g., 'f000' for analysis, 'f003' for 3-hour forecast)
    """
    try:
        logger.info("\n=== Testing GFS Forecast Source ===")

        # Get the GFS forecast source
        source = cat.gfs_forecast

        # Update parameters if provided
        if date_str is not None:
            source = source(date_str=date_str)

        logger.info(f"Source description: {source.description}")
        logger.info(f"Source metadata: {source.metadata}")

        # Get the schema
        logger.info("\nGetting schema...")
        schema = source._get_schema()
        logger.info(f"Schema: {schema}")

        # Read a small subset of the data
        logger.info("\nReading data...")

        # Configure to read only the 2m temperature
        source = source(
            cfgrib_filter_by_keys={
                "typeOfLevel": "heightAboveGround",
                "level": 2,
                "shortName": "2t",
            }
        )

        # Read the data - use read() instead of to_dask()
        logger.info("Reading data from source...")
        ds = source.read()

        # Log basic information about the dataset
        logger.info(f"\nDataset info:")
        logger.info(f"Dataset type: {type(ds)}")

        # Check if we got a valid dataset
        if hasattr(ds, "data_vars"):
            logger.info(f"Variables: {list(ds.data_vars)}")
            logger.info(f"Dimensions: {dict(ds.dims)}")

            # Convert temperature from Kelvin to Celsius for display
            if "t2m" in ds:
                logger.info("\nTemperature statistics (2m above ground):")
                logger.info(f"  Min: {float(ds['t2m'].min().values):.2f} K")
                logger.info(f"  Max: {float(ds['t2m'].max().values):.2f} K")
                logger.info(f"  Mean: {float(ds['t2m'].mean().values):.2f} K")
        else:
            logger.warning(f"Unexpected return type from source.read(): {type(ds)}")
            logger.warning(f"Returned object: {ds}")

        return ds

    except Exception as e:
        logger.error(f"Error testing GFS forecast source: {e}", exc_info=True)
        raise


def main():
    """Main function to test the GFS intake driver."""
    try:
        logger.info("Starting GFS Intake Driver Test")

        # Load the catalog
        cat = load_catalog()

        # Test with a specific date that has data (2 days ago to ensure availability)
        target_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
            "%Y%m%d"
        )
        logger.info(f"\n=== Testing with specific date: {target_date} ===")

        # Test with specific parameters
        ds = test_gfs_forecast_source(
            cat, date_str=target_date, lead_time="f000"  # Analysis time
        )

        if ds is not None:
            logger.info("\nSuccessfully retrieved GFS data!")

            # If we have a valid dataset, show more info
            if hasattr(ds, "data_vars"):
                logger.info("\nAvailable variables:")
                for var_name, var in ds.data_vars.items():
                    logger.info(
                        f"- {var_name}: {var.dims} {var.attrs.get('long_name', '')}"
                    )

        logger.info("\nTest completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
