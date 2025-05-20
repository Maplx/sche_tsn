"""
Author: <Chuanyu> (skewcy@gmail.com)
main.py (c) 2024
Desc: description
Created:  2024-10-30T17:55:31.428Z
"""

import re
import z3
import csv
import sys
import numpy as np
# Step 1: Parse the Input Data

OFFSET_MAX = -3

stream_path = sys.argv[1]
sche_path = sys.argv[2]

# Flow description as a string
with open(stream_path, 'r') as f:
    flow_description = f.read()

# Schedule description as a string
with open(sche_path, 'r') as f:
    schedule_description = f.read()
    
# Define the mapping of nodes to their IDs
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

# Link to nodes mapping
link_to_nodes = {}

# Parse flow description
flows = []
applications = set()
links_set = set()
flow_lines = flow_description.strip().split("\n")[1:]  # Skip header

for line in flow_lines:
    parts = line.strip().split(",")
    app_id = int(parts[0])
    flow_id = int(parts[2])
    links = list(map(int, re.findall(r"\d+", parts[3])))
    ## Add the trailing link [to dst]

    nodes = [node_mapping[x] for x in parts[4].split(" -> ")]
    for i in range(len(links)):
        link_to_nodes[links[i]] = (nodes[i], nodes[i+1])
     
    period = int(parts[5])
    flows.append(
        {
            "app_id": app_id,
            "flow_id": flow_id,
            "links": links,
            "nodes": nodes,
            "period": period,
            "src": connected_nodes[nodes[0]],
            "dst": connected_nodes[nodes[-1]]
        }
    )
    applications.add(app_id)
    links_set.update(links)

