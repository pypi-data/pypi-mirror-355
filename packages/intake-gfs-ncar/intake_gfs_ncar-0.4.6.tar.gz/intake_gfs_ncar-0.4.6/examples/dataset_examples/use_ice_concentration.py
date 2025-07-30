#!/usr/bin/env python3
"""
Example script demonstrating how to use the gfs_ice_concentration dataset from the GFS catalog.

This script:
1. Loads the pre-configured sea ice concentration dataset from the catalog
2. Creates a visualization of sea ice concentration focused on polar regions
3. Saves the processed data to a NetCDF file
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
from cartopy.util import add_cyclic_point

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def plot_ice_concentration(
    ds, forecast_step=0, region="north", output_dir="gfs_output"
):
    """Create a plot of sea ice concentration for either the Arctic or Antarctic.

    Args:
        ds: Dataset containing ice concentration data
        forecast_step: Index of forecast step to plot
        region: Either "north" for Arctic or "south" for Antarctic
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

    # Add cyclic point to avoid discontinuity at dateline
    ci = step_ds.siconc.values
    lons = step_ds.longitude.values
    lats = step_ds.latitude.values
    ci_cyclic, lons_cyclic = add_cyclic_point(ci, coord=lons)

    # Set up the projection based on the region
    if region.lower() == "north":
        proj = ccrs.NorthPolarStereo()
        title_region = "Arctic"
        extent = [-180, 180, 50, 90]
    else:  # "south"
        proj = ccrs.SouthPolarStereo()
        title_region = "Antarctic"
        extent = [-180, 180, -90, -50]

    # Create the figure
    plt.figure(figsize=(10, 10))
    ax = plt.axes(projection=proj)

    # Set extent and add coastlines/gridlines
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(
        draw_labels=False, linewidth=0.5, color="gray", alpha=0.5, linestyle=":"
    )

    # Plot sea ice concentration
    levels = np.arange(0, 1.01, 0.05)
    cs = ax.contourf(
        lons_cyclic,
        lats,
        ci_cyclic,
        levels=levels,
        transform=ccrs.PlateCarree(),
        cmap="Blues",
        extend="both",
    )

    # Add colorbar
    cbar = plt.colorbar(cs, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("Sea Ice Concentration (fraction)")

    # Add title
    valid_time = step_ds.valid_time.values if "valid_time" in step_ds else "Unknown"
    plt.title(
        f"GFS {title_region} Sea Ice Concentration - {valid_time}\nForecast Step: {step_str}"
    )

    # Save the figure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        output_dir, f"gfs_ice_{region}_{timestamp}_{step_str}.png"
    )
    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Ice concentration plot for {title_region} saved to: {output_file}")
    return output_file


def main():
    """Main function to demonstrate using the gfs_ice_concentration dataset."""
    try:
        logger.info("=== GFS Sea Ice Concentration Dataset Example ===")

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

        # Get the sea ice concentration dataset from the catalog
        # Note: This dataset is pre-configured with the appropriate filter keys
        source = cat.gfs_ice_concentration(
            cycle=target_cycle, max_lead_time=3  # Get 3 hours of forecast data
        )

        logger.info("Reading sea ice concentration data...")
        ds = source.read()

        if ds is None:
            raise ValueError("No data was returned from the source")

        logger.info(f"Successfully read data with variables: {list(ds.data_vars)}")
        logger.info(f"Coordinates: {list(ds.coords)}")
        logger.info(f"Dimensions: {dict(ds.dims)}")

        # Create visualizations for both polar regions
        logger.info("Creating ice concentration visualizations...")
        arctic_plot = plot_ice_concentration(
            ds, forecast_step=0, region="north", output_dir=output_dir
        )
        antarctic_plot = plot_ice_concentration(
            ds, forecast_step=0, region="south", output_dir=output_dir
        )

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
            output_dir, f"gfs_ice_concentration_{date_str}_{hour_str}z.nc"
        )

        logger.info(f"Saving processed data to {output_file}")
        encoding = {var: {"zlib": True, "complevel": 4} for var in ds.data_vars}

        # Add some global attributes
        ds.attrs.update(
            {
                "title": "GFS Sea Ice Concentration",
                "source": "NOAA NCEP GFS",
                "history": f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
                "conventions": "CF-1.8",
            }
        )

        ds.to_netcdf(
            output_file,
            encoding=encoding,
            format="NETCDF4",
            engine="netcdf4",
            mode="w",
        )

        logger.info(f"\nSuccess! Dataset saved to: {os.path.abspath(output_file)}")
        logger.info(f"Visualizations saved to:")
        logger.info(f"  - Arctic: {os.path.abspath(arctic_plot)}")
        logger.info(f"  - Antarctic: {os.path.abspath(antarctic_plot)}")

        # Display ice concentration statistics
        if "step" in ds.dims and ds.dims["step"] > 1:
            logger.info("\nIce concentration statistics by forecast step:")
            for step_idx in range(min(3, ds.dims["step"])):  # Show first 3 steps
                step_val = ds.step.values[step_idx].astype("timedelta64[h]").astype(int)
                step_ds = ds.isel(step=step_idx)
                # Filter only ice-covered areas (siconc > 0.15 is typically considered ice-covered)
                ice_mask = step_ds["siconc"] > 0.15
                if ice_mask.sum().values > 0:
                    ice_only = step_ds["siconc"].where(ice_mask)
                    logger.info(
                        f"  Step f{step_val:03d}: Mean concentration in ice-covered areas: "
                        f"{float(ice_only.mean().values):.2f}, max: {float(ice_only.max().values):.2f}"
                    )
                else:
                    logger.info(
                        f"  Step f{step_val:03d}: No significant ice coverage detected"
                    )
        else:
            # Filter only ice-covered areas
            ice_mask = ds["siconc"] > 0.15
            if ice_mask.sum().values > 0:
                ice_only = ds["siconc"].where(ice_mask)
                logger.info(
                    f"\nMean ice concentration in ice-covered areas: {float(ice_only.mean().values):.2f}"
                )
                logger.info(
                    f"Maximum ice concentration: {float(ds['siconc'].max().values):.2f}"
                )
                logger.info(
                    f"Total area with ice concentration > 0.15: {float(ice_mask.sum().values)} grid cells"
                )
            else:
                logger.info("\nNo significant ice coverage detected in the dataset")

    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
