import csv
import sys
import re

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
}'''

TIME_SLOT_SIZE = 4800
T_PROC = 1200 ## Add preocessing time 


stream_path = sys.argv[1]

# Read the input CSV file
with open(stream_path, 'r') as file:
    reader = csv.DictReader(file)
    rows = list(reader)

## =======   V1: Reserve in the beginning ======================
# Open the output CSV file
# with open('output/0-OFFSET.csv', 'w', newline='') as file:
#     fieldnames = ['stream', 'frame', 'offset']
#     writer = csv.DictWriter(file, fieldnames=fieldnames)
#     writer.writeheader()

#     # Count the number of flows starting from each end-station
#     flow_counts = {}
#     flow_offset_index = {}
#     for i, row in enumerate(rows):
#         src_node = row['Node Path'].split(' -> ')[0]
#         src_id = node_mapping[src_node]
#         src = connected_nodes[src_id]
#         flow_counts[src] = flow_counts.get(src, 0)
#         flow_offset_index[i] = flow_counts[src]
#         flow_counts[src] += 1
#         # print(flow_offset_index[i])

#     # Process each row and calculate the offset
#     for i, row in enumerate(rows):
#         src_node = row['Node Path'].split(' -> ')[0]
#         src_id = node_mapping[src_node]
#         src = connected_nodes[src_id]

#         # Calculate the offset based on the number of flows starting from the same end-station
#         offset = flow_offset_index[i] * TIME_SLOT_SIZE

#         # Write the offset row to the output CSV file
#         writer.writerow({
#             'stream': i,
#             'frame': 0,
#             'offset': offset
#         })
## ============================================================


## =======   V2: Read from the schedule file ======================
offsets = {}
with open('sche.txt', 'r') as file:
    lines = file.readlines()

    for i, line in enumerate(lines):
        if "Offset:" in line:
            offset_start_line = i + 1
            break
    
    for i, line in enumerate(lines[offset_start_line:]):
        if line.strip():
            match = re.match(r'Source: (\d+), App (\d+), Flow (\d+), Instance (\d+): Offset (-*\d+)', line.strip())
            if match:
                source = int(match.group(1))
                app_id = int(match.group(2))
                flow_id = int(match.group(3))
                ins_id = int(match.group(4))
                offset = int(match.group(5))
                
                # Create a tuple key and store offset
                offsets[i] = offset
                # print(f"Line {i}: {offset}")

        if "Minimum offset" in line:
            minimum_offset = int(line.split(": ")[1])
            break
    
with open('output/0-OFFSET.csv', 'w') as file:
    fieldnames = ['stream', 'frame', 'offset']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for i, offset in offsets.items():
        writer.writerow({
            'stream': i,
            'frame': 0,
            'offset': (offset - minimum_offset) * TIME_SLOT_SIZE
        })
    
## ============================================================


