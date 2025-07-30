# Midas PowerSeries

The midas power series module is a general purpose data simulator, currently focussed on csv files.

Although this package is intended to be used with midas, it can be used in any mosaik simulation scenario.

## Installation

This package will usually be installed automatically by most of the other data simulators from midas. 
It is available on pypi, so you can install it manually with

```bash
pip install midas-powerseries
```

## Usage

The complete documentation is available at https://midas-mosaik.gitlab.io/midas.

### Inside of midas

There are already a few data simulators for specific data sets that can be used instead of this simulator.
However, if you have a csv file with time series and want to use it in a midas scenario, you have to add `powerseries` to your modules

```yaml
my_scenario:
  modules:
    - powerseries
    - ...
```

The configuration needs to provide the path to your csv file and how the data should be connected to the power grid.

```yaml
  powerseries_params:
    my_grid_scope:
      step_size: 900  # <-- Default value
      data_path: "path/to/folder/containing/csv/file"
      filename: "my_time_series.csv"
      data_step_size: 900  # <-- Default value
      data_scaling: 1.0  # Default value; use it if your data is, e.g., in kW instead of MW
      meta_scaling: 1.0  # Default value; use it to scale all of the time series globally
      active_mapping:
        0: [[load_01_p_mw, 1.0], [load_02_p_mw], 1.2]  # load_01_p_mw and load_02_p_mw have to be column names in the csv file
```

### Any mosaik scenario

tbd

## License

This software is released under the GNU Lesser General Public License (LGPL). 
See the license file for more information about the details.