hyper_period = np.lcm.reduce([f["period"] for f in flows])
flow_ins_nums = [hyper_period // f["period"] for f in flows]
applications = sorted(applications)
links_list = sorted(links_set)



# Build flow_links: mapping from (app_id, flow_id) to set of links used
flow_links = {}
for flow in flows:
    app_id = flow["app_id"]
    flow_id = flow["flow_id"]
    links = flow["links"]
    flow_links[(app_id, flow_id)] = set(links)

# Parse schedule description
schedule_lines = schedule_description.strip().split("\n")
schedule_header = schedule_lines[0].strip().split(",")
schedule_data = schedule_lines[1:]
num_timeslots = len(schedule_data)
num_links = len(schedule_header) - 1  # Exclude 'Time Slot' column

schedule = {} ## Return a app_id
for line in schedule_data:
    parts = line.strip().split(",")
    t = int(parts[0])
    for l in range(num_links):
        app = int(parts[l + 1])
        schedule[(t, l)] = app

# ================================================
# Step 2: Define Variables using Z3
# ================================================

solver = z3.Solver()

# Variables:

# flow_pcp[a,f] ∈ {0,..,7}
flow_pcp = {}
for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    flow_pcp[a, f] = z3.Int(f"flow_pcp_{a}_{f}")
    solver.add(z3.And(flow_pcp[a, f] >= 1, flow_pcp[a, f] <= 7))

# pcp_queue[l, pcp] ∈ {1,..,7}
pcp_queue = {}
for l in links_list:
    pcp_queue[l] = z3.Array(f"pcp_queue_{l}", z3.IntSort(), z3.IntSort())
    for pcp in range(1, 8):
        solver.add(z3.And(pcp_queue[l][pcp] >= 1, pcp_queue[l][pcp] <= 7))

# slot_queue[l][t] ∈ {0,..,7}
slot_queue = {}
for l in range(num_links):
    for t in range(num_timeslots):
        slot_queue[l, t] = z3.Int(f"slot_queue_{l}_{t}")
        solver.add(z3.And(slot_queue[l, t] >= 1, slot_queue[l, t] <= 7))

# Offset variables for each instance of each flow
offset = {}
for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    ins_num = flow_ins_nums[flows.index(flow)]
    offset[a, f] = [z3.Int(f"offset_{a}_{f}_{i}") for i in range(ins_num)]
    for i in range(ins_num):
        ## You may need to change this value if no solution found. TODO: Change this as a objective
        solver.add(offset[a, f][i] >= OFFSET_MAX)  # Offsets can be -1 or greater

# Step 3: Set Up Constraints
    
assign_flow_slot = {}
for t in range(num_timeslots):
    for l in range(num_links):
        key = (t, l)
        if key in schedule:
            a = schedule[key]
            if a != -1:
                # Find all flows of application a that use link l
                app_flows = [flow for flow in flows if flow["app_id"] == a and l in flow["links"]]
                for flow in app_flows:
                    f = flow["flow_id"]
                    ins_num = flow_ins_nums[flows.index(flow)]
                    for i in range(ins_num):
                        var_name = f"assign_flow_slot_{a}_{f}_{i}_{t}_{l}"
                        assign_flow_slot[l, t, a, f, i] = z3.Bool(var_name)

# Step 3: Set Up Constraints

# Constraint 1: For each link l, pcp_queue[l][pcp] are all different (one-to-one mapping)
ingress_port_links = {}
for l in links_list:
    pcp_values = [pcp_queue[l][pcp] for pcp in range(1,8)]
    solver.add(z3.Distinct(pcp_values))

    src = link_to_nodes[l][0]
    ingress_port_links.setdefault(src, []).append(l)

## Since PCP mapping happens on ingress, we need to avoid such cases (a, b) != (a, c)
## All mapping from (a, x) should be the same

# Enforce consistent PCP-to-Queue mapping for each ingress port -> This is not possible cause the last-hop link use (any, 0)
# for _, links in ingress_port_links.items():
#     if len(links) > 1:
#         # Use the first link in the group as the base reference
#         base_link = links[0]
#         for pcp in range(1, 8):
#             for other_link in links[1:]:
#                 solver.add(pcp_queue[other_link][pcp] == pcp_queue[base_link][pcp])

## Can simply avoid two streams from the same ingress port use the same PCP
## This works but impose stricter constraints
## IN-USE Solution ⬇️ ================================================

# If two flows share the same ingress port, they cannot have the same PCP

flows_by_ingress = {}
for flow in flows:
    src_node = flow["nodes"][0]  # First node is the ingress
    if src_node not in flows_by_ingress:
        flows_by_ingress[src_node] = []
    flows_by_ingress[src_node].append(flow)

# Add constraints to ensure flows from same ingress use different PCPs
for ingress_node, ingress_flows in flows_by_ingress.items():
    # For each pair of flows from the same ingress
    for i in range(len(ingress_flows)):
        flow1 = ingress_flows[i]
        a1, f1 = flow1["app_id"], flow1["flow_id"]
        for j in range(i + 1, len(ingress_flows)):
            flow2 = ingress_flows[j]
            a2, f2 = flow2["app_id"], flow2["flow_id"]
            # Add constraint that their PCPs must be different
            solver.add(flow_pcp[a1, f1] != flow_pcp[a2, f2])

# Constraint 2: For each timeslot t, link l, application a scheduled at t,l:
for t in range(num_timeslots):
    for l in range(num_links):
        key = (t, l)
        if key in schedule:
            a = schedule[key]
            if a != -1:
                # Find all flows of application a that use link l
                app_flows = [flow for flow in flows if flow["app_id"] == a and l in flow["links"]]

                queue_constraints = []
                for flow in app_flows:
                    f = flow["flow_id"]
                    ins_num = flow_ins_nums[flows.index(flow)]
                    for i in range(ins_num):
                        if (l, t, a, f, i) in assign_flow_slot:
                            var = assign_flow_slot[l, t, a, f, i]
                            # Ensure the flow instance is assigned to the correct queue
                            solver.add(z3.Implies(var, slot_queue[l, t] == z3.Select(pcp_queue[l], flow_pcp[a, f])))
                            queue_constraints.append(slot_queue[l, t] == z3.Select(pcp_queue[l], flow_pcp[a, f]))
                # At most one flow instance can be scheduled at time t on link l
                assign_vars = [assign_flow_slot[l, t, a, f, i]
                               for flow in app_flows
                               for f in [flow["flow_id"]]
                               for i in range(flow_ins_nums[flows.index(flow)])
                               if (l, t, a, f, i) in assign_flow_slot]
                if assign_vars:
                    solver.add(z3.Sum(assign_vars) <= 1)
                    solver.add(z3.Implies(slot_queue[l, t] != 0, z3.Or(queue_constraints)))
# Constraint 3: Ensure each flow instance has slots assigned on each of its links

flow_links = {}
for flow in flows:
    flow_links[flow["app_id"], flow["flow_id"]] = flow["links"]


for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    links = flow["links"]
    ins_num = flow_ins_nums[flows.index(flow)]
    for i in range(ins_num):
        for l in links:
            assign_vars = [assign_flow_slot[l, t, a, f, i]
                           for t in range(num_timeslots)
                           if (l, t, a, f, i) in assign_flow_slot]
            # Each instance must be assigned exactly once on each link
            solver.add(z3.Sum(assign_vars) == 1)
            print(f"Link {l} has {len(assign_vars)} assignments")

# Constraint 4: Offset Constraints
for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    period = flow["period"]
    ins_num = flow_ins_nums[flows.index(flow)]
    first_link = flow["links"][0]
    for i in range(ins_num):
        # Collect timeslots where instance i is assigned on the first link
        assigned_slots = [t for t in range(num_timeslots)
                          if (first_link, t, a, f, i) in assign_flow_slot]
        # For each timeslot, if the flow instance is assigned at t, offset < t
        for t in assigned_slots:
            var = assign_flow_slot[first_link, t, a, f, i]
            solver.add(z3.Implies(var, offset[a, f][i] < t))
        # [Multiple periods] Ensure offsets are strictly increasing for instances
        if i > 0:
            ## Ideally, offset[a, f][i] == offset[a, f][i - 1] + period
            solver.add(offset[a, f][i] > offset[a, f][i - 1])

# No collision from the same source
# Collect all flow instances from the same source node
src_flow_instances = {}
for flow in flows:
    src = flow["src"]
    a = flow["app_id"]
    f = flow["flow_id"]
    ins_num = flow_ins_nums[flows.index(flow)]
    for i in range(ins_num):
        if src not in src_flow_instances:
            src_flow_instances[src] = []
        src_flow_instances[src].append((a, f, i))

# Add constraints to ensure that offsets for flow instances from the same source are not equal
for src, flow_list in src_flow_instances.items():
    for idx1 in range(len(flow_list)):
        a1, f1, i1 = flow_list[idx1]
        for idx2 in range(idx1 + 1, len(flow_list)):
            a2, f2, i2 = flow_list[idx2]
            solver.add(offset[a1, f1][i1] != offset[a2, f2][i2])


## ==== Constraint 5: Ensure flow instance ordering ======
## ==============================================

flow_link_timeslot = {}

for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    ins_num = flow_ins_nums[flows.index(flow)]
    period = flow["period"]
    links = flow["links"]
    for i in range(ins_num):
        for l in links:
            var_name = f"flow_link_timeslot_{a}_{f}_{i}_{l}"
            flow_link_timeslot[a, f, i, l] = z3.Int(var_name)
            # The timeslot must be within valid range
            solver.add(flow_link_timeslot[a, f, i, l] >= 0)
            solver.add(flow_link_timeslot[a, f, i, l] < num_timeslots)

            # Link the timeslot variable to the assign_flow_slot variables
            possible_timeslot_constraints = []
            for t in range(num_timeslots):
                if (l, t, a, f, i) in assign_flow_slot:
                    var = assign_flow_slot[l, t, a, f, i]
                    # If the flow instance is assigned at timeslot t on link l, then flow_link_timeslot equals t
                    possible_timeslot_constraints.append(z3.And(var, flow_link_timeslot[a, f, i, l] == t))
            # At least one of these assignments must be true
            # Ensure that each flow instance has a timeslot assigned on each link
            solver.add(z3.Or(possible_timeslot_constraints))

        # Ensure ordering of timeslots along the path for each instance
        for idx in range(len(links) - 1):
            l_prev = links[idx]
            l_next = links[idx + 1]
            # The timeslot on l_next must be after the timeslot on l_prev for the same instance
            solver.add(flow_link_timeslot[a, f, i, l_next] > flow_link_timeslot[a, f, i, l_prev])


### Make sure the offset order is consistent with the flow order in the first link
for src, flow_list in src_flow_instances.items():
    for idx1 in range(len(flow_list)):
        a1, f1, i1 = flow_list[idx1]
        if (a1, f1, i1, links[0]) not in flow_link_timeslot:
            continue
        for idx2 in range(idx1 + 1, len(flow_list)):
            a2, f2, i2 = flow_list[idx2]
            if (a2, f2, i2, links[0]) not in flow_link_timeslot:
                continue
            ## Add constraints that the offset order is consistent with the flow order in the first link
            solver.add(z3.Or(
                z3.And(offset[a1, f1][i1] < offset[a2, f2][i2], flow_link_timeslot[a1, f1, i1, links[0]] < flow_link_timeslot[a2, f2, i2, links[0]]),
                z3.And(offset[a1, f1][i1] > offset[a2, f2][i2], flow_link_timeslot[a1, f1, i1, links[0]] > flow_link_timeslot[a2, f2, i2, links[0]]),
            ))

### Make sure the delay from offset to last-hop link is no more than the period
for flow in flows:
    a = flow["app_id"]
    f = flow["flow_id"]
    links = flow["links"]
    solver.add(flow_link_timeslot[a, f, 0, links[-1]] - offset[a, f][0] + 1 < flow["period"])
            

# ==============================================


if solver.check() == z3.sat:
    model = solver.model()

    # Step 5: Extract and Print the Matrices

    # Flow to PCP mapping for each flow
    print("Flow to PCP mapping (flow_pcp_app_link):")
    for flow in flows:
        a = flow["app_id"]
        f = flow["flow_id"]
        pcp_value = model[flow_pcp[a, f]].as_long()
        print(f"Application {a}, Flow {f}: PCP {pcp_value}")

    print("\nPCP to Queue mapping (pcp_queue):")
    for l in links_list:
        for pcp in range(1, 8):
            queue = model.evaluate(pcp_queue[l][pcp]).as_long()
            print(f"Link {l}-{link_to_nodes[l]}: PCP {pcp}: Queue {queue}")

    # Timeslot to Queue mapping for each link
    print("\nTimeslot to Queue mapping (slot_queue):")
    for l in range(num_links):
        if l not in link_to_nodes:
            continue
        print(f"Link {l}-{link_to_nodes[l]}:")
        for t in range(num_timeslots):
            key = (t, l)
            if schedule[key] == -1:
                queue = 0
            else:
                queue = model[slot_queue[l, t]].as_long()
            print(f"  Timeslot {t}: Queue {queue}")

    # Print flow schedules along their paths
    print("\nFlow Schedules along Paths:")
    for flow in flows:
        a = flow["app_id"]
        f = flow["flow_id"]
        links = flow["links"]
        print(f"\nApp {a}, Flow {f} path:")
        for l in links:
            print(f"  Link {l}-{link_to_nodes[l]}:", end=" ")
            for i in range(flow_ins_nums[flows.index(flow)]):
                print(f"  Instance {i}:", end=" ")
                scheduled_slots = []
                scheduled_queues = []  # Add this to store queues
                for t in range(num_timeslots):
                    if (l, t, a, f, i) in assign_flow_slot and model.evaluate(assign_flow_slot[l, t, a, f, i]):
                        scheduled_slots.append(t)
                        scheduled_queues.append(model[slot_queue[l, t]].as_long())  # Get queue for this specific timeslot
                # Print both slots and their corresponding queues
                print(f"Timeslots: {scheduled_slots} Queues: {scheduled_queues}")
    
    # Print offset
    print("\nOffset:")
    minimum_offset = 0
    for flow in flows:
        a = flow["app_id"]
        f = flow["flow_id"]
        offset_value = model[offset[a, f][0]].as_long()
        if offset_value < minimum_offset:
            minimum_offset = offset_value
        print(f"Source: {flow['src']}, App {a}, Flow {f}, Instance 0: Offset {offset_value}")
    print(f"Minimum offset: {minimum_offset}")

    
    # Print delay
    # There are 2 types of delay:
    # 1. The delay between offset and the finished time
    # 2. The delay between first-hop link and the last-hop link

    print("\nDelay:")
    for flow in flows:
        a = flow["app_id"]
        f = flow["flow_id"]
        links = flow["links"]
        print(f"App {a}, Flow {f}:", end=" ")
        
        release_time = model[offset[a, f][0]].as_long()
        finish_time = 0
        for t in range(num_timeslots):
            if (links[-1], t, a, f, 0) in assign_flow_slot and model.evaluate(assign_flow_slot[links[-1], t, a, f, 0]):
                finish_time = t + 1
                break
        delay = finish_time - release_time
        print(f"e2e delay: {delay}", end=" ")

        first_link = links[0]
        last_link = links[-1]

        is_first_link_scheduled = False
        is_last_link_scheduled = False
        for t in range(num_timeslots):
            if (first_link, t, a, f, 0) in assign_flow_slot and model.evaluate(assign_flow_slot[first_link, t, a, f, 0]):
                first_link_time = t
                is_first_link_scheduled = True
                break
        for t in range(num_timeslots):
            if (last_link, t, a, f, 0) in assign_flow_slot and model.evaluate(assign_flow_slot[last_link, t, a, f, 0]):
                last_link_time = t + 1
                is_last_link_scheduled = True
                break
        if is_first_link_scheduled and is_last_link_scheduled:
            first_hop_delay = last_link_time - first_link_time
            print(f"first-hop delay: {first_hop_delay}")
        else:
            assert False, "First or last link is not scheduled"
        
else:
    print("No feasible solution found.")
