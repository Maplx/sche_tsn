import csv
import sys
import re

# Read the flow to PCP mapping from sche.txt
flow_to_pcp = {}
with open('sche.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        if 'Application' in line:
            parts = line.split(':')
            app_flow = parts[0].strip()
            pcp = int(parts[1].strip().split(' ')[1])
            flow_to_pcp[app_flow] = pcp

# Read the PCP to queue mapping from sche.txt
pcp_to_queue = {}
with open('sche.txt', 'r') as file:
    lines = file.readlines()
    for i, line in enumerate(lines):
        if 'Link' in line and 'PCP' in line and 'Queue' in line:
            link = re.search(r'(\d+, \d+)', line).group(1)
            link = eval(link)
            pcp = re.search(r'PCP \d+', line).group(0).split(' ')[1]
            pcp = int(pcp)
            queue = re.search(r'Queue \d+', line).group(0).split(' ')[1]
            queue = int(queue)
            pcp_to_queue[(link, pcp)] = queue

# Read the route information from route.csv
route_info = {}
with open('output/0-ROUTE.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        stream = int(row['stream'])
        link = eval(row['link'])
        if stream not in route_info:
            route_info[stream] = []
        route_info[stream].append(link)

stream_path = sys.argv[1]

# Read the flows_information_with_nodes.csv file
with open(stream_path, 'r') as f:
    reader = csv.DictReader(f)
    flows = list(reader)

# Open the output CSV file
with open('output/0-QUEUE.csv', 'w', newline='') as file:
    fieldnames = ['stream', 'frame', 'link', 'queue']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # Process each stream and compute the queue assignment
    for stream, links in route_info.items():
        # Find the corresponding flow information
        try:
            flow = flows[stream]
        except IndexError:
            print(f"Flow {stream} not found")
            continue
    
        app_id = flow['App ID']
        flow_id = flow['Flow ID']
        app_flow = f'Application {app_id}, Flow {flow_id}'
        pcp = flow_to_pcp[app_flow]

        for link in links:
            if (link, pcp) in pcp_to_queue:
                queue = pcp_to_queue[(link, pcp)]
            else:
                queue = 0

            writer.writerow({
                'stream': stream,
                'frame': 0,
                'link': link,
                'queue': queue
            }) 