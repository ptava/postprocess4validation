# postprocess4validation

This is an alpha release (v0.1.0a0). The package is functional but still under active development.
- [x] Quantitative analysis of OpenFOAM simulation results
- [x] Qualitative analysis of OpenFOAM simulation results
- [x] Pre-processing for OpenFOAM simulations
- [ ] Rebuild lost tests suite

## Disclaimer
This Python package is a personal tool developed to automate OpenFOAM computational model validation against experimental data. Given that the project evolved from individual experimentation, many design choices, implementations, and workarounds may appear unnecessarily complex or inefficient. You will encounter parts of the codebase -particularly related to data loading, storage, and plot generation - that clearly need refactoring and optimization (refer to open issues for details)

Be aware that certain solutions may seem overly complicated or suboptimal. Contributions, suggestions, and improvements are welcome; however, please understand that the original intent was personal use, and the current state of the code reflects that fact.

<!-- [![PyPI version](https://img.shields.io/pypi/v/postprocess4validation.svg)](https://pypi.org/project/postProcess4Validation/) -->
<!-- [![Python Version](https://img.shields.io/pypi/pyversions/postprocess4validation.svg)](https://pypi.org/project/postProcess4Validation/) -->
<!-- [![License](https://img.shields.io/github/license/ptava/postprocess4validation.svg)](https://github.com/ptava/postProcess4Validation/blob/main/LICENSE) -->

## Overview

**postprocess4validation** is a Python-based tool designed to analyze and compare OpenFOAM simulation results with experimental data. It supports both steady and unsteady cases, handling scalar quantities only. The tool computes statistical metrics and visualizes results in interactive 2D and 3D plots.

## Features

### 1. Quantitative Analysis:
- Computes statistical metrics such as Normalised Mean Squared Error (NMSE), Geometric Mean Bias (MG), and Geometric Variance (GV) based on point-wise experimental data and OpenFOAM probes sampling
- Compares multiple simulation setups with interactive visualization
- Outputs statistical metrics values and representative plots for each field available
- 2D log-log plot MG vs. GV
- 3D plot of Normalised Relative Error (NRE)
- Interactive lens feature for detailed exploration of data points (toggle with space bar)
- Includes stl geometry if provided
- OpenFOAMProbesLoader defined to handle OpenFOAM probes data structure:
    "\<case-folder\>/postProcessing/\<probes-folder\>/\<time\>/\<probe-file\>"
- ProbesLoader defined to handle csv probes data with \<probe-file\>:

        file name: "<field>"

        # x0,y0,z0,
        # x1,y1,z1,
        ...
        # xN,yN,zN,
        t0, field0, field1, ..., fieldN
        t1, field0, field1, ..., fieldN
        ...
        tM, field0, field1, ..., fieldN

Quantitative comparison of experimental and model results are performed using the following statistical performance measures, where $P_i$ is the model prediction, and $O_i$ is the observed value:

#### <u>Geometric mean bias</u> ($MG$)

This is the logarithmic measure of the mean relative bias.  
- Strongly influenced by extremely low observations and predictions.  
- Less sensitive to infrequent high concentrations than the fractional bias.  
- Indicates only systematic errors.

For an ideal model, $MG = 1$.

$$
MG = \exp\left( \frac{1}{n} \sum_{i=1}^n \ln O_i - \frac{1}{n} \sum_{i=1}^n \ln P_i \right)
$$

#### <u>Geometric variance</u> ($VG$)

A metric like the NMSE that shows the scatter in the data, including both systematic and random errors.  
For an ideal model prediction, $VG = 1$.

$$
VG = \exp\left( \frac{1}{n} \sum_{i=1}^n \left( \ln O_i - \ln P_i \right)^2 \right)
$$

#### <u>Normalised mean square error</u> ($NMSE$)

A measure of scatter that includes both systematic and random errors.  
- For an ideal model prediction, $NMSE = 0$  
- Not meaningful for variables that can be both positive and negative (e.g., velocity components).

$$
NMSE = \frac{1}{n} \sum_{i=1}^n \frac{(O_i - P_i)^2}{\overline{O} \, \overline{P}}
$$

#### <u>Normalised relative error</u> ($NRE_i$)

A local measure of the relative difference between predicted and observed values, computed at each spatial point $i$.  Used for visualisation purposes (e.g. 3D error plots).  

$$
    NRE_i = \left| \frac{P_i - O_i}{O_i} \right|
$$

## 2. Qualitative analysis
- Detects and plots lines and planes based on point-wise experimental data and OpenFOAM lines sampling
- Detects lines across multiple simulations and plots lines with data: a line has data if at least one simulation result is stored in it
- It plots only planes with data in it: a plane has data if there is at least N lines with data where N can be selected by the user
- Interactive scaling parameter to improve visualization run-time
- Includes stl geometry if provided, showing geometry intersections with the plotted planes
- OpenFOAMLinesLoader to handle OpenFOAM lines data structure:
    "\<case-folder\>/postProcessing/\<lines-subfolder\>/\<time\>/\<line-file\>"
- LinesLoader to handle raw lines data:
    with <line-file>:

        file name: "line_<float>_<float>_<field0>_..._<fieldN>"

        coord_0, field0, ... , fieldN
        coord_1, field0, ... , fieldN
        ...
        coord_N, field0, ... , fieldN


## 3. Pre-proceessing
- Writes function object file for OpenFOAM simulations starting from  user-provided csv file with points info
- Writes 'probes' and 'lines' function object file

TO DO:
 user should be able to create a plot representing the 3d domain to visualize points location and lines automatically detected for post-processing


## Installation

<!-- ### From PyPI -->
<!-- ```bash -->
<!-- pip install postprocess4validation -->
<!-- ``` -->

### From Source
```bash
git clone https://github.com/ptava/postprocess4validation.git
cd postprocess4validation
pip install .
# or with uv
uv pip install .
```

### Development Installation
```bash
git clone https://github.com/ptava/postprocess4validation.git
cd postprocess4validation
pip install -e ".[dev]"
# or with uv
uv pip install -e ".[dev]"
```

## Usage

### Command Line Interface

#### Quantitative Analysis
```bash
# Process a single simulation
quantitative-cli --single path/to/postProcessing --exp path/to/expData.csv

# Process multiple simulations (automatically detected)
quantitative-cli --exp path/to/expData.csv

# Save plot without displaying
quantitative-cli --exp path/to/expData.csv --save-only

# Enable interactive lens and add geometru to 3D plot
quantitative-cli --exp path/to/expData.csv --interactive --stl path/to/geometry.stl
```

#### Qualitative Analysis
```bash
# Process a single simulation
qualitative-cli --single path/to/postProcessing --exp path/to/expData.csv

# Process multiple simulations (automatically detected)
qualitative-cli --exp path/to/expData.csv

# Save plot without displaying
qualitative-cli --exp path/to/expData.csv --save-only

# Enable interactive scaling and add geometry sections to 2D plots
qualitative-cli --exp path/to/expData.csv --interactive --stl path/to/geometry.stl


```

### Python API

```python
from postprocess4validation.quantitative import (
    process_exp_data, 
    process_probes_files,
    compute_metrics, 
    create_plot, 
    fill_plot, 
    finalize_plot
)
from matplotlib import pyplot as plt

# Load data
exp_dataset = process_exp_data("path/to/expData.csv")
sim_dataset = process_probes_files("path/to/postProcessing/probes")

# Compute metrics
results = compute_metrics(exp_dataset, sim_dataset)

# Visualize results
fig, ax = create_plot()
fill_plot(ax, "simulation", results)
finalize_plot(ax)
plt.show()
```

## Input Data Format

### Experimental Data
CSV file containing probe points and measured scalar quantities:
```
x,y,z,U,p
0.1,0,0,1.0,101325.0
0.2,0,0,2.0,101320.0
```

### Simulation Data
Standard OpenFOAM probes output format in the `postProcessing/probes` directory.
Standard OpenFOAM lines output format in the `postProcessing/lines` directory

## Outputs

### Quantitative package
- **Metrics**: Statistical results saved to a CSV file
- **Plots**: 

    ⇲Interactive visualization of statistical metrics (Geometric Bias vs Geometric Variance)

    ⇲Interactive visualization of relative error in all available points in a 3D plot

### Qualitative package
- **Plots**: 
    ⇲ Interactive visualization of all the available lines data that can be compared with the provided experiment data. All plots are grouped based on their normal component. The package plots only the planes and lines with data in it, among all planes and lines that could be visualized from the provided data-set.

## Dependencies

- numpy
- matplotlib
- mplcursors
- numpy-stl
- trimesh

## Development

### Running Tests

### Code Formatting

### Type Checking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) file for details about changes in each release.
