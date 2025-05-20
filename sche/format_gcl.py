import csv
import math

# Read the slot_queue data from the file
with open('sche.txt', 'r') as file:
    lines = file.readlines()

# Find the start and end lines of the slot_queue section
start_line = None
end_line = None
for i, line in enumerate(lines):
    if line.startswith('Timeslot to Queue mapping (slot_queue):'):
        start_line = i + 1
    elif start_line is not None and line.strip() == '':
        end_line = i
        break

# # Get the maximum offset
# max_offset = 0
# with open('output/0-OFFSET.csv', 'r') as file:
#     reader = csv.DictReader(file)
#     max_offset = max(int(row['offset']) for row in reader)

# Extract the slot_queue data
slot_queue_data = lines[start_line:end_line]

# Parse the slot_queue data
slot_queue = {}
current_link = None
max_timeslot = 0
for line in slot_queue_data:
    line = line.strip()
    if line.startswith('Link'):
        # Parse link as node pair
        link_nodes = line.split(':')[0].split('-')[1].strip('(').strip(')').split(', ')
        current_link = (int(link_nodes[0]), int(link_nodes[1]))
        slot_queue[current_link] = {}
    elif line:
        timeslot, queue = int(line.split(':')[0].split()[-1]), int(line.split(':')[1].split()[-1])
        slot_queue[current_link][timeslot] = queue
        max_timeslot = max(max_timeslot, timeslot)

for line in lines:
    if "Minimum offset" in line:
        minimum_offset = int(line.split(": ")[1])
        print(f"Minimum offset: {minimum_offset}")
        break

# Define the cycle time and time slot size
TIME_SLOT_SIZE = 4800
T_PROC = 1200 ## Add preocessing time before each time slot

## Round up to the next power of 10
base_cycle_time = (TIME_SLOT_SIZE + T_PROC) * (max_timeslot + 1) - minimum_offset * TIME_SLOT_SIZE
magnitude = math.floor(math.log10(base_cycle_time)) + 1
CYCLE_TIME = 10 ** magnitude


# Open the output CSV file
with open('output/0-GCL.csv', 'w', newline='') as file:
    fieldnames = ['link', 'queue', 'start', 'end', 'cycle']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # Generate GCL entries for each link and timeslot


    for link, timeslots in slot_queue.items():
        start_time = 0
        end_time =  TIME_SLOT_SIZE - minimum_offset * TIME_SLOT_SIZE
        writer.writerow({
            'link': link,
            'queue': 0,
            'start': start_time,
            'end': end_time,
            'cycle': CYCLE_TIME
        })

        for timeslot, queue in timeslots.items():
            ## Add processing time before each time slot
            ## No need to add the first one
            start_time = end_time
            end_time = start_time + TIME_SLOT_SIZE

            writer.writerow({
                'link': (link[0], link[1]),
                'queue': queue,
                'start': start_time,
                'end': end_time,
                'cycle': CYCLE_TIME
            })

            start_time = end_time
            end_time += T_PROC

            writer.writerow({
                'link': (link[0], link[1]),
                'queue': 0,
                'start': start_time,
                'end': end_time,
                'cycle': CYCLE_TIME
            })
        
        # writer.writerow({
        #     'link': link,
        #     'queue': 0,
        #     'start': max_end + CYCLE_TIME,
        #     'end': max_end + CYCLE_TIME,
        #     'cycle': CYCLE_TIME
        # })
