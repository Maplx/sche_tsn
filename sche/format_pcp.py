import csv
import re

def parse_flow_pcp_mapping(sche_file):
    """Parse the flow to PCP mapping from sche.txt"""
    flow_pcp = {}
    flow_id = 0  # Global counter for flows across all applications
    with open(sche_file, 'r') as f:
        content = f.read()
        # Find the flow to PCP mapping section
        pattern = r'Application (\d+), Flow (\d+): PCP (\d+)'
        matches = re.finditer(pattern, content)
        for match in matches:
            app_id, local_flow_id, pcp = map(int, match.groups())
            flow_pcp[flow_id] = pcp
            flow_id += 1
    return flow_pcp

def main():
    # Read flow to PCP mapping
    flow_pcp = parse_flow_pcp_mapping('sche.txt')
    
    # Write PCP mapping to CSV
    with open('output/0-PCP.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['stream', 'pcp'])
        
        for stream_id, pcp in flow_pcp.items():
            writer.writerow([stream_id, pcp])

if __name__ == '__main__':
    main()
