# BioImageSuiteLite

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/bioimagesuitelite.svg)](https://badge.fury.io/py/bioimagesuitelite)

**An Interactive Open-Source Platform for Automated Detection and Analysis of Transient Events in Time-Lapse Microscopy**

![1750010543782](image/README/1750010543782.png)

***A screenshot of the main BioImageSuiteLite interface.***

---

## Overview

BioImageSuiteLite is a user-friendly desktop application designed for biologists and researchers to analyze time-lapse microscopy data. It simplifies the entire workflow from data import to results export, enabling rapid, reproducible analysis of cellular events.

The tool provides an intuitive graphical user interface (GUI) built on the powerful [Napari](https://napari.org/) viewer, allowing users to:

- **Load Data:** Directly import `.avi` files or multi-page `.tif`/`.tiff` stacks.
- **Define Regions of Interest (ROIs):** Interactively draw multiple ROIs to focus analysis on specific areas.
- **Process & Segment:** Apply Difference of Gaussians (DoG) filtering for feature enhancement and use Otsu's method for robust, automated segmentation.
- **Analyze & Visualize:** Automatically calculate and plot event frequency, intensity dynamics, and other key metrics over time.
- **Export Results:** Save analysis data (e.g., events per second per area) to `.csv` files for further analysis and plotting.

## Installation

We recommend installing BioImageSuiteLite into a dedicated virtual environment.

### 1. Simple Installation (Recommended)

Install the package directly using pip:

```bash
# It is recommended to create a virtual environment first
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install from PyPI
pip install bioimagesuitelite
```

### 2. To install the latest development version directly from GitHub:

For the latest development version:

```bash
pip install git+https://github.com/InnovationLine/BioImageSuiteLite.git
```

## Quick Start

1. **Launch the application:**
   Open your terminal or command prompt (with the virtual environment activated) and run:
   ```bash
   bioimagesuitelite
   ```
2. **Load Data:**
   Click the **"Load File"** button to open your microscopy data (`.avi` or `.tif`/`.tiff`).
3. **Draw an ROI:**
   Select the **Polygon tool** from the Napari layer controls (top left) and draw one or more regions around the cells you want to analyze.
4. **Run Analysis:**
   Adjust parameters in the GUI dock widget as needed (e.g., Gaussian sigma, thresholding method). Click the **"Run Analysis"** button to start processing.
5. **Explore Results:**
   View the generated plots for event traces and intensity profiles. Use the **"Save Data"** button to export your quantitative results to a CSV file.

For a detailed reference, see the full [User Guide](./UserGuide.md).

## System Requirements

- Python >= 3.8
- The core dependencies are listed in the `pyproject.toml` file and include:
  - `numpy`
  - `scipy`
  - `opencv-python-headless`
  - `tifffile`
  - `scikit-image`
  - `napari[all]`
  - `shapely`
  - `ruptures`

## How to Cite

If you use BioImageSuiteLite in your research, please cite it. Once we have a DOI, we will update this section with the proper citation format.

## Tutorial: An Interactive Guide

For a hands-on tutorial that walks you through a complete analysis workflow—from loading data to exporting results—please see our comprehensive Jupyter Notebook. This is the best place to start to understand the full capabilities of BioImageSuiteLite.

➡️ **[Launch the Interactive Tutorial](./examples/comprehensive_analysis_guide.ipynb)**

## For Developers

We welcome contributions! To set up a development environment:

### Setting up the Environment

```bash
# Clone the repository
git clone https://github.com/InnovationLine/BioImageSuiteLite.git
cd BioImageSuiteLite

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode with developer dependencies
pip install -e .
```

### Running the GUI from source

To launch the GUI directly from the source code, run:

```bash
python -m BioImageSuiteLite.gui_manager
```

For more details on the project structure and architecture, please see our [Architecture Guide](./ARCHITECTURE.md).

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
This license permits free use, modification, and distribution of the software, provided the original copyright and license notice are included in any copies.

## Citation

*BioImageSuiteLite* is academic software. If you use it in your research, please cite it as follows:

**[Citation details will be added here once a DOI is generated.]**
