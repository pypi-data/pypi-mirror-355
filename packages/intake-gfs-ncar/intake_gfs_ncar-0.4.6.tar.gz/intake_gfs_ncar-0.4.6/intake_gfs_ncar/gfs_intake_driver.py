"""Intake driver for GFS forecast data from NCAR THREDDS.

This module provides an Intake driver for accessing Global Forecast System (GFS)
forecast data from the NCAR THREDDS server.
"""

import logging
import traceback
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import xarray as xr
from intake.source.base import DataSource, Schema

logger = logging.getLogger(__name__)

# Default GFS data URL (NCAR THREDDS)
DEFAULT_BASE_URL = "https://thredds.rda.ucar.edu/thredds"

# Default file pattern for GFS forecast files
DEFAULT_FILE_PATTERN = (
    "{base_url}/{date:%Y}/{date:%Y%m%d}/"
    "gfs.0p25.{date:%Y%m%d}{model_run_time:02d}.f{lead_time:03d}.grib2"
)


class GFSForecastSource(DataSource):
    """Intake driver for GFS forecast data from NCAR THREDDS.

    This driver provides access to GFS forecast data in GRIB2 format from the
    NCAR THREDDS server. It supports filtering by variable, level, and forecast
    lead time, and returns data as xarray Datasets.

    Parameters
    ----------
    cycle : str or datetime-like, optional
        Forecast initialization cycle. Can be 'latest' for most recent,
        ISO format datetime string, or datetime object. Default: 'latest'
    max_lead_time : int, optional
        Maximum forecast lead time in hours. Default: 24
    base_url : str, optional
        Base URL for the NCAR THREDDS server
    cfgrib_filter_by_keys : dict, optional
        Dictionary of GRIB filter parameters (e.g., {'typeOfLevel': 'surface'})
    access_method : str, optional
        Data access method: 'ncss' (NetcdfSubset), 'fileServer' (HTTP download),
        or 'auto' (try ncss first, fallback to fileServer). Default: 'auto'
    ncss_params : dict, optional
        Additional NetcdfSubset parameters (e.g., {'north': 60, 'south': 30})
    metadata : dict, optional
        Additional metadata to include in the source
    """

    name = "gfs_forecast"
    version = "0.1.0"
    container = "xarray"
    partition_access = True

    parameters = {
        "cycle": {
            "description": "Model cycle (forecast initialization time)",
            "type": "str",
            "default": "latest"
        },
        "max_lead_time": {
            "description": "Maximum lead time to retrieve (hours)",
            "type": "int",
            "default": 24
        }
    }

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cfgrib_filter_by_keys: Optional[Dict[str, Any]] = None,
        access_method: str = "auto",
        ncss_params: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cycle: str = "latest",
        max_lead_time: int = 24,
        **kwargs,
    ):
        super().__init__(metadata=metadata or {})


        # Handle "today" default for cycle parameter
        if cycle == "today":
            cycle = "latest"

        # Parse and validate cycle (date and model run time)
        try:
            if isinstance(cycle, str):
                if cycle.lower() == "latest":
                    # Use current time if 'latest' is specified
                    cycle_dt = datetime.now(timezone.utc)
                    # Round down to the nearest 6-hour cycle (00, 06, 12, 18Z)
                    hour = (cycle_dt.hour // 6) * 6
                    cycle_dt = cycle_dt.replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    )
                    self.date = cycle_dt.date()
                    self.model_run_time = cycle_dt.hour
                    logger.info(
                        f"Using latest cycle: {cycle_dt.isoformat()} ({self.model_run_time:02d}Z)"
                    )
                else:
                    try:
                        cycle_dt = datetime.fromisoformat(cycle)
                    except ValueError:
                        # Fall back to pandas for more flexible parsing
                        cycle_dt = pd.to_datetime(cycle)
                    self.date = cycle_dt.date()
                    self.model_run_time = cycle_dt.hour
                    logger.info(
                        f"Using specified cycle: {cycle_dt.isoformat()} ({self.model_run_time:02d}Z)"
                    )
            elif isinstance(cycle, datetime):
                # Handle datetime objects directly
                cycle_dt = cycle
                self.date = cycle_dt.date()
                self.model_run_time = cycle_dt.hour
                logger.info(
                    f"Using datetime cycle: {cycle_dt.isoformat()} ({self.model_run_time:02d}Z)"
                )
            else:
                # Handle pandas Timestamp and other datetime-like objects
                cycle_dt = pd.to_datetime(cycle)
                self.date = cycle_dt.date()
                self.model_run_time = cycle_dt.hour
                logger.info(
                    f"Using parsed cycle: {cycle_dt.isoformat()} ({self.model_run_time:02d}Z)"
                )

            # Validate model run time is valid
            if not (0 <= self.model_run_time <= 23):
                raise ValueError("Cycle hour must be between 0 and 23")

        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid cycle format: {cycle}. Expected ISO format "
                f"(YYYY-MM-DDTHH:MM:SS), 'latest', or datetime object"
            ) from e

        # Validate max_lead_time
        try:
            self.max_lead_time = int(max_lead_time)
            if self.max_lead_time <= 0:
                raise ValueError("max_lead_time must be a positive integer")
            if (
                self.max_lead_time > 384
            ):  # Maximum GFS forecast length is typically 384 hours
                logger.warning(
                    f"max_lead_time={max_lead_time} is greater than typical GFS maximum of 384 hours"
                )
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid max_lead_time: {max_lead_time}. Expected positive " f"integer"
            ) from e

        self.base_url = base_url.rstrip("/")
        self.cfgrib_filter_by_keys = cfgrib_filter_by_keys or {}
        self.access_method = access_method
        self.ncss_params = ncss_params or {}
        self._ds = None
        self._urls = None

        # Create the cycle datetime for metadata
        cycle_datetime = datetime.combine(self.date, time(hour=self.model_run_time))

        # Update metadata
        self.metadata.update(
            {
                "cycle": cycle_datetime.isoformat(),
                "date": self.date.isoformat(),
                "max_lead_time": self.max_lead_time,
                "model_run_time": f"{self.model_run_time:02d}Z",
                "base_url": self.base_url,
                "cfgrib_filter_by_keys": self.cfgrib_filter_by_keys,
                "access_method": self.access_method,
                "ncss_params": self.ncss_params,
                **kwargs,
            }
        )

        logger.info(
            f"Initialized GFS source for cycle: {cycle_datetime.isoformat()} "
            f"with max_lead_time: {self.max_lead_time}"
        )

    def _build_urls(self) -> List[str]:
        """Build URLs for all forecast lead times up to max_lead_time."""
        if self._urls is not None:
            return self._urls

        urls = []
        date_str = self.date.strftime("%Y%m%d")
        model_run_time_str = f"{self.model_run_time:02d}"

        logger.info(
            f"Building URLs for max_lead_time={self.max_lead_time} (f{self.max_lead_time:03d})"
        )

        # GFS files are available in 3-hour increments up to 120 hours,
        # then 6-hour increments up to 240 hours, and 12-hour increments beyond that
        for lead_time in range(0, min(self.max_lead_time, 120) + 1, 3):
            url = self._build_file_url(date_str, model_run_time_str, lead_time)
            urls.append(url)
            logger.debug(f"Added URL for lead_time={lead_time}: {url}")

        if self.max_lead_time > 120:
            for lead_time in range(123, min(self.max_lead_time, 240) + 1, 3):
                url = self._build_file_url(date_str, model_run_time_str, lead_time)
                urls.append(url)
                logger.debug(f"Added URL for lead_time={lead_time}: {url}")

        if self.max_lead_time > 240:
            for lead_time in range(246, self.max_lead_time + 1, 6):
                url = self._build_file_url(date_str, model_run_time_str, lead_time)
                urls.append(url)
                logger.debug(f"Added URL for lead_time={lead_time}: {url}")

        self._urls = urls
        logger.info(
            f"Generated {len(urls)} URLs for GFS data from {date_str} {model_run_time_str}Z"
        )
        if urls:
            logger.info(f"First URL: {urls[0]}")
            if len(urls) > 1:
                logger.info(f"Last URL: {urls[-1]}")
                logger.info(f"All URLs: {urls}")
        else:
            logger.warning("No URLs generated - check date and model run time")

        return urls

    def _build_file_url(self, date_str: str, model_run_time_str: str, lead_time: int) -> str:
        """Build URL for a specific forecast file based on access method."""
        file_path = f"files/g/d084001/{date_str[:4]}/{date_str}/gfs.0p25.{date_str}{model_run_time_str}.f{lead_time:03d}.grib2"

        if self.access_method == "ncss" or self.access_method == "auto":
            # Use NetcdfSubset service
            url = f"{self.base_url}/ncss/grid/{file_path}"
            if self.cfgrib_filter_by_keys or self.ncss_params:
                url += self._build_ncss_query()
        else:
            # Use HTTP fileServer
            url = f"{self.base_url}/fileServer/{file_path}"

        return url

    def _build_ncss_query(self) -> str:
        """Build NetcdfSubset query parameters from cfgrib filters and ncss params."""
        params = {}

        # Add NetcdfSubset-specific parameters
        params.update(self.ncss_params)

        # Convert cfgrib filters to NetcdfSubset parameters where possible
        if self.cfgrib_filter_by_keys:
            # Map common cfgrib keys to NetcdfSubset variable names
            var_mapping = {
                '2t': 'Temperature_height_above_ground',
                't2m': 'Temperature_height_above_ground',
                '10u': 'u-component_of_wind_height_above_ground',
                '10v': 'v-component_of_wind_height_above_ground',
                'msl': 'Pressure_reduced_to_MSL_msl',
                'sp': 'Surface_pressure_surface',
                'ci': 'Ice_cover_surface',
            }

            # Try to map variables
            if 'shortName' in self.cfgrib_filter_by_keys:
                short_names = self.cfgrib_filter_by_keys['shortName']
                if isinstance(short_names, str):
                    short_names = [short_names]

                vars_to_add = []
                for short_name in short_names:
                    if short_name in var_mapping:
                        vars_to_add.append(var_mapping[short_name])

                if vars_to_add:
                    params['var'] = ','.join(vars_to_add)

            # Handle level selections
            if 'level' in self.cfgrib_filter_by_keys:
                level = self.cfgrib_filter_by_keys['level']
                if 'typeOfLevel' in self.cfgrib_filter_by_keys:
                    level_type = self.cfgrib_filter_by_keys['typeOfLevel']
                    if level_type == 'heightAboveGround':
                        params['vertCoord'] = f"{level}"

        # Set default format to netcdf if not specified
        if 'format' not in params:
            params['format'] = 'netcdf'

        # Build query string
        if params:
            query_parts = []
            for key, value in params.items():
                query_parts.append(f"{key}={value}")
            return "?" + "&".join(query_parts)
        else:
            return "?format=netcdf"

    def _get_schema(self) -> Schema:
        """Get schema for the data source."""
        if self._schema is not None:
            return self._schema

        self._build_urls()

        if not self._urls:
            raise ValueError("No valid URLs found for the specified parameters")

        # Try to open the first file to get the schema
        try:
            url = self._urls[0]
            logger.info(f"Getting schema from: {url}")

            # Check if this is a NetcdfSubset URL
            is_ncss = "/ncss/" in url

            if is_ncss:
                # Try NetcdfSubset approach first
                try:
                    logger.info("Attempting schema discovery with NetcdfSubset")
                    ds = xr.open_dataset(url, engine="netcdf4")

                    logger.info("NetcdfSubset schema discovery successful")
                    logger.info(f"Variables: {list(ds.variables.keys())}")
                    logger.info(f"Dimensions: {dict(ds.sizes)}")
                    logger.info(f"Coordinates: {list(ds.coords.keys())}")

                    # Convert to schema
                    shape = {k: v for k, v in ds.sizes.items()}
                    dtype = {k: str(v.dtype) for k, v in ds.variables.items()}

                    self._schema = Schema(
                        datashape=None,
                        shape=tuple(shape.values()) if shape else None,
                        dtype=dtype,
                        npartitions=len(self._urls),
                        extra_metadata={
                            "variables": list(ds.data_vars.keys()),
                            "coords": list(ds.coords.keys()),
                            "dims": dict(ds.sizes),
                            "access_method": "ncss",
                        },
                    )

                    # Store the dataset if it's small enough
                    if sum(shape.values()) < 1e6:  # Arbitrary threshold
                        self._ds = ds

                    return self._schema

                except Exception as e:
                    logger.warning(f"NetcdfSubset schema discovery failed: {e}")
                    if self.access_method != "auto":
                        raise

                    # Fall back to fileServer approach
                    logger.info("Falling back to fileServer for schema discovery")
                    url = url.replace("/ncss/grid/", "/fileServer/").split("?")[0]

            # GRIB2 fileServer approach
            import os
            import shutil
            import tempfile
            import urllib.request

            logger.info(f"Downloading file for schema: {url}")

            # Create a temporary directory for the download
            temp_dir = tempfile.mkdtemp(prefix="gfs_intake_")
            try:
                # Download the file with a .grib2 extension
                temp_file = os.path.join(temp_dir, "temp.grib2")
                logger.info(f"Downloading to temporary file: {temp_file}")

                # Download with a timeout
                try:
                    with (
                        urllib.request.urlopen(url, timeout=30) as response,
                        open(temp_file, "wb") as out_file,
                    ):
                        shutil.copyfileobj(response, out_file)
                except Exception as e:
                    raise IOError(f"Failed to download {url}: {e}")

                # Check if the file was downloaded successfully
                if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                    raise IOError(
                        f"Downloaded file is empty or does not exist: {temp_file}"
                    )

                logger.info(
                    f"Successfully downloaded file, size: {os.path.getsize(temp_file)} bytes"
                )

                # Open the dataset with cfgrib
                backend_kwargs = {
                    "indexpath": "",
                    "errors": "raise",  # Raise exceptions to see actual errors
                    "filter_by_keys": self.cfgrib_filter_by_keys or {},
                }

                logger.info(f"Opening with cfgrib, filter_by_keys: {backend_kwargs}")

                try:
                    ds = xr.open_dataset(
                        temp_file, engine="cfgrib", backend_kwargs=backend_kwargs
                    )

                    logger.info("GRIB schema discovery successful")
                    logger.info(f"Variables: {list(ds.variables.keys())}")
                    logger.info(f"Dimensions: {dict(ds.sizes)}")
                    logger.info(f"Coordinates: {list(ds.coords.keys())}")

                    # Convert to schema
                    shape = {k: v for k, v in ds.sizes.items()}
                    dtype = {k: str(v.dtype) for k, v in ds.variables.items()}

                    self._schema = Schema(
                        datashape=None,
                        shape=tuple(shape.values()) if shape else None,
                        dtype=dtype,
                        npartitions=len(self._urls),
                        extra_metadata={
                            "variables": list(ds.data_vars.keys()),
                            "coords": list(ds.coords.keys()),
                            "dims": dict(ds.sizes),
                            "access_method": "fileServer",
                        },
                    )

                    # Store the dataset if it's small enough
                    if sum(shape.values()) < 1e6:  # Arbitrary threshold
                        self._ds = ds

                    return self._schema

                except Exception as e:
                    logger.error(f"Error opening GRIB file with cfgrib: {e}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    raise

            finally:
                # Clean up the temporary directory
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        logger.debug(f"Removed temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(
                        f"Could not remove temporary directory {temp_dir}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")

            # Return an empty schema if we can't determine it
            self._schema = Schema(
                datashape=None,
                shape=None,
                npartitions=(
                    len(self._urls) if hasattr(self, "_urls") and self._urls else 0
                ),
                extra_metadata={
                    "error": str(e),
                    "urls": (
                        self._urls[:5] if hasattr(self, "_urls") and self._urls else []
                    ),
                },
            )

        return self._schema

    def _get_partition(self, i: int) -> xr.Dataset:
        """Get one partition from the dataset.

        Parameters
        ----------
        i : int
            The partition number to read.

        Returns
        -------
        xarray.Dataset
            The dataset for the specified partition.
        """
        if self._urls is None:
            self._build_urls()

        if self._urls is None or i >= len(self._urls):
            raise IndexError(f"Partition {i} is out of range")

        url = self._urls[i]
        logger.info(f"Reading data from {url}")

        # Check if this is a NetcdfSubset URL (contains ncss)
        is_ncss = "/ncss/" in url

        try:
            if is_ncss:
                return self._read_ncss_data(url, i)
            else:
                return self._read_grib_data(url, i)
        except Exception as e:
            # Enhance error message with partition context
            error_msg = f"Failed to read partition {i} from {url}: {e}"
            logger.error(error_msg)

            # Provide helpful suggestions based on error type
            if "404" in str(e) or "Not Found" in str(e):
                logger.info(f"Partition {i} data may not be available. This could be due to:")
                logger.info("  - Recent forecast times that haven't been published yet")
                logger.info("  - Archived data that's no longer available")
                logger.info("  - Incorrect date/time specification")
                logger.info(f"  - URL: {url}")

            raise type(e)(error_msg) from e

    def _read_ncss_data(self, url: str, partition_idx: int) -> xr.Dataset:
        """Read data from NetcdfSubset service."""
        try:
            # Create a temporary file to download the NetCDF file
            import os
            import tempfile
            import urllib.request
            import urllib.error

            logger.info(f"Downloading NetCDF data from NetcdfSubset: {url}")

            with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Download the file with better error handling
            logger.info(f"Downloading NetCDF file to temporary location: {tmp_path}")
            try:
                urllib.request.urlretrieve(url, tmp_path)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise IOError(f"Data not found (HTTP 404): {url}. This forecast time may not be available yet or may have been archived.")
                elif e.code == 400:
                    raise IOError(f"Bad request (HTTP 400): {url}. Check variable names and query parameters.")
                else:
                    raise IOError(f"HTTP Error {e.code}: {e.reason} for URL: {url}")
            except urllib.error.URLError as e:
                raise IOError(f"Network error accessing {url}: {e.reason}")

            # Check if file was downloaded successfully
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                raise IOError(f"Failed to download NetCDF file from {url}")

            logger.info("Successfully downloaded NetCDF file, size: %d bytes", os.path.getsize(tmp_path))

            # Open with xarray netcdf4 engine
            ds = xr.open_dataset(tmp_path, engine="netcdf4")

            logger.info(f"Successfully opened NetCDF dataset with variables: {list(ds.variables.keys())}")
            logger.info(f"Dataset dimensions: {dict(ds.sizes)}")

            # Add metadata
            ds.attrs["source_url"] = url
            ds.attrs["access_method"] = "ncss"
            ds.attrs["partition_index"] = partition_idx

            # Load data into memory
            logger.info("Loading NetCDF data into memory")
            ds = ds.load()

            # Clean up temporary file
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    logger.debug(f"Removed temporary file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file {tmp_path}: {e}")

            return ds

        except Exception as e:
            logger.warning(f"NetcdfSubset failed for partition {partition_idx}: {e}")
            if self.access_method == "auto":
                logger.info("Falling back to fileServer method")
                # Convert to fileServer URL and try GRIB approach
                fallback_url = url.replace("/ncss/grid/", "/fileServer/").split("?")[0]
                return self._read_grib_data(fallback_url, partition_idx)
            else:
                raise

    def _read_grib_data(self, url: str, partition_idx: int) -> xr.Dataset:
        """Read data from GRIB2 file using HTTP fileServer."""
        try:
            # Create a temporary file to download the GRIB file
            import os
            import tempfile
            import urllib.request

            with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Download the file
            logger.info(f"Downloading GRIB file to temporary location: {tmp_path}")
            urllib.request.urlretrieve(url, tmp_path)

            # Check if file was downloaded successfully
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                raise IOError(f"Failed to download file from {url}")

            # Open with cfgrib engine and specified filters
            logger.info(f"Opening GRIB file with cfgrib: {tmp_path}")
            backend_kwargs = {
                "indexpath": "",
                "errors": "raise",  # Change to 'raise' to see actual errors
                "filter_by_keys": self.cfgrib_filter_by_keys,
            }

            logger.info(f"Using backend kwargs: {backend_kwargs}")
            logger.info("Filter by keys details:")
            for key, value in self.cfgrib_filter_by_keys.items():
                logger.info(f"  {key}: {value}")

            # Try to open the dataset
            try:
                ds = xr.open_dataset(
                    tmp_path, engine="cfgrib", backend_kwargs=backend_kwargs
                )

                # Check if we got any data
                if not ds.variables:
                    logger.warning(f"No variables found in the dataset from {url}")
                else:
                    logger.info(
                        f"Successfully read dataset with variables: {list(ds.variables.keys())}"
                    )

                # Log detailed information about dimensions and coordinates
                logger.info(f"Dataset dimensions: {dict(ds.sizes)}")
                if "time" in ds.coords:
                    logger.info(f"Time values: {ds.time.values}")
                if "step" in ds.coords:
                    logger.info(f"Step values: {ds.step.values}")

                # Add URL as an attribute for reference
                ds.attrs["source_url"] = url
                ds.attrs["access_method"] = "fileServer"
                ds.attrs["partition_index"] = partition_idx
                # Extract lead time from URL or filename
                if ".f" in url and ".grib2" in url:
                    lead_time_part = url.split(".f")[-1].split(".grib2")[0]
                    ds.attrs["lead_time"] = f"f{lead_time_part}"

                # Actually load all data into memory to avoid file access issues
                logger.info(f"Loading data into memory from {tmp_path}")
                ds = ds.load()

                # Now we can safely delete the temporary file since data is loaded
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.debug(f"Removed temporary file: {tmp_path}")
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {tmp_path}: {e}")

                return ds

            except Exception as e:
                logger.error(f"Error opening dataset with cfgrib: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Clean up in case of error
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

        except Exception as e:
            logger.error(f"Error reading data from {url}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    def _standardize_variable_names(self, ds: xr.Dataset) -> xr.Dataset:
        """Standardize variable names and coordinates to match GRIB conventions.

        This method renames NetCDF variables from NetcdfSubset to match
        the expected GRIB variable names for consistency across access methods.
        It also standardizes time coordinate names to fix alignment issues.

        Parameters
        ----------
        ds : xr.Dataset
            Dataset with potentially non-standard variable names

        Returns
        -------
        xr.Dataset
            Dataset with standardized variable names and coordinates
        """
        # Mapping from NetCDF names (NetcdfSubset) to GRIB-style names
        name_mapping = {
            'Temperature_height_above_ground': 't2m',  # 2m temperature
            'u-component_of_wind_height_above_ground': 'u10',  # 10m u-wind
            'v-component_of_wind_height_above_ground': 'v10',  # 10m v-wind
            'Pressure_reduced_to_MSL_msl': 'msl',  # Mean sea level pressure
            'Surface_pressure_surface': 'sp',  # Surface pressure
            'Relative_humidity_height_above_ground': 'r2',  # 2m relative humidity
            'Specific_humidity_height_above_ground': 'q2',  # 2m specific humidity
            'Dewpoint_temperature_height_above_ground': 'd2m',  # 2m dewpoint
            'Total_precipitation_surface': 'tp',  # Total precipitation
            'Convective_precipitation_surface': 'cp',  # Convective precipitation
            'Snowfall_rate_water_equivalent_surface': 'sf',  # Snowfall
            'Geopotential_height_isobaric': 'gh',  # Geopotential height
            'Temperature_isobaric': 't',  # Temperature on pressure levels
            'u-component_of_wind_isobaric': 'u',  # U-wind on pressure levels
            'v-component_of_wind_isobaric': 'v',  # V-wind on pressure levels
            'Relative_humidity_isobaric': 'r',  # Relative humidity on pressure levels
            'Ice_cover_surface': 'ci',  # Sea ice concentration
        }

        # Create a copy to avoid modifying the original
        ds_renamed = ds.copy()

        # Track which variables were renamed
        renamed_vars = {}

        # Rename data variables
        for netcdf_name, grib_name in name_mapping.items():
            if netcdf_name in ds_renamed.data_vars:
                logger.debug(f"Renaming variable: {netcdf_name} → {grib_name}")
                ds_renamed = ds_renamed.rename({netcdf_name: grib_name})
                renamed_vars[netcdf_name] = grib_name

        # Standardize time coordinate names for consistency across partitions
        # NetcdfSubset sometimes returns 'time', 'time1', 'time2', etc.
        time_coords_to_rename = {}
        for coord_name in ds_renamed.coords:
            if isinstance(coord_name, str) and coord_name.startswith('time') and coord_name != 'time':
                time_coords_to_rename[coord_name] = 'time'
                logger.debug(f"Renaming time coordinate: {coord_name} → time")

        if time_coords_to_rename:
            ds_renamed = ds_renamed.rename(time_coords_to_rename)
            logger.info(f"Standardized time coordinates: {time_coords_to_rename}")

        # Log standardization results
        if renamed_vars:
            logger.info(f"Standardized {len(renamed_vars)} variable names: {renamed_vars}")
            # Add metadata about the renaming (convert dict to string for NetCDF compatibility)
            ds_renamed.attrs['variable_name_standardization'] = str(renamed_vars)

        return ds_renamed

    def read(self) -> xr.Dataset:
        """Load entire dataset into memory and return as xarray.Dataset"""
        if self._ds is not None:
            return self._ds

        if self._urls is None:
            self._build_urls()

        if not self._urls:
            logger.warning("No URLs available to read data from")
            return xr.Dataset()

        try:
            logger.info(f"Reading {len(self._urls)} partitions...")
            # Read all partitions and combine
            datasets = []
            for i, url in enumerate(self._urls):
                try:
                    logger.info(f"Reading partition {i+1}/{len(self._urls)} from {url}")
                    ds = self._get_partition(i)
                    if ds is not None and len(ds.variables) > 0:
                        logger.info(
                            f"Successfully read partition {i+1} with variables: {list(ds.variables.keys())}"
                        )
                        # Standardize variable names for consistency
                        ds = self._standardize_variable_names(ds)
                        datasets.append(ds)
                    else:
                        logger.warning(f"No data in partition {i+1}")
                except Exception as e:
                    logger.error(f"Error reading partition {i+1}: {e}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    # Continue with other partitions even if one fails
                    continue

            if not datasets:
                logger.warning("No data was read from any partition")
                return xr.Dataset()

            logger.info(f"Combining {len(datasets)} partitions...")
            # Combine datasets along the time dimension if it exists
            try:
                if len(datasets) > 1:
                    if "time" in datasets[0].dims:
                        logger.info("Concatenating datasets along time dimension")
                        self._ds = xr.concat(datasets, dim="time")
                    elif "step" in datasets[0].coords:
                        # If no time dimension but step coordinate exists, try to create a new dimension
                        logger.info("Trying to combine datasets along step coordinate")
                        try:
                            # Log each dataset's step value for debugging
                            for i, ds in enumerate(datasets):
                                logger.info(f"Dataset {i} step value: {ds.step.values}")

                            # Create a new dataset that includes step as a dimension
                            # First, ensure the step coordinate values are all different
                            step_values = [ds.step.values.item() for ds in datasets]
                            if len(set(step_values)) != len(step_values):
                                logger.warning(
                                    "Duplicate step values found, cannot combine"
                                )
                                self._ds = datasets[0]
                            else:
                                # Convert step from coordinate to dimension
                                new_datasets = []
                                for ds in datasets:
                                    # Expand step from scalar coordinate to 1-element dimension
                                    ds = ds.expand_dims("step")
                                    new_datasets.append(ds)

                                # Now concat these datasets along the step dimension
                                combined = xr.concat(new_datasets, dim="step")
                                logger.info(
                                    f"Successfully combined datasets along step dimension: {combined.step.values}"
                                )
                                self._ds = combined
                        except Exception as e:
                            logger.error(f"Error combining along step: {e}")
                            logger.debug(f"Traceback: {traceback.format_exc()}")
                            logger.info(
                                "Using only the first dataset due to combination error"
                            )
                            self._ds = datasets[0]
                    else:
                        logger.info(
                            "Using single dataset (no time or step concatenation possible)"
                        )
                        self._ds = datasets[0]
                else:
                    logger.info("Using single dataset (only one available)")
                    self._ds = datasets[0]

                # Log some basic info about the combined dataset
                if hasattr(self._ds, "variables") and self._ds.variables:
                    logger.info(
                        f"Combined dataset has {len(self._ds.variables)} " f"variables"
                    )
                    logger.info(f"Dataset dimensions: {dict(self._ds.sizes)}")

                    # Log time range if time dimension exists
                    if (
                        "time" in self._ds.sizes
                        and hasattr(self._ds, "time")
                        and len(self._ds.time) > 0
                    ):
                        logger.info(
                            f"Time range: {self._ds.time.values.min()} to {self._ds.time.values.max()}"
                        )

                return self._ds

            except Exception as e:
                logger.error(f"Error combining datasets: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Return the first dataset if concatenation fails
                if datasets:
                    logger.info("Returning first dataset due to concatenation error")
                    return datasets[0]
                return xr.Dataset()

        except Exception as e:
            logger.error(f"Error reading dataset: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    def to_dask(self):
        """Return the dataset with dask arrays."""
        ds = self.read()

        # If the dataset already uses dask arrays, return it as-is
        if any(hasattr(var.data, 'chunks') for var in ds.data_vars.values()):
            return ds

        # Otherwise, chunk the dataset to use dask arrays
        try:
            return ds.chunk()
        except Exception:
            # If chunking fails, return the dataset as-is
            return ds

    def close(self):
        """Close any open files or resources."""
        if self._ds is not None:
            if hasattr(self._ds, "close"):
                self._ds.close()
            self._ds = None
        self._urls = None
        self._schema = None


# Driver registration is now handled in __init__.py to avoid duplicate registrations
