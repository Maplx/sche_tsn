import json

### Use VLAN 1 for network control messages


def load_json(ssh_info_path: str):
    with open(ssh_info_path, "r") as f:
        conf = json.load(f)
    return conf


## VLAN
# Commands run on the TTTech Evaluation Board
def vlan_add_bridge(port, vlan_id):
    # print('stucked in vlan_add_bridge')
    return f"bridge vlan add dev sw0p{port} vid {vlan_id}"


## PCP is from 0 to 7
def vlan_add_talker(vlan_id):
    # print('stucked in vlan_add_talker')
    comm = []
    comm.append(f"sudo ip link add link i210 name vlan{vlan_id} type vlan id {vlan_id}")
    comm.append(f"sudo ip addr add 192.168.{vlan_id}.1/24 dev vlan{vlan_id}")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 0:0")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 1:1")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 2:2")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 3:3")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 4:4")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 5:5")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 6:6")
    comm.append(f"sudo ip link set vlan{vlan_id} type vlan egress 7:7")
    comm.append(f"sudo ip link set vlan{vlan_id} up")

    return ";".join(comm)


def vlan_add_listener(vlan_id):
    # print('stucked in vlan_add_listener')
    comm = []
    comm.append(f"sudo ip link add link i210 name vlan{vlan_id} type vlan id {vlan_id}")
    comm.append(f"sudo ip addr add 192.168.{vlan_id}.2/24 dev vlan{vlan_id}")
    comm.append(f"sudo ip link set vlan{vlan_id} up")
    return ";".join(comm)


def delete_all_vlan_es():
    comm = "for i in {0..255}; do ip link show vlan$i > /dev/null 2>&1 && sudo ip link delete vlan$i; done"
    return comm


def delete_all_vlan_sw():
    comm = "for dev in {2..5}; do bridge vlan del dev sw0p${dev} vid 2-255; done"
    return comm


## MSTP
def add_tree(tree_id):
    """
    The tree_id is same as VLAN id here
    """
    comm = """
    mstpctl createtree br0 {tree_id}
    """
    return comm.format(tree_id=tree_id)


def add_vid2fid_map(vid2fid):
    """
    Recommand use same vid and fid
    """
    comm = "mstpctl setvid2fid br0"
    for fid, vid_list in vid2fid.items():
        for vid in vid_list:
            comm += " " + f"{fid}:{vid}"

    return comm


def add_fid2mstid_map(fid2mstid):
    """
    Recommand use same fid and mstid
    """
    comm = "mstpctl setfid2mstid br0"
    for mstid, fid_list in fid2mstid.items():
        for fid in fid_list:
            comm += " " + f"{mstid}:{fid}"
    return comm


def assign_mstp_root(tree_id):
    comm = f"mstpctl settreeprio br0 {tree_id} 0"
    return comm


def add_pcp2queue_map(pcp, queue, port):
    """
    use same fid and mstid
    """
    assert pcp >= 1
    comm = "tsntool brport wrtctbl {pcp} {queue} sw0p{port}"


    return comm.format(pcp=pcp, queue=queue, port=port)


def reset_pcp2queue_map(port):
    """
    Recommend use same fid and mstid
    """
    comm = []
    comm.append(f"tsntool brport wrtctbl 0 0 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 1 1 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 2 2 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 3 3 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 4 4 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 5 5 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 6 6 sw0p{port}")
    comm.append(f"tsntool brport wrtctbl 7 7 sw0p{port}")
    return ";".join(comm)


def set_mstid(mstid="cy", level="1"):
    comm = f"mstpctl setmstconfid br0 {level} {mstid}"
    return comm


def set_tree_port_cost(port, tree, cost):
    """port should be sw0pX"""
    comm = f"mstpctl settreeportcost br0 sw0p{port} {tree} {cost}"
    return comm


def reset_vid2fid_map():
    """
    Recommand use same vid and fid
    """
    comm = "mstpctl setvid2fid br0 0:2-255"
    return comm


def reset_fid2mstid_map():
    """
    Recommand use same fid and mstid
    """
    comm = "mstpctl setfid2mstid br0 0:2-255"
    return comm


