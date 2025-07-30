#!/usr/bin/env python3
"""
Robust test script for the GFS Intake driver and catalog.

This script provides a more robust way to test the GFS intake catalog with better
error handling and logging. It focuses on testing the driver's functionality
rather than just downloading data.
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
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gfs_intake_test.log"),
    ],
)
logger = logging.getLogger(__name__)


def get_catalog():
    """Load and return the GFS intake catalog."""
    try:
        # Get the path to the catalog file
        catalog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "intake_gfs_ncar",
            "gfs_catalog.yaml",
        )

        if not os.path.exists(catalog_path):
            raise FileNotFoundError(f"Catalog file not found at: {catalog_path}")

        logger.info(f"Loading catalog from: {catalog_path}")
        return intake.open_catalog(catalog_path)

    except Exception as e:
        logger.error(f"Failed to load catalog: {e}")
        raise


def test_catalog_loading():
    """Test if the catalog can be loaded successfully."""
    logger.info("\n=== Testing Catalog Loading ===")
    try:
        cat = get_catalog()
        logger.info("Successfully loaded catalog.")

        # List available sources
        sources = list(cat)
        logger.info(f"Available sources: {sources}")

        if not sources:
            logger.warning("No sources found in the catalog!")
            return False

        return True

    except Exception as e:
        logger.error(f"Catalog loading test failed: {e}")
        return False


def test_gfs_forecast_source():
    """Test the GFS forecast source with basic operations."""
    logger.info("\n=== Testing GFS Forecast Source ===")

    try:
        # Get the catalog
        cat = get_catalog()

        # Get the GFS forecast source
        if "gfs_forecast" not in cat:
            logger.error("GFS forecast source not found in catalog!")
            return False

        source = cat.gfs_forecast
        logger.info(f"Source description: {source.description}")

        # Test with a date that's likely to have data (7 days ago)
        target_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y%m%d"
        )
        logger.info(f"Testing with date: {target_date}")

        # Configure the source
        source = source(
            date_str=target_date,
            cfgrib_filter_by_keys={
                "typeOfLevel": "heightAboveGround",
                "level": 2,
                "shortName": "2t",  # 2m temperature
            },
        )

        # Test getting the schema
        try:
            schema = source._get_schema()
            logger.info(f"Schema: {schema}")
            logger.info("Successfully retrieved schema.")
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return False

        # Test reading a small chunk of data
        try:
            logger.info("Attempting to read data...")
            ds = source.read()

            if ds is None:
                logger.error("No data was returned from source.read()")
                return False

            logger.info(f"Successfully read data. Type: {type(ds)}")

            # Log basic info if we have a dataset
            if hasattr(ds, "data_vars"):
                logger.info(f"Variables: {list(ds.data_vars)}")
                logger.info(f"Dimensions: {dict(ds.dims)}")

                # Try to access a small portion of data
                if "t2m" in ds:
                    logger.info("Successfully accessed 't2m' variable")
                    logger.info(f"t2m shape: {ds['t2m'].shape}")
                    logger.info(f"t2m attributes: {ds['t2m'].attrs}")

            return True

        except Exception as e:
            logger.error(f"Error reading data: {e}")
            logger.exception("Full traceback:")
            return False

    except Exception as e:
        logger.error(f"GFS forecast source test failed: {e}")
        logger.exception("Full traceback:")
        return False


def main():
    """Run all tests and report results."""
    logger.info("Starting GFS Intake Driver Tests")
    logger.info("================================")

    test_results = {}

    # Run catalog loading test
    test_results["catalog_loading"] = test_catalog_loading()

    # Run GFS forecast source test
    test_results["gfs_forecast"] = test_gfs_forecast_source()

    # Print summary
    logger.info("\n=== Test Summary ===")
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name:20} {status}")

    # Return non-zero exit code if any test failed
    if not all(test_results.values()):
        logger.error("\nSome tests failed. Check the logs for details.")
        return 1

    logger.info("\nAll tests passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
