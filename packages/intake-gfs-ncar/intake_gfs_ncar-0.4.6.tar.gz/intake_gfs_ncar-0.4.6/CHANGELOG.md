# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2023-06-30

### Added
- Added `gfs_surface_winds` predefined dataset for accessing 10m wind components
- Added `gfs_ice_concentration` predefined dataset for accessing sea ice concentration
- Added example scripts for predefined datasets in examples/dataset_examples/
- Added GitHub Actions workflow for CI testing
- Added comprehensive .gitignore file

### Changed
- **Breaking:** Replaced `date_str` and `model_run_time` parameters with a single `cycle` parameter in ISO format
- **Breaking:** Changed `max_lead_time_fXXX` to `max_lead_time` that takes an integer value
- Updated package dependencies and requirements
- Improved error handling and logging for date/time parsing
- Enhanced code robustness with better error handling and validation

### Fixed
- Fixed handling of "latest" parameter option 
- Improved datetime parsing to handle more formats
- Fixed various edge cases in the examples

## [0.1.0] - 2023-01-15

### Added
- Initial release
- Basic GFS forecast data driver
- Support for filtering by variable, level, and forecast lead time
- Example scripts for common use cases