def delete_tree(tree_id):
    """
    Make sure use `dd_fid2mstid_map(fid, 0)` to unallocate the fid
    """
    comm = "mstpctl deletetree br0 {tree_id}"
    return comm.format(tree_id=tree_id)


def hex(x):
    return format(x, "#04x")


def gcl_to_cfg(gcl: list, cycle):
    """
    gcl: list of tuple (queue, start, end)

    e.g.

    sgs 800 0x08
    sgs 12000 0xF7
    """

    comm = []
    gcl = sorted(gcl, key=lambda x: x[1])
    # GCL_TIME_ERROR = 1920 ## 1920 = ceil(204 * 8 / 320)
    GCL_TIME_ERROR = 0
    current_time = 0

    for queue, start, end in gcl:
        queue = str(hex(0x00 + 2**queue))
        if start == current_time:
            comm.append(f"sgs {end - start} {queue}")
        else:
            if start - current_time > 0:
                comm.append(f"sgs {start - current_time} {hex(0x01 + 0x02)}")
            comm.append(f"sgs {end - start + GCL_TIME_ERROR} {queue}")
        current_time = end + GCL_TIME_ERROR
    if current_time < cycle:
        comm.append(f"sgs {cycle - current_time} {hex(0xff)}")

    # assert sum([eval(x.split()[1])
    #             for x in comm]) == cycle, "GCL is not correct"

    ### Make the last window size 12800
    # comm[-1] = " ".join([comm[-1].split()[0], "12800", comm[-1].split()[2]])

    return "\n".join(comm)


def reset_gcl(port):
    comm = "tsntool st reset sw0p{port}"
    return comm.format(port=port)


def apply_gcl(sw_id, port):
    comm = "tsntool st wrcl sw0p{port} sw{sw:02d}_{port}.cfg"
    return comm.format(port=port, sw=sw_id)


def start_tas(port, cycle, sec, nsec):
    cycle_sec = 1_000_000_000 // cycle
    comm = "tsntool st configure {sec}.{nsec:09d} 1/{cycle_sec} 0 sw0p{port}"
    return comm.format(sec=sec, nsec=nsec, cycle_sec=cycle_sec, port=port)


def disable_ntp():
    comm = "sudo systemctl stop systemd-timesyncd; sudo systemctl stop ntp"
    return comm


def start_phy2sys(interface):
    comm = (
        "nohup sudo phc2sys -s {interface} -c CLOCK_REALTIME -m -O 0 > ./phc.log 2>&1 &"
    )
    return comm.format(interface=interface)


def start_ptp4l(interface):
    comm = "nohup sudo ptp4l -i {interface} -f /home/ubuntu/code/RPiTSN/config/gptp.cfg -m > ./ptp.log 2>&1 &"
    return comm.format(interface=interface)


def end_sync():
    comm = "sudo killall -9 phc2sys; sudo killall -9 ptp4l"
    return comm


def reset_qdisc(interface):
    comm = "sudo tc qdisc del dev {interface} root"
    return comm.format(interface=interface)


def config_qdisc(interface, offset):
    """
    Qdisc can only be applied on the main interface, not the vlan interface
    """
    # comm = "sudo bash /home/ubuntu/code/RPiTSN/config/config_qdisc.sh -d {interface} -o {offset}"
    comm = []
    comm.append(
        f"sudo tc qdisc add dev {interface} parent root handle 6666 mqprio num_tc 2 map 0 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 queues 1@0 1@1 hw 0"
    )
    comm.append(
        f"sudo tc qdisc add dev {interface} parent 6666:2 etf clockid CLOCK_TAI delta {offset} offload"
    )
    return ";".join(comm)


def start_client(expid, idd, interface, port, ip, period, size, sec, nsec, pcp):
    comm = "nohup sudo /home/ubuntu/code/RPiTSN/src/client -i {interface} -d {ip} -p {port} -k {pcp} -t {period} -l {size} -b {sec}.{nsec} -v -w > client{idd}_{expid}.log 2>&1 &"
    print(
        comm.format(
            idd=idd,
            pcp=pcp,
            interface=interface,
            ip=ip,
            port=port,
            period=period,
            size=size,
            sec=sec,
            nsec=nsec,
            expid=expid,
        )
    )
    return comm.format(
        idd=idd,
        pcp=pcp,
        interface=interface,
        ip=ip,
        port=port,
        period=period,
        size=size,
        sec=sec,
        nsec=nsec,
        expid=expid,
    ) 



