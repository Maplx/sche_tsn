import paramiko
import pandas as pd
import json
from tqdm import tqdm
import argparse
import os
import subprocess
from typing import Dict, Optional

from main import find_unique_file


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def check_ssh_connection(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=username, password=password)
        ssh.close()
        return True
    except Exception as e:
        print(f"Failed to connect to {ip}: {e}")
        return False


def check_remote_file(ssh, remote_path):
    stdin, stdout, stderr = ssh.exec_command(f"ls {remote_path}")
    if stdout.channel.recv_exit_status() == 0:
        return True
    else:
        return False



def check_input_stream_file(stream_file_path):
    df = pd.read_csv(stream_file_path)
    if df.empty:
        print(f"The input stream file {stream_file_path} is empty")
        return False
    else:
        print(f"✓ The input stream file {stream_file_path} is not empty")

    # Check if the columns are correct
    required_columns = ["id", "src", "dst", "size", "period", "deadline", "jitter"]
    if not all(col in df.columns for col in required_columns):
        print(
            f"The input stream file {stream_file_path} is missing some required columns"
        )
        return False
    else:
        print(f"✓ The input stream file {stream_file_path} has correct columns")

    # Check if dst column is wrapped by []

    if not (df["dst"].str.strip().str.startswith("[").all() and df["dst"].str.strip().str.endswith("]").all()):
        print(f"The dst column in {stream_file_path} is not wrapped by []") 
        return False
    else:
        print(f"✓ The dst column in {stream_file_path} is wrapped by []")

    # Check if deadline is less than period
    if not all(df["deadline"] <= df["period"]):
        print(f"The deadline is not less than period in {stream_file_path}")
        return False
    else:
        print(f"✓ The deadline is less than period in {stream_file_path}")

    # Convert IDs to integers and check if they're continuous
    ids = df['id'].astype(int).tolist()  # Convert to integers
    expected_ids = list(range(len(ids)))  # Create list [0,1,2,...,n-1]

    if ids != expected_ids:
        print("The id column in stream.csv is not continuous")
        assert False

    return True

def check_input_schedule_file(schedule_folder):
    offset_file = find_unique_file(schedule_folder, "*OFFSET.csv")
    if offset_file is None:     
        print(f"No OFFSET.csv file found in {schedule_folder}")
        return False
    else:
        print(f"✓ The OFFSET.csv file found in {schedule_folder}")
    route_file = find_unique_file(schedule_folder, "*ROUTE.csv")
    if route_file is None:
        print(f"No ROUTE.csv file found in {schedule_folder}")
        return False
    else:
        print(f"✓ The ROUTE.csv file found in {schedule_folder}")
    queue_file = find_unique_file(schedule_folder, "*QUEUE.csv")
    if queue_file is None:
        print(f"No QUEUE.csv file found in {schedule_folder}")
        return False
    else:
        print(f"✓ The QUEUE.csv file found in {schedule_folder}")
    gcl_file = find_unique_file(schedule_folder, "*GCL.csv")
    if gcl_file is None:
        print(f"No GCL.csv file found in {schedule_folder}")
        return False
    else:
        print(f"✓ The GCL.csv file found in {schedule_folder}")
    return True

def parse_lldp_output(output: str) -> Optional[Dict]:
    """Parse LLDP output and return neighbor information."""
    if "LLDP neighbors:" not in output:
        return None
    
    neighbor_info = {}
    for line in output.split('\n'):
        line = line.strip()
        if "MgmtIP:" in line and "fe80::" not in line:  # Get IPv4 management IP
            neighbor_info['ip'] = line.split()[-1]
        elif "PortDescr:" in line:
            neighbor_info['port'] = line.split()[-1]
    
    return neighbor_info if neighbor_info else None

