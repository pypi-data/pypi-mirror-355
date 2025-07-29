<a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&style=for-the-badge" /></a>
<a href="https://paulotto.github.io/projects/jaw-tracking-system/"><img src="https://img.shields.io/badge/Website-JTS-color?style=for-the-badge&color=rgb(187%2C38%2C73)" /></a>

# JawTrackingSystem (JTS): A customizable, low-cost, optical jaw tracking system

A modular and extensible Python package for analyzing jaw motion using motion capture data. 
Designed for research and clinical applications, it provides a flexible pipeline for calibration, 
coordinate transformations, registration, smoothing, visualization, and export of jaw kinematics.
The models for the hardware components are provided as STL files and inside a FreeCAD project file.

---

## Table of Contents
- [Features](#features)
- [Hardware](#hardware)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Setup and Usage](#setup-and-usage)
- [Extending the Framework](#extending-the-framework)
- [Directory Structure](#directory-structure)
- [Testing](#testing)
- [License](#license)
- [Citation](#citation)

---

## Features
- Customizable, 3D-printable hardware components
- Offline or real-time jaw motion analysis (online processing in development)
- Abstract base classes for motion capture data (supports Qualisys, extensible to others)
- Calibration routines for anatomical landmark registration
- Modular pipeline: calibration, relative motion, coordinate transformation, smoothing, visualization, export
- Support for data export in HDF5 format
- Easy configurable via JSON files
- Visualization utilities for 2D/3D trajectories
- Comprehensive logging and error handling
- Test suite for core functionality

## Hardware
The hardware components are designed to be low-cost and customizable. The models for the hardware components are 
provided as STL files and inside a FreeCAD project file. You can find the files in the [models](models) directory.

The mouthpiece, teeth attachment, headpiece, and digitizing pointer are designed to be 3D-printed. 
Since it isn't easy to 3D-print a sharp point for the digitizing pointer, a dart point is used, which can be attached 
to a 2BA thread connected to the digitizing pointer's tip.
For the reflective markers, you can use reflective fibers or reflective tape (see [Components](#components)).

### Components
| <img src=".resources/images/mouthpiece_render_blender.png" height="80"/> | <img src=".resources/images/mouth_attachement_render_blender.png" height="80"/> | <img src=".resources/images/headpiece_render_blender.png" height="80"/> | <img src=".resources/images/calibration_tool_render_blender.png" height="60"/> |
|:------------------------------------------------------------------------:|:-------------------------------------------------------------------------------:|:-----------------------------------------------------------------------:|:------------------------------------------------------------------------------:|
|                                Mouthpiece                                |                                Teeth attachment                                 |                                Headpiece                                |                               Digitizing pointer                               |

| <img src=".resources/images/2ba_thread_background.png" height="200"/> | <img src=".resources/images/dart_point.png" height="200"/> | <img src=".resources/images/reflective_fiber.png" height="130"/> | <img src=".resources/images/tmp_dental_glue.png" height="130"/> |
|:---------------------------------------------------------------------:|:----------------------------------------------------------:|:----------------------------------------------------------------:|:---------------------------------------------------------------:|
|                              2BA thread                               |                         Dart point                         |                         Reflective fiber                         |                      Temporary dental glue                      |

## Installation

Install the package using pip:

```bash
python -m pip install jaw-tracking-system
```
From GitHub:
```bash
python -m pip install git+https://github.com/paulotto/jaw_tracking_system.git
```
Or just clone the repository, copy the `jts` directory to your project, and install the dependencies:

```bash
git clone https://github.com/paulotto/jaw_tracking_system.git 
cd jaw_tracking_system
cp -r jts your_project_directory/
python -m pip install -r requirements.txt
```

### Optional Dependencies
```bash
python -m pip install plotly==6.0.1 qtm_rt
```

## Quick Start

1. Prepare a configuration JSON file (see [README](config/README.md) for examples).
2. Run the analysis pipeline:

```bash
python -m jts.core path/to/config.json
```

3. Results (trajectories, plots, exports) will be saved to the output directory specified in your config.

## Configuration

All analysis parameters are specified in a JSON config file. Key sections include:
- `data_source`: Type (e.g., "qualisys"), filename, and system-specific parameters
- `analysis`: Calibration, experiment intervals, smoothing, coordinate transforms
- `output`: Output directory, file formats, export options
- `visualization`: Plotting options

See [config.json](config/config.json) for a template.

## Setup and Usage
TODO: Describe experimental setup, hardware assembly, and how to run the system.

### As a Script

```bash
python -m jts.core path/to/config.json
```

Optional flags:
- `--verbose` for detailed logging
- `--plot` to show plots interactively

### As a Library

```python
from jts.core import JawMotionAnalysis, ConfigManager

config = ConfigManager.load_config('path/to/config.json')
analysis = JawMotionAnalysis(config)
results = analysis.run_analysis()
```

## Extending the Framework

- Add new motion capture system support by subclassing `MotionCaptureData`.
- Implement new calibration or analysis routines by extending `JawMotionAnalysis`.
- Add new visualization or export utilities in `helper.py`.

## Directory Structure

```
jaw_tracking_system/
├── jts/
│   ├── __init__.py
│   ├── calibration_controllers.py
│   ├── core.py
│   ├── helper.py
│   ├── plotly_visualization.py
│   ├── precision_analysis.py
│   ├── qualisys_streaming.py
│   ├── qualisys.py
│   ├── streaming.py
├── config/
│   ├── README.md
│   └── config.json
├── models/
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_helper.py
│   ├── test_precision_analysis.py
│   └── test_qualisys.py
├── LICENSE
├── MANIFEST.in
├── README.md
├── requirements.txt
├── setup.py
```

## Testing

Run the test suite with:

```bash
pytest tests
```

## License

This project is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0). See the [LICENSE](./LICENSE) file for details.

## Citation

If you use this package in your research, please cite:

```
@software{mueller2025jts,
  author = {Paul-Otto Müller and Sven Suppelt and Mario Kupnik and Oskar von Stryk},
  title = {JawTrackingSystem (JTS): A customizable, low-cost, optical jaw tracking system},
  year = {2025},
  url = {https://github.com/paulotto/jaw-tracking-system},
  version = {1.0.0},
  license = {CC BY-NC-SA 4.0}
}
```

---

For more information, see the [project website](https://paulotto.github.io/projects/jaw-tracking-system/).
