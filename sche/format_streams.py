import csv
import sys
import numpy as np

node_mapping = {
    'S1': 0,
    'S2': 1,
    "S3": 2,
    "S4": 3,
    'S5': 4,
    'S6': 5,
    'S7': 6,
    'S8': 7
}

# Define the mapping of node IDs to their connected nodes
connected_nodes = {
    0: 8,
    1: 9,
    2: 10,
    3: 11,
    4: 12,
    5: 13,
    6: 14,
    7: 15
}

'''
# Define the mapping of nodes to their IDs
node_mapping = {

    'A': 4,
    'B': 5,
    'C': 6,
    'D': 7
}

# Define the mapping of node IDs to their connected nodes
connected_nodes = {
    4: 12,
    5: 13,
    6: 14,
    7: 15
}
'''
with open('output/0-GCL.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        cycle_time = int(row['cycle'])

stream_path = sys.argv[1]
# Read the input CSV file
with open(stream_path, 'r') as file:
    reader = csv.DictReader(file)
    rows = list(reader)

# Convert Period strings to integers before calculating LCM
hyperperiod = np.lcm.reduce([int(row['Period']) for row in rows])

# Open the output CSV file
with open('output/stream.csv', 'w', newline='') as file:
    fieldnames = ['id', 'src', 'dst', 'size', 'period', 'deadline', 'jitter']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # Process each row
    for i, row in enumerate(rows):
        node_path = row['Node Path'].split(' -> ')
        src_node = node_path[0]
        dst_node = node_path[-1]

        # Map nodes to their IDs
        src_id = node_mapping[src_node]
        dst_id = node_mapping[dst_node]

        # Get the connected nodes for the start and end nodes
        src = connected_nodes[src_id]
        dst = [connected_nodes[dst_id]]

        # Write the converted row to the output CSV file
        writer.writerow({
            'id': i,
            'src': src,
            'dst': dst,
            'size': 500,
            'period': cycle_time,
            'deadline': cycle_time,
            'jitter': cycle_time, 
        })