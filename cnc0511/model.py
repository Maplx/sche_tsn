import pandas as pd
import glob
import os
from tools import *


class Flow:

    def __init__(self) -> None:
        self.id = None
        self.PCP = None
        self.offset = None
        self.path = []
        self.queue = {}

        self.src = None
        self.dst = None
        self.period = None
        self.size = None
        self.deadline = None

    def get_prev_link(self, link):
        assert link in self.path
        assert self.path.index(link) > 0
        return self.path[self.path.index(link) - 1]

    def get_next_link(self, link):
        assert link in self.path
        assert self.path.index(link) < len(self.path) - 1
        return self.path[self.path.index(link) + 1]


class Entity:

    def __init__(self) -> None:
        self.id = None
        self.name = None
        self.links = {}  # {str(start, end): Link}
        self.egress_ports = {}  # {int(port): str(start, end)}
        self.ingress_ports = {}  # {str(start, end): int(port)}


class Link:

    def __init__(self) -> None:
        self.start = None
        self.end = None

        self.e_port = None
        self.s_port = None

        self.GCL = []
        self.cycle = None

        self.active = False
        self.flows = []


class CNC:

    def __init__(self) -> None:
        self.Entities = []
        self._entity_set = set()
        self.Flows = []
        self._flow_set = set()

        self.cycle = None
        self.reserved_queue = 0

    def __del__(self) -> None:
        pass

    def init_topo(self, topology_file='conf.json'):
        conf = load_json(topology_file)
        for entity_name, entity_conf in conf.items():
            entity = Entity()
            entity.name = entity_name
            entity.id = int(entity_name[-2:])
            for port, end in entity_conf['links'].items():
                link = Link()
                link.start = entity.id
                link.end = int(end[-2:])
                link.e_port = int(port[-1])

                link_id = f"({link.start}, {link.end})"
                entity.egress_ports[int(port[-1])] = link_id
                entity.links[link_id] = link

            while entity.id >= len(self.Entities):
                self.Entities.append(None)
            self.Entities[entity.id] = entity
            self._entity_set.add(entity.id)
        
        ## Add the s_port: s_port
        for entity in self.Entities:
            if entity is None:
                continue
            for link_id, link in entity.links.items():
                dst_entity = self.Entities[link.end]
                if 'sw' in dst_entity.name:
                    for e_port, e_link_id in dst_entity.egress_ports.items():
                        if e_link_id == reverse_link_id(link_id):
                            link.s_port = e_port
                            self.Entities[
                                link.end].ingress_ports[link_id] = link.s_port

    def assign_flows(self, flow_path, offset_path, queue_path, route_path, pcp_path=None):
        flows = pd.read_csv(flow_path)
        queue = pd.read_csv(queue_path)
        offset = pd.read_csv(offset_path)
        path = pd.read_csv(route_path)

        if pcp_path:
            pcp = pd.read_csv(pcp_path)
            self.is_pcp_assigned = True
            print("[Info] PCP is assigned by input file")
        else:
            self.is_pcp_assigned = False
            print("[Info] PCP is assigned by default")

        for _, row in flows.iterrows():
            flow = Flow()
            flow.id = row['id']
            flow.PCP = pcp.loc[flow.id, 'pcp'] if pcp_path else None
            flow.src = row['src']
            flow.dst = eval(row['dst'])[0]
            flow.period = row['period']
            flow.size = row['size']
            flow.deadline = row['deadline']

            self.Flows.append(flow)
            self._flow_set.add(flow.id)

        for _, row in queue.iterrows():
            link = row['link']
            if not self.link_exists(link):
                raise ValueError(f"Link {link} does not exist in the topology.")
            self.Flows[row['stream']].queue[link] = row['queue'] + self.reserved_queue
            self.Flows[row['stream']].path.append(link)

        for _, row in offset.iterrows():
            self.Flows[row['stream']].offset = row['offset']

        _link_to_flows = {}
        for _, row in path.iterrows():
            _link_to_flows.setdefault(row['link'], [])
            _link_to_flows[row['link']].append(row['stream'])

        for entity in nafor(self.Entities):
            for link_id in entity.links.keys():
                if link_id in _link_to_flows:
                    ## Add flow to link
                    entity.links[link_id].active = True
                    entity.links[link_id].flows = _link_to_flows[link_id]

        # ## Check if the flows are all in the link
        # for entity in self.Entities:
        #     for link_id, link in entity.links.items():
        #         if len(link.flows) > 0:
        #             print(link_id, link.flows)

        ## Print the route of all streams
        for i in range(len(self.Flows)):
            # print(flow.id, self.sort_path(flow.path, flow.src, flow.dst))
            self.Flows[i].path = self.sort_path(self.Flows[i].path,
                                                self.Flows[i].src,
                                                self.Flows[i].dst)
    

    def sort_path(self, lst, start, end):
        # Convert the list of string tuples to a list of integer tuples
        tuple_list = [eval(item) for item in lst]

        # Create a dictionary to store outgoing edges for each node
        graph = {}
        for a, b in tuple_list:
            graph[a] = b

        # Start from node 8
        current_node = start
        sorted_path = []

        # Traverse the path until we reach node 9
        while current_node != end:
            next_node = graph[current_node]
            sorted_path.append(f'({current_node}, {next_node})')
            current_node = next_node

        return sorted_path

    def assign_GCL(self, gcl_path):
        gcl = pd.read_csv(gcl_path)
        cycle = gcl['cycle'].unique()[0]

        for _, row in gcl.iterrows():
            link = row['link']
            start = eval(link)[0]
            end = eval(link)[1]
            self.Entities[start].links[link].GCL.append(
                [row['queue'] + self.reserved_queue, row['start'], row['end']])
            if self.Entities[start].links[link].cycle is None:
                self.Entities[start].links[link].cycle = cycle
                if self.cycle is None:
                    self.cycle = cycle
                elif self.cycle != cycle:
                    raise ValueError(f"[Warning] Cycle mismatch: {self.cycle} and {cycle}")
                

        ## Assert if cycle is None for any active link
        ## Active: link has flows
        for entity in nafor(self.Entities):
            for link_id, link in entity.links.items():
                if link.active and link.cycle is None:
                    print(f"[Warning] GCL is not assigned for active link {link_id}")

    def link_exists(self, link):
        start, end = eval(link)
        for entity in self.Entities:
            if entity is None:
                continue
            if entity.id == start:
                return link in entity.links
        return False


def reverse_link_id(link_id):
    start = eval(link_id)[0]
    end = eval(link_id)[1]
    return f"({end}, {start})"


if __name__ == '__main__':
    ## Test for reserve path function
    cnc = CNC()
    cnc.init_topo()
    cnc.assign_flows('offset.csv', 'queue.csv', 'route.csv')
    cnc.assign_GCL('gcl.csv')

    # for entity in cnc.Entities:
    #     for link_id, link in entity.links.items():
    #         for flow in link.flows:
    #             flow_ins = cnc.Flows[flow]
    #             print(link_id, flow_ins.id, flow_ins.PCP, flow_ins.queue)
