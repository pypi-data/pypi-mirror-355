# Intake GFS NCAR

An [Intake](https://intake.readthedocs.io/) driver for accessing Global Forecast System (GFS) data from the NCAR THREDDS server.

## Features

- Access GFS forecast data through a simple Python interface
- Supports filtering by variable, level, and forecast lead time
- Built on xarray and cfgrib for efficient handling of GRIB2 data
- Supports both single files and time series of forecast files
- Compatible with Dask for out-of-core computations
- Uses NetCDF Subset Service (NCSS) for efficient data access
- Includes pre-configured datasets for common variables (winds, ice concentration)

## Installation

```bash
pip install intake-gfs-ncar
```

## Usage

### Basic Usage

```python
import intake

# Open the catalog
cat = intake.open_catalog("gfs_catalog.yaml")

# Get a data source for surface variables
source = cat.gfs_forecast(
    cycle="2023-01-01T00:00:00",  # Forecast cycle in ISO format
    max_lead_time=24,  # Maximum forecast lead time in hours
    cfgrib_filter_by_keys={
        'typeOfLevel': 'surface',  # Get surface variables
        'step': 3  # 3-hour forecast step
    }
)

# Load the data as an xarray Dataset
ds = source.read()
print(ds)
```

### Available Parameters

- `cycle`: Forecast cycle in ISO format (e.g., '2023-01-01T00:00:00') or 'latest'
- `max_lead_time`: Maximum forecast lead time in hours (e.g., 24)
- `cfgrib_filter_by_keys`: Dictionary of GRIB filter parameters (see below)
- `base_url`: Base URL for the NCAR THREDDS server (defaults to NCAR's THREDDS server)

### GRIB Filter Keys

You can filter the GRIB data using any of the following keys in the `cfgrib_filter_by_keys` parameter:

- `typeOfLevel`: Type of level (e.g., 'surface', 'isobaricInhPa')
- `level`: Pressure level in hPa (for isobaric levels)
- `shortName`: Variable short name (e.g., 't' for temperature, 'u' for u-wind)
- `step`: Forecast step in hours

## Examples

Check the `examples/` directory for complete working examples, including:
- `example_surface_winds_catalog.py` - Surface wind analysis with automatic wind speed/direction calculation
- `example_ice_concentration_catalog.py` - Sea ice concentration analysis with polar region statistics

### Get 500 hPa geopotential height

```python
source = cat.gfs_forecast(
    cycle="2023-01-01T00:00:00",
    max_lead_time=24,
    cfgrib_filter_by_keys={
        'typeOfLevel': 'isobaricInhPa',
        'level': 500,
        'shortName': 'gh'
    }
)
```

### Get surface temperature

```python
source = cat.gfs_forecast(
    cycle="2023-01-01T00:00:00",
    max_lead_time=24,
    cfgrib_filter_by_keys={
        'typeOfLevel': 'surface',
        'shortName': '2t'  # 2m temperature
    }
)
```

### Predefined Datasets

The catalog also includes predefined datasets with common filter configurations that use NetCDF Subset Service for efficient access:

#### Surface Winds

```python
# Get 10m wind components (u10, v10) with pre-configured filters
source = cat.gfs_surface_winds(
    cycle="2023-01-01T00:00:00",
    max_lead_time=24
)
ds = source.read()
# Variables: u10, v10 (automatically standardized from NetCDF names)
```

#### Sea Ice Concentration

```python
# Get sea ice concentration data optimized for polar regions
source = cat.gfs_ice_concentration(
    cycle="2023-01-01T00:00:00",
    max_lead_time=24
)
ds = source.read()
# Variable: ci (sea ice concentration, 0.0-1.0)
```

These predefined datasets automatically handle:
- Variable name standardization between NetCDF and GRIB formats
- Optimal access method selection (NetCDF Subset Service)
- Pre-configured filters for common use cases

## Development

### Installation from source

```bash
git clone https://github.com/oceanum/intake-gfs-ncar.git
cd intake-gfs-ncar
pip install -e '.[dev]'
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=intake_gfs_ncar --cov-report=term-missing

# Run specific test file
pytest tests/test_gfs_intake_driver.py
```

### Code quality

The project uses several tools to maintain code quality:

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy intake_gfs_ncar --ignore-missing-imports

# Check package build
python -m build
python -m twine check dist/*

# Check manifest
check-manifest
```

### GitHub Actions Workflows

The project includes several GitHub Actions workflows:

- **Tests and Code Quality** (`python-tests.yml`): Runs on every push and PR
  - Tests on Python 3.9, 3.10, and 3.11
  - Code formatting, linting, and type checking
  - Coverage reporting

- **Build Test** (`build-test.yml`): Tests package building on PRs
  - Validates that the package can be built successfully
  - Tests installation from both wheel and source distributions
  - Validates package metadata

- **Build and Release to PyPI** (`release.yml`): Automated releases
  - Triggers on version tags (e.g., `v0.3.0`)
  - Builds and publishes to PyPI
  - Creates GitHub releases with artifacts

### Release Process

This project uses automated releases through GitHub Actions. To create a new release:

1. **Prepare the release** using the release script:
   ```bash
   # Dry run to see what would happen
   python scripts/release.py --version 0.3.0 --dry-run
   
   # Actually prepare the release
   python scripts/release.py --version 0.3.0
   ```

2. **Push to GitHub** to trigger the release:
   ```bash
   git push origin main
   git push origin v0.3.0
   ```

3. **Monitor the release** at [GitHub Actions](https://github.com/oceanum/intake-gfs-ncar/actions)

The automated workflow will:
- Run all tests across supported Python versions
- Build source and wheel distributions
- Publish to PyPI using trusted publishing
- Create a GitHub release with built artifacts
- Extract release notes from `CHANGELOG.md` if available

#### Manual Release (if needed)

If you need to release manually:

```bash
# Build the package
python -m build

# Check the build
python -m twine check dist/*

# Upload to Test PyPI first (optional)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

#### Test Releases

You can test the release process using Test PyPI:

```bash
# Trigger a test release manually
gh workflow run release.yml --field test_release=true
```

### PyPI Configuration

The project uses PyPI's trusted publishing feature, which eliminates the need for API tokens. The GitHub repository is configured as a trusted publisher for the `intake-gfs-ncar` package on PyPI.

For this to work, the following GitHub repository environments must be configured:
- `pypi`: For production releases to PyPI
- `test-pypi`: For test releases to Test PyPI

Each environment should have appropriate protection rules and the PyPI trusted publishing should be configured to allow releases from this repository.

## License

MIT

## Acknowledgements

This package was developed by [Oceanum](https://oceanum.science) with support from the wider scientific Python community.