def terminate_client():
    comm = """
    sudo killall -9 client
    """
    return comm


def clean_logs():
    comm = """
    sudo rm *.log
    """
    return comm


def start_server(
    expid,
    idd,
    interface,
    port,
):
    comm = """
    nohup sudo /home/ubuntu/code/RPiTSN/src/server -i {interface} -p {port} -r > server{idd}_{expid}.log 2>&1 &
    """
    print(comm.format(idd=idd, interface=interface, port=port, expid=expid))
    return comm.format(idd=idd, interface=interface, port=port, expid=expid)


def terminate_server():
    comm = """
    sudo killall -9 server
    """
    return comm


def nafor(iterable):
    """
    Filter out None values from an iterable.
    Usage: for item in nafor(items): ...
    
    Args:
        iterable: Any iterable object (list, tuple, etc.)
        
    Returns:
        Generator that yields non-None values
    """
    return (x for x in iterable if x is not None)


def start_multiple_clients(client_configs):
    """
    Starts multiple clients in parallel
    
    Args:
        client_configs: list of dicts containing client parameters
    """
    commands = []
    for config in client_configs:
        cmd = ("nohup sudo /home/ubuntu/code/RPiTSN/src/client "
               f"-i {config['interface']} -d {config['ip']} -p {config['port']} "
               f"-k {config['pcp']} -t {config['period']} -l {config['size']} "
               f"-b {config['sec']}.{config['nsec']} -v -w "
               f"> client{config['idd']}_{config['expid']}.log 2>&1 & ")
        commands.append(cmd)
    
    print(" ".join(commands))
    return " ".join(commands)


def start_multiple_servers(server_configs):
    commands = []
    for config in server_configs:
        cmd = f"nohup sudo /home/ubuntu/code/RPiTSN/src/server -i {config['interface']} -p {config['port']} -r > server{config['idd']}_{config['expid']}.log 2>&1 &"
        commands.append(cmd)
    print(" ".join(commands))
    return " ".join(commands)


def check_vlan_connectivity(src_entity, dst_entity, vlan_id, pcp):
    src_ip = f"192.168.{vlan_id}.1"
    dst_ip = f"192.168.{vlan_id}.2"
    
    # Send ping from source to destination with specific PCP
    ping_cmd = f"ping -c 4 -Q {pcp} {dst_ip}"
    output = src_entity.exec_command(ping_cmd)
    
    if "4 packets transmitted, 4 received" in output:
        print(f"VLAN {vlan_id} PCP {pcp} connectivity between {src_entity.name} and {dst_entity.name}: PASS")
    else:
        print(f"VLAN {vlan_id} PCP {pcp} connectivity between {src_entity.name} and {dst_entity.name}: FAIL")

def check_all_vlan_connectivity(controller):
    for flow in controller.cnc.Flows:
        src_entity = controller.cnc.Entities[flow.src] 
        dst_entity = controller.cnc.Entities[flow.dst]
        vlan_id = flow.id + 2
        pcp = flow.PCP
        
        check_vlan_connectivity(src_entity, dst_entity, vlan_id, pcp)

def test_vlan_connectivity(src_ip, dst_ip, vlan_id, pcp, iface="i210"):
    """
    Test VLAN connectivity using testcon.py script
    """
    comm = f"sudo python3 /home/ubuntu/testcon.py -d {dst_ip} -v {vlan_id} -p {pcp} -i {iface}"
    return comm

if __name__ == "__main__":
    # print(add_tree(2))
    # print(add_vid2fid_map({1: [2], 2: [3]}))
    # print(add_fid2mstid_map({1: [2], 2: [3]}))

    ## Print and test the client and server command
    # print(start_gcl(2, 1_000_000, 1521126347, 0))
    # print(start_client(0, "vlan5", 10009, "192.168.9.2", 1000000, 100, 1521128300))
    # print(start_server(0, "vlan5", 10009))
    # start_server()

    ## Unit test for gcl_to_cfg
    print(gcl_to_cfg([(0, 0, 1000000), (1, 1000000, 2000000), (2, 2000000, 3000000)], 3000000))