def verify_topology(config: Dict) -> bool:
    """Verify if the physical topology matches the configuration file."""
    all_connections_valid = True

    for device_name, device_info in config.items():
        if device_info['type'] != 'sw':
            continue
        
        print(f"\nChecking connections for {device_name}...")
        
        # Create SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                device_info['ip'],
                username=device_info['username'],
                password=device_info['password']
            )

            # Check each port's connection
            for local_port, remote_device in device_info['links'].items():
                interface_name = f"sw0{local_port}"
                stdin, stdout, stderr = ssh.exec_command(f"lldpctl {interface_name}")
                lldp_output = stdout.read().decode()
                
                neighbor = parse_lldp_output(lldp_output)
                expected_ip = config[remote_device]['ip']
                
                if neighbor is None:
                    print(f"❌ {device_name}:{interface_name} -> {remote_device}: No LLDP neighbor found")
                    all_connections_valid = False
                elif neighbor['ip'].split('.')[-1] != expected_ip.split('.')[-1]:
                    print(f"❌ {device_name}:{interface_name} -> {remote_device}: Wrong connection (connected to {neighbor['ip']})")
                    all_connections_valid = False
                else:
                    print(f"✓ {device_name}:{interface_name} -> {remote_device}: Connection verified")
                print(f" Expected IP: {expected_ip}, Actual IP: {neighbor['ip'] if neighbor else 'None'}")
            
            ssh.close()
            
        except Exception as e:
            print(f"Failed to verify connections for {device_name}: {e}")
            all_connections_valid = False
            
    return all_connections_valid

def check_i210_interface(ssh):
    """Check if i210 interface exists on the device."""
    stdin, stdout, stderr = ssh.exec_command("ip link show | grep -i i210")
    if stdout.channel.recv_exit_status() == 0:
        return True
    return False

def main():
    # Add command-line arguments
    parser = argparse.ArgumentParser(description="Configuration Checker")
    parser.add_argument(
        "--topology",
        type=str,
        default="conf.json",
        help="Path to the topology file (conf.json)",
    )
    parser.add_argument(
        "--stream",
        type=str,
        default="stream.csv",
        help="Path to the stream file (stream.csv)",
    )
    parser.add_argument(
        "--config_folder",
        type=str,
        default="./",
        help="Local folder where configuration files are located",
    )
    args = parser.parse_args()

    # Load the configuration (topology) file
    if not os.path.exists(args.topology):
        print(f"Topology file '{args.topology}' not found")
        return

    # Check for the presence of stream.csv
    if not os.path.exists(args.stream):
        print(f"Stream file '{args.stream}' not found")
        return

    config = load_json(args.topology)
    all_checks_passed = True

    # Check SSH connections to all entities
    print("[Step 1] Checking SSH connections...")
    for entity_name, entity_info in config.items():
        print("Checking SSH connection to ", entity_name, " IP: ", entity_info["ip"])
        ip = entity_info["ip"]
        username = entity_info["username"]
        password = entity_info["password"]
        if not check_ssh_connection(ip, username, password):
            print(f"Cannot connect to {entity_name} ({ip})")
            all_checks_passed = False
            assert False
        else:
            print(f"✓ SSH connection to {entity_name} ({ip}) verified")
            
            # Add i210 interface check for end stations
            if entity_info['type'] == 'es':
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=username, password=password)
                if not check_i210_interface(ssh):
                    print(f"❌ i210 interface not found on {entity_name} ({ip})")
                    all_checks_passed = False
                    assert False
                else:
                    print(f"✓ i210 interface found on {entity_name} ({ip})")
                ssh.close()

    # Check if the topology is valid
    print("\n[Step 2] Checking network topology...")
    if not verify_topology(config):
        all_checks_passed = False
        assert False

    # Check if the input .csv files are valid
    print("\n[Step 3] Checking input .csv files...")
    if not check_input_stream_file(args.stream):
        all_checks_passed = False
        assert False

    # Check if the schedule files are valid
    print("\n[Step 4] Checking schedule files...")
    if not check_input_schedule_file(args.config_folder):
        all_checks_passed = False
        assert False
        

    # Add topology verification after other checks
    if all_checks_passed:
        all_checks_passed = verify_topology(config)

    if all_checks_passed:
        print("\nAll configurations are correct and topology is verified.")
    else:
        print("\nSome configurations are missing or topology verification failed.")


if __name__ == "__main__":
    main()
