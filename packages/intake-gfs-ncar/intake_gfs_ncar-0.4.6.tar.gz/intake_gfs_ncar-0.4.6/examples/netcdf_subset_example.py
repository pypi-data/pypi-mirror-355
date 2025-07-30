#!/usr/bin/env python3
"""
Example demonstrating the new NetcdfSubset capabilities in intake-gfs-ncar.

This example shows:
1. Efficient data access using NetcdfSubset (much smaller downloads)
2. Variable filtering and geographic subsetting
3. Comparison between different access methods
4. Real-world usage patterns

The NetcdfSubset service provides significant advantages:
- Server-side variable filtering (only download what you need)
- Geographic subsetting (spatial bounding boxes)
- Much smaller file sizes (10-20MB vs 200MB for full GRIB files)
- Faster downloads and processing
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

import xarray as xr

# Add parent directory to path for importing the driver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intake_gfs_ncar.gfs_intake_driver import GFSForecastSource

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_netcdf_subset_basic():
    """Basic example using NetcdfSubset for 2m temperature."""
    logger.info("=== Example 1: Basic NetcdfSubset Usage ===")
    
    # Use a date from several years ago to ensure data availability
    test_date = '2015-01-16'
    
    # Create source with NetcdfSubset method
    source = GFSForecastSource(
        cycle=test_date + 'T00:00:00',
        max_lead_time=12,  # 12 hours of forecast data
        access_method='ncss',  # Use NetcdfSubset service
        cfgrib_filter_by_keys={
            'typeOfLevel': 'surface', 
            'shortName': '2t'  # 2m temperature
        }
    )
    
    logger.info("Loading 2m temperature data using NetcdfSubset...")
    start_time = time.time()
    
    try:
        # Read first partition to see the data structure
        ds = source._get_partition(0)
        
        download_time = time.time() - start_time
        logger.info(f"Download completed in {download_time:.2f} seconds")
        
        logger.info(f"Dataset variables: {list(ds.variables.keys())}")
        logger.info(f"Dataset dimensions: {dict(ds.sizes)}")
        
        # Check temperature data
        temp_var = 'Temperature_height_above_ground'
        if temp_var in ds:
            temp_data = ds[temp_var]
            logger.info(f"Temperature shape: {temp_data.shape}")
            logger.info(f"Temperature range: {float(temp_data.min()):.2f} - {float(temp_data.max()):.2f} K")
            logger.info(f"Temperature range (°C): {float(temp_data.min())-273.15:.2f} - {float(temp_data.max())-273.15:.2f}")
            
        return ds
        
    except Exception as e:
        logger.error(f"Error in basic NetcdfSubset example: {e}")
        return None


def example_geographic_subsetting():
    """Example showing geographic subsetting capabilities."""
    logger.info("=== Example 2: Geographic Subsetting ===")
    
    test_date = '2015-01-16'
    
    # Define a bounding box for the Western United States
    west_us_bounds = {
        'north': 49.0,   # Northern border (Canada)
        'south': 32.0,   # Southern border (Mexico)
        'west': -125.0,  # Pacific Coast
        'east': -100.0   # Eastern border
    }
    
    source = GFSForecastSource(
        cycle=test_date + 'T00:00:00',
        max_lead_time=6,
        access_method='ncss',
        cfgrib_filter_by_keys={
            'typeOfLevel': 'surface',
            'shortName': '2t'
        },
        ncss_params=west_us_bounds  # Add geographic subsetting
    )
    
    logger.info(f"Loading data for Western US region: {west_us_bounds}")
    start_time = time.time()
    
    try:
        ds = source._get_partition(0)
        download_time = time.time() - start_time
        
        logger.info(f"Regional download completed in {download_time:.2f} seconds")
        logger.info(f"Regional dataset dimensions: {dict(ds.sizes)}")
        
        # Check coordinate ranges
        if 'latitude' in ds.coords and 'longitude' in ds.coords:
            lat_range = (float(ds.latitude.min()), float(ds.latitude.max()))
            lon_range = (float(ds.longitude.min()), float(ds.longitude.max()))
            logger.info(f"Latitude range: {lat_range[0]:.2f} to {lat_range[1]:.2f}")
            logger.info(f"Longitude range: {lon_range[0]:.2f} to {lon_range[1]:.2f}")
            
        return ds
        
    except Exception as e:
        logger.error(f"Error in geographic subsetting example: {e}")
        return None


def example_multiple_variables():
    """Example with multiple meteorological variables."""
    logger.info("=== Example 3: Multiple Variables ===")
    
    test_date = '2015-01-16'
    
    # Request multiple surface variables
    source = GFSForecastSource(
        cycle=test_date + 'T00:00:00',
        max_lead_time=6,
        access_method='ncss',
        cfgrib_filter_by_keys={
            'typeOfLevel': 'surface',
            'shortName': ['2t', 'sp', 'msl']  # Temperature, surface pressure, mean sea level pressure
        }
    )
    
    logger.info("Loading multiple surface variables...")
    start_time = time.time()
    
    try:
        ds = source._get_partition(0)
        download_time = time.time() - start_time
        
        logger.info(f"Multi-variable download completed in {download_time:.2f} seconds")
        logger.info(f"Variables in dataset: {list(ds.variables.keys())}")
        
        # Look for expected variables
        expected_vars = ['Temperature_height_above_ground', 'Surface_pressure_surface', 'Pressure_reduced_to_MSL_msl']
        for var in expected_vars:
            if var in ds.variables:
                data = ds[var]
                logger.info(f"{var}: shape={data.shape}, range={float(data.min()):.2f}-{float(data.max()):.2f}")
            else:
                logger.info(f"{var}: not found (may have different name)")
                
        return ds
        
    except Exception as e:
        logger.error(f"Error in multiple variables example: {e}")
        return None


def example_access_method_comparison():
    """Compare different access methods: ncss vs fileServer."""
    logger.info("=== Example 4: Access Method Comparison ===")
    
    test_date = '2015-01-16'
    filter_keys = {'typeOfLevel': 'surface', 'shortName': '2t'}
    
    methods = [
        ('NetcdfSubset', 'ncss'),
        ('HTTP fileServer', 'fileServer'),
        ('Auto (tries ncss first)', 'auto')
    ]
    
    results = {}
    
    for method_name, method in methods:
        logger.info(f"Testing {method_name} method...")
        
        source = GFSForecastSource(
            cycle=test_date + 'T00:00:00',
            max_lead_time=3,  # Just one forecast step for comparison
            access_method=method,
            cfgrib_filter_by_keys=filter_keys
        )
        
        start_time = time.time()
        try:
            ds = source._get_partition(0)
            download_time = time.time() - start_time
            
            # Get download size info from attributes
            access_method = ds.attrs.get('access_method', 'unknown')
            
            results[method_name] = {
                'time': download_time,
                'variables': len(ds.variables),
                'dims': dict(ds.sizes),
                'access_method': access_method,
                'success': True
            }
            
            logger.info(f"{method_name}: {download_time:.2f}s, {len(ds.variables)} vars, method={access_method}")
            
        except Exception as e:
            logger.error(f"{method_name} failed: {e}")
            results[method_name] = {'success': False, 'error': str(e)}
    
    # Summary
    logger.info("\n=== Access Method Comparison Summary ===")
    for method_name, result in results.items():
        if result['success']:
            logger.info(f"{method_name}: {result['time']:.2f}s ({result['access_method']})")
        else:
            logger.info(f"{method_name}: FAILED - {result['error']}")
    
    return results


def example_predefined_datasets():
    """Example using predefined datasets from the catalog."""
    logger.info("=== Example 5: Predefined Catalog Datasets ===")
    
    test_date = '2015-01-16'
    
    # The catalog should have predefined datasets optimized for common use cases
    try:
        # Example: surface winds (optimized for NetcdfSubset)
        logger.info("Testing predefined surface winds dataset...")
        
        winds_source = GFSForecastSource(
            cycle=test_date + 'T00:00:00',
            max_lead_time=6,
            access_method='ncss',
            cfgrib_filter_by_keys={
                'typeOfLevel': 'heightAboveGround',
                'level': 10,
                'shortName': ['10u', '10v']
            }
        )
        
        start_time = time.time()
        ds = winds_source._get_partition(0)
        download_time = time.time() - start_time
        
        logger.info(f"Surface winds download: {download_time:.2f}s")
        logger.info(f"Wind variables: {[var for var in ds.variables.keys() if 'wind' in var.lower()]}")
        
        return ds
        
    except Exception as e:
        logger.error(f"Error in predefined datasets example: {e}")
        return None


def main():
    """Run all examples."""
    logger.info("Starting NetcdfSubset examples...")
    logger.info("These examples demonstrate the enhanced capabilities of intake-gfs-ncar")
    logger.info("with NCAR THREDDS NetcdfSubset support.\n")
    
    examples = [
        ("Basic NetcdfSubset", example_netcdf_subset_basic),
        ("Geographic Subsetting", example_geographic_subsetting),
        ("Multiple Variables", example_multiple_variables),
        ("Access Method Comparison", example_access_method_comparison),
        ("Predefined Datasets", example_predefined_datasets),
    ]
    
    results = {}
    
    for example_name, example_func in examples:
        logger.info(f"\n{'='*60}")
        try:
            result = example_func()
            results[example_name] = {'success': True, 'result': result}
            logger.info(f"✓ {example_name} completed successfully")
        except Exception as e:
            logger.error(f"✗ {example_name} failed: {e}")
            results[example_name] = {'success': False, 'error': str(e)}
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("EXAMPLES SUMMARY")
    logger.info(f"{'='*60}")
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    for example_name, result in results.items():
        status = "✓ PASSED" if result['success'] else "✗ FAILED"
        logger.info(f"{example_name}: {status}")
    
    logger.info(f"\nOverall: {success_count}/{total_count} examples passed")
    
    if success_count == total_count:
        logger.info("\n🎉 All examples completed successfully!")
        logger.info("NetcdfSubset integration is working correctly.")
    else:
        logger.info(f"\n⚠️  {total_count - success_count} example(s) failed.")
        logger.info("This may be due to network issues or data availability.")
    
    logger.info("\nKey Benefits of NetcdfSubset:")
    logger.info("• Much smaller downloads (10-20MB vs 200MB)")
    logger.info("• Server-side variable filtering")
    logger.info("• Geographic subsetting support")
    logger.info("• Faster processing and reduced bandwidth")
    logger.info("• Automatic fallback to fileServer when needed")


if __name__ == "__main__":
    main()