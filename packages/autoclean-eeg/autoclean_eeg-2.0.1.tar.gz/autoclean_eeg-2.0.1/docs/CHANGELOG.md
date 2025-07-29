# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 6/12/2025

### 🚨 LARGE CHANGES
- **Pipeline API**: Changed `autoclean_dir` parameter to `output_dir` in Pipeline constructor
- **Configuration**: Removed `autoclean_config` parameter - YAML configuration no longer required
- **Task System**: Combined previous task files and yaml config files into one simplified task file
- **Workspace Management**: Complete overhaul of user workspace setup and management
- **Task Validation**: Simplified requirements - only `run_id`, `unprocessed_file`, and `task` now required
- **CLI Support**: Added cli interface for workspace managment and processing files. Can be combined with uv tools. 

### Added
- **Python Task Files**: Create custom tasks as Python files with embedded configuration
- **Workspace Setup Wizard**: Interactive setup for first-time users with automatic workspace creation
- **Dynamic Task Discovery**: Automatic discovery and registration of custom Python task files
- **Export Counter System**: Streamlined data export tracking replacing complex stage file management
- **Production Deployment**: Complete dependency locking with requirements.txt generation
- **Enhanced Error Handling**: Improved error messages and validation throughout pipeline

### Changed
- **Simplified Architecture**: Removed YAML configuration dependencies for built-in tasks
- **Modern API Design**: Consistent parameter naming across all components
- **User Experience**: Streamlined workflow for both basic and advanced users
- **Test Coverage**: Achieved 85.8% test pass rate with comprehensive integration testing
- **Code Quality**: 100% compliance with Black, isort, and Ruff formatting standards
- **Memory Management**: Optimized processing workflows for better resource utilization

### Migration Guide
**Breaking Changes Require Updates:**

1. **Pipeline Initialization**:
   ```python
   # OLD (v1.4.1)
   pipeline = Pipeline(autoclean_dir="output", autoclean_config="config.yaml")
   
   # NEW (v2.0.0)
   pipeline = Pipeline(output_dir="output")
   ```

2. **Task Configuration**:
   - YAML configuration files no longer required for built-in tasks
   - Custom tasks now defined as Python files with embedded settings
   - Simplified task validation with fewer required fields

3. **Workspace Setup**:
   - New interactive setup wizard on first run
   - Automatic workspace creation and management
   - Enhanced custom task discovery and organization

## [1.4.1] - 5/21/2025

### Changed
- Switched database from unqlite to sqlite to prevent build issues and for long term sustainability 
- Created Mixin base class that defines helper functions for all mixins
- Changed bids creation step function to a mixin for ease of use

### Fixed
- Fixed a bug where when using threshold rejection for epoching export would fail due to custom event handling 
- Fixed issue with cached versions of docker-review gui leading to infinite browser refresh

## [1.4.0] - 5/15/2025

### Added
- Added native ICA support using MNE and mne_icalabel
- Added native segment rejection features adapted from the pylossless pipeline
- Added basic steps mixin. Runs configured steps for resampling, filtering, trimming and cropping, dropping channels, and marking EOGs

### Changed
- Completely removed pylossless leading to further modularity

[1.4.0]: https://github.com/cincibrainlab/autoclean_pipeline/releases/tag/v1.4.0

## [1.3.0] - 4/30/2025

### Added
- Added MFF file support 
- Added proper documentation site linked on the GitHub 
- Added event retention after epoching
- Added async lock to BIDS function to prevent errors related to concurrent file writes
- Moved IO functions into their own module 

### Fixed
- Fixed all pylint warnings and properly formatted all code in src
- Fixed logger so that batch runs do not repeat outputs

### Deprecated
- Deprecated pydantic metadata models and legacy tools
- Deprecated the majority of step functions in favor of mixins 

[1.3.0]: https://github.com/cincibrainlab/autoclean_pipeline/releases/tag/v1.3.0

## [1.2.0] - 03/19/2025

### Added
- Added robust system for flagging concerning behavior in processing
- Added customized pylossless pipeline function
- Added task for converting .raw to .set files
- Further optimizations and testing for ideal cleaning parameters

[1.2.0]: https://github.com/cincibrainlab/autoclean_pipeline/releases/tag/v1.2.0

## [1.1.0] - 03/3/2025

### Added
- Modularized import system further using mixins
- Mixins are imported in task base class
- Plugins added for custom import behavior
- Refresh files button to autoclean_review
- Complete documentation site

### Deprecated  
- Most basic step functions

[1.1.0]: https://github.com/cincibrainlab/autoclean_pipeline/releases/tag/v1.1.0

## [1.0.0] - 02/28/2025

### Added
- Initial release of AutoClean EEG
- Core pipeline functionality
- Support for multiple EEG paradigms
- BIDS-compatible data organization
- Quality control and reporting system
- Database-backed processing tracking
- Task-based modular architecture

[1.0.0]: https://github.com/cincibrainlab/autoclean_pipeline/releases/tag/v1.0.0