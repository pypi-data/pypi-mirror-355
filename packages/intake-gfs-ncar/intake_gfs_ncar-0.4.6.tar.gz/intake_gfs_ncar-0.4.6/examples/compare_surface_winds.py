#!/usr/bin/env python3
"""
Comparison script to test both surface wind data approaches.

This script runs both the original example (using gfs_forecast with manual filters)
and the new catalog-based example (using gfs_surface_winds dataset) to verify
they produce equivalent results.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import xarray as xr

# Import both example functions
from example_surface_winds import get_surface_winds
from example_surface_winds_catalog import get_surface_winds_from_catalog

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("compare_surface_winds.log"),
    ],
)
logger = logging.getLogger(__name__)


def compare_datasets(file1, file2):
    """Compare two NetCDF files with wind data.
    
    Args:
        file1: Path to first NetCDF file
        file2: Path to second NetCDF file
        
    Returns:
        bool: True if datasets are equivalent, False otherwise
    """
    try:
        logger.info(f"Comparing datasets:")
        logger.info(f"  File 1: {file1}")
        logger.info(f"  File 2: {file2}")
        
        # Load both datasets
        ds1 = xr.open_dataset(file1)
        ds2 = xr.open_dataset(file2)
        
        logger.info(f"Dataset 1 variables: {list(ds1.data_vars)}")
        logger.info(f"Dataset 2 variables: {list(ds2.data_vars)}")
        
        # Check dimensions
        if ds1.dims != ds2.dims:
            logger.warning(f"Dimensions differ: {ds1.dims} vs {ds2.dims}")
            return False
        
        # Find wind variables in both datasets
        wind_vars_1 = {}
        wind_vars_2 = {}
        
        # Check for wind variables in dataset 1
        if "u10" in ds1 and "v10" in ds1:
            wind_vars_1 = {"u": ds1["u10"], "v": ds1["v10"]}
        elif "u-component_of_wind_height_above_ground" in ds1 and "v-component_of_wind_height_above_ground" in ds1:
            wind_vars_1 = {
                "u": ds1["u-component_of_wind_height_above_ground"],
                "v": ds1["v-component_of_wind_height_above_ground"]
            }
        
        # Check for wind variables in dataset 2
        if "u10" in ds2 and "v10" in ds2:
            wind_vars_2 = {"u": ds2["u10"], "v": ds2["v10"]}
        elif "u-component_of_wind_height_above_ground" in ds2 and "v-component_of_wind_height_above_ground" in ds2:
            wind_vars_2 = {
                "u": ds2["u-component_of_wind_height_above_ground"],
                "v": ds2["v-component_of_wind_height_above_ground"]
            }
        
        if not wind_vars_1 or not wind_vars_2:
            logger.error("Could not find wind variables in one or both datasets")
            return False
        
        # Compare wind components
        u_diff = float((wind_vars_1["u"] - wind_vars_2["u"]).abs().max().values)
        v_diff = float((wind_vars_1["v"] - wind_vars_2["v"]).abs().max().values)
        
        logger.info(f"Maximum U-component difference: {u_diff:.6f} m/s")
        logger.info(f"Maximum V-component difference: {v_diff:.6f} m/s")
        
        # Compare calculated wind speed and direction if available
        if "wind_speed" in ds1 and "wind_speed" in ds2:
            speed_diff = float((ds1["wind_speed"] - ds2["wind_speed"]).abs().max().values)
            logger.info(f"Maximum wind speed difference: {speed_diff:.6f} m/s")
        
        if "wind_direction" in ds1 and "wind_direction" in ds2:
            dir_diff = float((ds1["wind_direction"] - ds2["wind_direction"]).abs().max().values)
            logger.info(f"Maximum wind direction difference: {dir_diff:.6f} degrees")
        
        # Consider datasets equivalent if differences are very small (numerical precision)
        tolerance = 1e-6
        equivalent = u_diff < tolerance and v_diff < tolerance
        
        if equivalent:
            logger.info("✓ Datasets are equivalent within numerical precision")
        else:
            logger.warning("✗ Datasets have significant differences")
        
        # Close datasets
        ds1.close()
        ds2.close()
        
        return equivalent
        
    except Exception as e:
        logger.error(f"Error comparing datasets: {e}", exc_info=True)
        return False


def main():
    """Main function to run the comparison."""
    try:
        logger.info("=== GFS Surface Wind Data Comparison ===")
        
        # Use data from 7 days ago to ensure it's available
        target_date = datetime.now(timezone.utc) - timedelta(days=7)
        # Round to nearest 00, 06, 12, 18Z cycle
        hour = (target_date.hour // 6) * 6
        target_cycle = target_date.replace(
            hour=hour, minute=0, second=0, microsecond=0
        ).isoformat()
        forecast_hour = "f000"
        
        logger.info(f"Processing cycle: {target_cycle}, forecast hour: {forecast_hour}")
        
        # Create separate output directories for comparison
        output_dir1 = "gfs_output/original"
        output_dir2 = "gfs_output/catalog"
        
        logger.info("\n1. Running original example (gfs_forecast with manual filters)...")
        try:
            output_file1 = get_surface_winds(
                cycle=target_cycle,
                forecast_hour=forecast_hour,
                output_dir=output_dir1,
                include_all_steps=True,
            )
            logger.info(f"Original example completed: {output_file1}")
        except Exception as e:
            logger.error(f"Original example failed: {e}")
            output_file1 = None
        
        logger.info("\n2. Running catalog-based example (gfs_surface_winds dataset)...")
        try:
            output_file2 = get_surface_winds_from_catalog(
                cycle=target_cycle,
                forecast_hour=forecast_hour,
                output_dir=output_dir2,
                max_lead_time=3,
            )
            logger.info(f"Catalog example completed: {output_file2}")
        except Exception as e:
            logger.error(f"Catalog example failed: {e}")
            output_file2 = None
        
        # Compare results if both succeeded
        if output_file1 and output_file2:
            logger.info("\n3. Comparing results...")
            equivalent = compare_datasets(output_file1, output_file2)
            
            if equivalent:
                logger.info("\n✓ SUCCESS: Both approaches produce equivalent results!")
                logger.info("The gfs_surface_winds catalog dataset works correctly.")
            else:
                logger.warning("\n✗ WARNING: Results differ between approaches")
                logger.warning("This may indicate an issue with the catalog configuration.")
        elif output_file1:
            logger.warning("\nOnly original example succeeded - catalog dataset may have issues")
        elif output_file2:
            logger.warning("\nOnly catalog example succeeded - original approach may have issues")
        else:
            logger.error("\nBoth examples failed - check network connectivity and data availability")
            return 1
        
        logger.info("\nComparison complete!")
        logger.info("Files generated:")
        if output_file1:
            logger.info(f"  Original: {os.path.abspath(output_file1)}")
        if output_file2:
            logger.info(f"  Catalog:  {os.path.abspath(output_file2)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())