<!--
Author: <Chuanyu> (skewcy@gmail.com)
readme.md (c) 2024
Desc: description
Created:  2024-10-28T17:36:23.579Z
-->

# TSN Testbed Controller

The TSN Testbed Controller is a Python project for managing and controlling a Time-Sensitive Networking (TSN) testbed. It provides functionality to configure switches, assign flows, set up VLANs, configure MSTP, synchronize devices, and run experiments on the testbed.

## Features

- Initialize testbed topology from a configuration file
- Assign flows to the network based on flow, offset, queue, and route information
- Configure VLANs on switches and end stations
- Set up Multiple Spanning Tree Protocol (MSTP) on switches
- Synchronize devices using the Precision Time Protocol (PTP)
- Configure Priority Code Point (PCP) mapping on switches
- Set up Gate Control Lists (GCLs) on switches
- Run experiments by starting and stopping flows

## Prerequisites

- Python 3.x
- Required Python packages: paramiko, tqdm, pandas

## Configuration

The project uses several configuration files:

- `conf.json`: Contains the testbed topology and device information
- Flow-related CSV files:
  - `stream.csv`: Defines the flows in the network
  - `<exp>-0-OFFSET.csv`: Specifies the offsets for each flow
  - `<exp>-0-ROUTE.csv`: Defines the route for each flow
  - `<exp>-0-QUEUE.csv`: Specifies the queue assignment for each flow
- `<exp>-0-GCL.csv`: Contains the Gate Control List (GCL) configuration

## Usage

1. Set up the testbed devices and network topology according to the `conf.json` file. Use bash script under `scripts/` to configure devices and network topology.
2. Prepare the necessary configuration files (`conf.json`, flow-related CSVs, and GCL CSV).
3. Run the `main.py` script to execute the TSN Testbed Controller.

```bash
python3 main.py --topology conf.json --stream stream.csv --config_folder <exp>-schedule
```

- `--topology`: Path to the topology file (conf.json)
- `--stream`: Path to the stream file (stream.csv)
- `--config_folder`: Path to the folder containing schedule files

Note, the `main.py` script will automatically find the unique files in the schedule folder matching the pattern `*-*.csv`. The folder must contain exactly four files: `*-OFFSET.csv`, `*-ROUTE.csv`, `*-QUEUE.csv`, and `*-GCL.csv`.


The `main.py` script performs the following steps:

1. Initializes the testbed topology.
2. Assigns flows to the network.
3. Configures VLANs on switches and end stations.
4. Sets up MSTP on switches.
5. Synchronizes devices using PTP.
6. Configures PCP mapping on switches.
7. Sets up GCLs on switches.
8. Runs the experiment by starting and stopping flows.

## Project Structure

- `cnc/`: Main package directory
  - `__init__.py`: Package initialization file
  - `main.py`: Main script to run the TSN Testbed Controller
  - `model.py`: Defines the data models used in the project
  - `tools.py`: Contains utility functions for various tasks
  - `conf.json`: Configuration file for the testbed topology and devices
  - `configs/`: Directory to store GCL configuration files
- `readme.md`: Project readme file

## License

This project is licensed under the [Insert License Name] License. See the [LICENSE](./LICENSE) file for details.

## Contact

For any questions or inquiries, please contact [Insert Contact Name] at [Insert Contact Email].


---

python3