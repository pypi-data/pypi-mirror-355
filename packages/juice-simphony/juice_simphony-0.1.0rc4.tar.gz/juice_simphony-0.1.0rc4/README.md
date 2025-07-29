# Symphony Web


## Getting started


## Project requirements

- Python 3.10

## Install the package

```
pip install juice-simphony
```

## Check spice kernels (for MAPPS products)

Ensure that the spice meta-kernel is aligned with that of the segmentation. 
If not, perform a git checkout accordingly.


## Run the script

Start by running the script with the -h option

```
juice-simphony -h
```
the following output is expected
```
usage: juice-simphony [-h] [--config CONFIG] [--template] [--mapps]

Standalone Simphony Scenario Generator

options:
  -h, --help       show this help message and exit
  --config CONFIG  Path to JSON config file
  --template       Optional flag to dump template and exit
  --mapps          Enable MAPPS-specific behavior
```

Get the template configuration file by executing
```
juice-simphony --template
```
which prints the configuration file in data/config_scenario.json.

```
{
  "juice_conf": "$HOME/juice_conf",
  "output_folder": "$HOME/JUICE_PREOPS/PLANNING",
  "kernel_abs_path": "$HOME/juice/kernels",
  "scenario_id": "S008_01",
  "shortDesc": "ORB17",
  "trajectory": "CREMA_5_1_150lb_23_1_a3",
  "mnemonic": "S008_ORB17_S13P00",
  "startTime": "2032-12-18T17:32:33",
  "endTime": "2033-01-08T21:05:31",
  "main_target": "Jupiter",
  "iniAbsolutePath": "SOFTWARE/MAPPS",
  "descriptions": {
    "juice_conf": "JUICE configuration folder",
    "output_folder": "output folder main path; for simplicity, please do not update",
    "kernel_abs_path": "$HOME/juice/kernels",
    "scenario_id": "number of the science scenario as per SOCs reference (scenario_number plus version index); expected format: 1 letter + 3 digits + _ + 2 digits (e.g., 'S008_01')",
    "shortDesc": "string for the output folder",
    "trajectory": "trajectory identifier, to be used together with mnemonic",
    "mnemonic": "mnemonic of the trajectory; to be used together with trajectory",
    "startTime": "scenario start time; timestamp in ISO 8601 format YYYY-MM-DDTHH:MM:SS",
    "endTime": "scenario end time; timestamp in ISO 8601 format YYYY-MM-DDTHH:MM:SS",
    "main_target": "object of interest (used for MAPPS output)",
    "iniAbsolutePath": "string (used for MAPPS output)"
  }
}
```
Execute the package via 
```
juice-simphony --config yourpath/config_scenario.json 

or

juice-simphony --config yourpath/config_scenario.json  --mapps
```
where the --mapps option allows the generation of MAPPS specific outputs.

The output is a zip file in the output folder provided above in the configuration. 
