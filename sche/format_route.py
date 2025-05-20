import csv
import sys


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

stream_path = sys.argv[1]
# Read the input CSV file
with open(stream_path, 'r') as file:
    reader = csv.DictReader(file)
    rows = list(reader)

# Open the output CSV file
with open('output/0-ROUTE.csv', 'w', newline='') as file:
    fieldnames = ['stream', 'link']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # Process each row and calculate the route
    for i, row in enumerate(rows):
        node_path = row['Node Path'].split(' -> ')
        
        # Add the source node to the beginning of the path
        src_node = node_path[0]
        src_id = node_mapping[src_node]
        src = connected_nodes[src_id]
        node_path.insert(0, src)
        
        # Add the destination node to the end of the path
        dst_node = node_path[-1]
        dst_id = node_mapping[dst_node]
        dst = connected_nodes[dst_id]
        node_path.append(dst)
        
        # Write the route links to the output CSV file
        for j in range(len(node_path) - 1):
            if node_path[j] in node_mapping:
                src_id = node_mapping[node_path[j]]
            else:
                src_id = node_path[j]
            if node_path[j+1] in node_mapping:
                dst_id = node_mapping[node_path[j+1]]
            else:
                dst_id = node_path[j+1]
            link = (src_id, dst_id)
            writer.writerow({
                'stream': i,
                'link': link
            }) 