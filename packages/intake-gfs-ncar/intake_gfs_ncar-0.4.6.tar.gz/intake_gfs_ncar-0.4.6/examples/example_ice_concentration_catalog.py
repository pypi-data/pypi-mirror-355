#!/usr/bin/env python3
"""
Example script to download and process GFS sea ice concentration data using the dedicated catalog dataset.

This script demonstrates how to:
1. Use the dedicated gfs_ice_concentration catalog entry for sea ice data
2. Download sea ice concentration data at surface level using the pre-configured dataset
3. Process and visualize ice concentration data
4. Save the results to a NetCDF file

This example uses the gfs_ice_concentration dataset from the catalog, which is pre-configured
with the appropriate filters for surface ice concentration, making it simpler to use than
the general gfs_forecast dataset.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import intake

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gfs_ice_concentration_catalog.log"),
    ],
)
logger = logging.getLogger(__name__)


def process_ice_concentration(ds):
    """Process sea ice concentration data.

    Args:
        ds: xarray Dataset containing ice concentration data

    Returns:
        xarray Dataset with processed ice concentration data
    """
    # Handle different variable naming conventions
    ice_var = None

    # Check for NetCDF variable names (from NetcdfSubset)
    if "Ice_cover_surface" in ds:
        ice_var = ds["Ice_cover_surface"]
        logger.info("Found NetCDF ice variable: Ice_cover_surface")
    # Check for GRIB variable names (from fileServer/cfgrib)
    elif "ci" in ds:
        ice_var = ds["ci"]
        logger.info("Found GRIB ice variable: ci")

    if ice_var is not None:
        # Ensure values are in proper range [0, 1]
        ice_var = ice_var.clip(0, 1)

        # Add the processed variable back to dataset
        ds["ice_concentration"] = ice_var

        # Add attributes
        ds["ice_concentration"].attrs = {
            "long_name": "Sea ice concentration",
            "units": "1",
            "standard_name": "sea_ice_area_fraction",
            "valid_range": [0.0, 1.0],
            "description": "Fraction of grid cell covered by sea ice (0.0 = no ice, 1.0 = completely covered)",
        }

        return ds
    else:
        available_vars = list(ds.data_vars.keys())
        raise ValueError(
            "Required ice concentration variable not found in the dataset. "
            "Expected either 'ci' or 'Ice_cover_surface'. "
            f"Available variables: {available_vars}"
        )


def get_statistics_summary(ds, var_name="ice_concentration"):
    """Get statistics summary for ice concentration data.

    Args:
        ds: xarray Dataset
        var_name: Name of the ice concentration variable

    Returns:
        dict: Statistics summary
    """
    ice_data = ds[var_name]

    stats = {
        "min": float(ice_data.min().values),
        "max": float(ice_data.max().values),
        "mean": float(ice_data.mean().values),
        "std": float(ice_data.std().values),
        "ice_covered_fraction": float((ice_data > 0.15).sum() / ice_data.size),  # Fraction with >15% ice cover
        "fully_covered_fraction": float((ice_data > 0.85).sum() / ice_data.size),  # Fraction with >85% ice cover
    }

    return stats


def get_ice_concentration_from_catalog(
    cycle, forecast_hour="f000", output_dir="gfs_output", max_lead_time=3
):
    """Download and process GFS sea ice concentration data using the dedicated catalog dataset.

    Args:
        cycle: ISO datetime string (YYYY-MM-DDTHH:MM:SS) or 'latest'
               Represents the model cycle time (e.g., '2025-01-01T00:00:00' for 00Z run)
        forecast_hour: Forecast hour (e.g., 'f000' for analysis, 'f003' for 3-hour forecast)
            Only used for output filename
        output_dir: Directory to save output files
        max_lead_time: Maximum forecast lead time in hours

    Returns:
        str: Path to the output NetCDF file
    """
    try:
        logger.info(
            f"Processing sea ice concentration data using catalog dataset for cycle {cycle}"
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

        # Use the dedicated gfs_ice_concentration dataset
        logger.info("Using dedicated gfs_ice_concentration dataset from catalog")
        source = cat["gfs_ice_concentration"](
            cycle=cycle,
            max_lead_time=max_lead_time,
        )

        logger.info("GFS ice concentration source created from catalog")
        logger.info("Pre-configured filters:")
        for key, value in source.cfgrib_filter_by_keys.items():
            logger.info(f"  {key}: {value}")

        logger.info("Reading data...")
        ds = source.read()

        if ds is None:
            raise ValueError("No data was returned from the source")

        logger.info(f"Successfully read data. Variables: {list(ds.data_vars)}")

        # Process ice concentration data
        logger.info("Processing ice concentration data...")
        ds = process_ice_concentration(ds)

        # Add global attributes
        ds.attrs.update(
            {
                "title": "GFS Sea Ice Concentration (from catalog dataset)",
                "source": "NOAA NCEP GFS via NCAR THREDDS",
                "catalog_dataset": "gfs_ice_concentration",
                "history": f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC using dedicated catalog dataset",
                "conventions": "CF-1.8",
                "processing": "Sea ice concentration extracted from GFS forecast data",
                "spatial_coverage": "Global with focus on polar regions",
                "ice_concentration_notes": "Values represent fraction of grid cell covered by sea ice (0.0-1.0)",
            }
        )

        # For filename, use the actual date we're processing
        if isinstance(cycle, str) and cycle.lower() == "latest":
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        elif isinstance(cycle, str):
            try:
                date_str = datetime.fromisoformat(cycle).strftime("%Y%m%d")
            except ValueError:
                # If not a valid ISO format, use the original cycle string
                date_str = cycle
        else:
            # Assume it's a datetime object
            date_str = cycle.strftime("%Y%m%d")

        # Save to NetCDF - if we have multiple forecast steps, include that in the filename
        if "step" in ds.coords and hasattr(ds.step, "size") and ds.step.size > 1:
            output_file = os.path.join(
                output_dir,
                f"gfs_ice_concentration_catalog_{date_str}_f000-f{int(ds.step.max().values.astype('timedelta64[h]').astype(int)):03d}.nc",
            )
        else:
            output_file = os.path.join(
                output_dir, f"gfs_ice_concentration_catalog_{date_str}_{forecast_hour}.nc"
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

        # Show statistics for ice concentration
        if "ice_concentration" in ds:
            # If we have multiple steps, show statistics for each
            if "step" in ds.dims and ds.dims["step"] > 1:
                logger.info("Ice concentration statistics by forecast step:")
                for step_idx in range(ds.dims["step"]):
                    step_val = (
                        ds.step.values[step_idx].astype("timedelta64[h]").astype(int)
                    )
                    step_ds = ds.isel(step=step_idx)
                    stats = get_statistics_summary(step_ds, "ice_concentration")
                    logger.info(
                        f"  Step f{step_val:03d}: Range {stats['min']:.3f} to {stats['max']:.3f}, "
                        f"Mean {stats['mean']:.3f}, Ice covered: {stats['ice_covered_fraction']:.1%}"
                    )
            else:
                stats = get_statistics_summary(ds, "ice_concentration")
                logger.info(
                    f"Ice concentration range: {stats['min']:.3f} to {stats['max']:.3f}"
                )
                logger.info(f"Mean ice concentration: {stats['mean']:.3f}")
                logger.info(f"Grid cells with >15% ice cover: {stats['ice_covered_fraction']:.1%}")
                logger.info(f"Grid cells with >85% ice cover: {stats['fully_covered_fraction']:.1%}")

        return output_file

    except Exception as e:
        logger.error(f"Error processing ice concentration data from catalog: {e}", exc_info=True)
        raise


def main():
    """Main function to run the example."""
    try:
        logger.info("=== GFS Sea Ice Concentration Data Example (Using Catalog Dataset) ===")

        # Use data from a few days ago to ensure it's available
        target_date = datetime.now(timezone.utc) - timedelta(days=2)
        # Round to nearest 00, 06, 12, 18Z cycle
        hour = (target_date.hour // 6) * 6
        target_cycle = target_date.replace(
            hour=hour, minute=0, second=0, microsecond=0
        ).isoformat()
        forecast_hour = "f000"  # Analysis time

        logger.info(f"Processing cycle: {target_cycle}, forecast hour: {forecast_hour}")
        logger.info("Using the dedicated gfs_ice_concentration dataset from catalog")

        # Get ice concentration data using the catalog dataset
        output_file = get_ice_concentration_from_catalog(
            cycle=target_cycle,
            forecast_hour=forecast_hour,
            output_dir="gfs_output",
            max_lead_time=3,
        )

        logger.info(f"\nSuccess! Output saved to: {os.path.abspath(output_file)}")
        logger.info("\nTo load this data in Python, use:")
        logger.info("import xarray as xr")
        logger.info("ds = xr.open_dataset('%s')", output_file)
        logger.info("# To access ice concentration data:")
        logger.info("# ice_data = ds['ice_concentration']")
        logger.info("# To access data for a specific forecast step:")
        logger.info("# step_data = ds.sel(step=ds.step[0])  # First forecast step")

        logger.info("\nUsage notes:")
        logger.info("- Ice concentration values range from 0.0 (no ice) to 1.0 (completely covered)")
        logger.info("- Values >0.15 typically indicate significant ice coverage")
        logger.info("- This data is most relevant for polar regions (Arctic and Antarctic)")
        logger.info("- Winter months typically show higher ice concentrations")

        logger.info("\nComparison with surface winds example:")
        logger.info("- This example uses the pre-configured gfs_ice_concentration catalog dataset")
        logger.info("- The original approach would use gfs_forecast with manual filter configuration")
        logger.info("- Both should produce equivalent results but this approach is simpler")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
