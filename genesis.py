#!/usr/bin/env python3

""" 
Main script for the framework
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import  sys, traceback, json, os, argparse, logging, shutil, time, subprocess, socket, auxiliar, threading, requests, pickle, struct

from classes import iosocket

from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, NodeOptions
from core.emulator.enumerations import NodeTypes, EventTypes
from core.location.mobility import BasicRangeModel
from core import constants
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode

from core.emane.ieee80211abg import EmaneIeee80211abgModel
from core.emane.nodes import EmaneNet

class Runner():

  def __init__(self, 
               application,         # Which application will run
               network,             # Which transport to use
               membership,          # Which membership algorithm
               time_scale,          # Changes time scale to make application run faster
               time_limit,          # Simulation limit
               number_of_nodes,     # Total number of nodes
               omnet,               # Run omnet simulator?
               core,                # Run CORE emulator?
               disks,               # Create virtual disks?
               dump,                # Use TCP Dump?
               start_delay,         # How long to wait starting application
               fault_detector,
               topology,
               omnet_settings):
    """
    Runner class
    """
    self.application = application
    self.network = network
    self.membership = membership
    self.topology = topology
    self.fault_detector = fault_detector
    self.time_scale = time_scale
    self.time_limit = time_limit
    self.number_of_nodes = number_of_nodes
    self.nodes_to_start = list(range(self.number_of_nodes))
    self.omnet = omnet
    self.core = core
    self.disks = disks
    self.dump = dump
    self.start_delay = start_delay
    self.omnet_settings = omnet_settings
    self.nodes_digest = {}
    self.iosocket_semaphore = False

  def core_topology(self):
    """
    Defines and instantiate a CORE emulation session
    """
    os.system("core-cleanup")
    radius = 120
    self.nodes = []
    topology_file = open("./topologies/" + self.topology + ".json","r").read()
    topology = json.loads(topology_file)
    topo_from_file = []
    for node in topology:
      topo_from_file.append([int(node['x']), int(node['y'])])
      #print("x:" + str(int(node['x'])) + " y:" + str(int(node['y'])))
    # ip generator for example
    prefixes = IpPrefixes("10.0.0.0/24")

    # create emulator instance for creating sessions and utility methods
    self.coreemu = CoreEmu()
    self.session = self.coreemu.create_session()

    # location information is required to be set for emane
    #self.session.location.setrefgeo(47.57917, -122.13232, 2.0)
    #self.session.location.refscale = 150.0

    # must be in configuration state for nodes to start, when using "node_add" below
    self.session.set_state(EventTypes.CONFIGURATION_STATE)
    # create wlan network node

    node_options=[]
    for i in range(0,self.number_of_nodes):
        node_options.append(NodeOptions(name='drone'+str(i)))
    symm = [[150,50 ],
            [250,50 ],
            [150,150],
            [250,150],
            [350,250],
            [250,250],
            [350,50 ],
            [150,250],
            [350,150],
            [652,300],
            [451,302],
            [726,400],
            [651,464],
            [729,466],
            [651,126],
            [728,124],
            [729,198],
            [451,128],
            [376,129],
            [377,200],
            [371,401],
            [452,472],
            [371,473],
            [551,200],
            [550,400],
            [804,501],
            [802,98 ],
            [302,100],
            [302,502]]

    star = [[417,218], #node0
            [307,258], #node1
            [514,283], #node2
            [338,131], #node3
            [496,129], #node4
            [403,333]] #node5
      
    topo = topo_from_file
    for i in range(0,self.number_of_nodes):
      node_options[i].set_position(topo[i][0],topo[i][1])

    for node_opt in node_options:
      self.nodes.append(self.session.add_node(CoreNode, options=node_opt))
    
    options = NodeOptions(x=200, y=200)
    #options = NodeOptions(x=200, y=200, emane=EmaneIeee80211abgModel.name)
    #wlan = session.add_node(EmaneNet, options=options)
    self.wlan = self.session.add_node(WlanNode,options=options )
    #wlan = session.add_node(_type=NodeTypes.WIRELESS_LAN)
    # configure general emane settings
    #config = session.emane.get_configs()
    #config.update({"eventservicettl": "2"})
    # configure emane model settings
    # using a dict mapping currently support values as strings
    #session.emane.set_model_config(wlan.id, EmaneIeee80211abgModel.name, {"unicastrate": "3"})
    self.modelname = BasicRangeModel.name
    self.session.mobility.set_model_config(self.wlan.id, BasicRangeModel.name,
        {
            "range": radius,
            "bandwidth": "433300000",
            "delay": "300",
            "jitter": "0",
            "error": "0",
        },
    )

    for node in self.nodes:
      interface = prefixes.create_iface(node)
      self.session.add_link(node.id, self.wlan.id, iface1_data=interface)
    self.session.instantiate()

  def server_thread(self):
    'Starts a thread with the Socket.io instance that will serve the HMI'
    self.iosocket = iosocket.Socket(self.nodes, self.wlan, self.session, self.modelname, self.nodes_digest, self.iosocket_semaphore, self)

  def start(self):
    'Start the emulation'
    self.Bus = Bus()
    self.Bus.start()
    self.Bus.register_cb(self.bus_callback)
    self.run()

  def bus_callback(self, data):
    data = pickle.loads(data)
    try:
      if data[0] == 'BROADCAST':
        if data[1] == 'POSITION':
          for node in self.nodes:
            if data[2][0] == node.id:
              node.setposition(data[2][1], data[2][2])
        elif data[1] == 'LEADER':
          self.nodes_digest['leader'] = data[2]
          self.iosocket_semaphore = True
    except:
      pass

  def run(self):
    'Runs each component of the simulation OMNet or CORE, configures BATMAN in each node, and launches the application'

    #start omnet
    if self.omnet:
      OMNet = self.omnet_run(self.omnet_settings)
      logging.info("Started OMNet++ with PID: " + str(OMNet.pid))    
    
    #start core
    if self.core:
      self.core_topology()
      self.configure_batman()
      self.createNodesCore()
      #self.core_terminal()

    #create disks
    if self.disks:
      self.createDisks(self.number_of_nodes)

    #get simdir
    simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)

    #create nodes
    if self.omnet:
      self.createNodes(self.number_of_nodes, self.application, self.network)

    #wait for nodes to start and create socket. This is only needed for slow computers.
    backoff = 0
    started = False
    time.sleep(1)
    starting_time = time.time() + self.start_delay
    while (len(self.nodes_to_start) > 0):
      time.sleep(backoff) 
      try:
        #firing up the nodes
        self.startNodes(starting_time)
      except SystemExit:
        os.system("sudo killall xterm")
        sys.exit(1)
      except:
        logging.info("Too fast... backing off: " + str(backoff))
        backoff += 0.2

    #start dumps
    if self.dump:
      #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.omnet:
        self.tcpdump(self.number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.core:
        self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    #this keeps the script on a lock until all nodes had finished.
    path ="./reports/" + simdir + "/finished"
    logging.info("Checking for nodes finished in: " + path)
    Aux = auxiliar.Auxiliar(path, self.number_of_nodes)
    lock=True
    if self.core:
      #pass
      sthread = threading.Thread(target=self.server_thread, args=())
      sthread.start()
    while lock==True:
      lock = Aux.check_finished()
      time.sleep(1)

    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      try:
        r = requests.get('http://localhost:5000/sim/stop')
        print(r)
        self.iosocket.shutdown()
      except:
        pass
      self.coreemu.shutdown()
    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def omnet_run(self, settings):
    #this opens a terminal windows with omnet running
    omnet = subprocess.Popen([
                  "xterm",
                  "-hold",
                  "-e",
                  "taskset -c 1 inet -u Cmdenv -n " + settings['omnet_include_path'] + " " + settings['ini_file']]
                  , stdin=subprocess.PIPE, shell=False)
    return omnet

  def terminal(self, args):
    #open extra terminal windows in each node
    for i in range(0,args.numberOfNodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T client" + str(i) + " &"
      node = subprocess.Popen([
                    "ip",
                    "netns",
                    "exec",
                    "drone" + str(i),
                    "bash",
                    "-c",
                    command])

  def core_terminal(self):
    #open extra terminal windows in each node
    for i in range(0,self.number_of_nodes):
      shell = self.session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      #print(shell)
      #command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T client" + str(i) + " -e " + shell + " &"
      #print(command)
      try:
        node = subprocess.Popen([
            "xterm",
            #"-xrm 'XTerm.vt100.allowTitleOps: false'",
            "-hold",
            #"-T drone" + str(i),
            "-e",
            shell]
            , stdin=subprocess.PIPE, shell=False)
        #node = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)
      except:
        traceback.print_exc()
        pass

  def createDisks(self, number_of_nodes):
    #create virtual disk for each node
    #os.system("for i in {0..10}; do umount /mnt/genesis/drone$i; done")
    #os.system("for i in {0..10}; do rm -rf /mnt/genesis/drone$i; done")
    #os.system("for i in {0..10}; do mkdir /mnt/genesis/drone$i; done")
    for i in range(0,number_of_nodes):
      command = "mount -t tmpfs -o size=512m tmpfs /mnt/genesis/drone" + str(i) + " &"
      node = subprocess.Popen([
                    "bash",
                    "-c",
                    command])

  def createNodes(self, number_of_nodes, application, network):
    #creates a terminal window for each node running the main application
    process = []
    for i in range(0,number_of_nodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i) 
      command += " -hold -e ./main.py drone"+ str(i) + " " + self.application + " " 
      command += str(self.time_scale) + " " + str(self.time_limit) + " random_walk -p " 
      command += self.network  + " ipv4 -b 100 -r node"
      command += " -m " + self.membership
      command += " -f " + self.fault_detector + " &"
      node = subprocess.Popen([
                    "ip",
                    "netns",
                    "exec",
                    "drone" + str(i),
                    "bash",
                    "-c",
                    command])
      process.append(node)

  def configure_batman(self):
    process = []
    for i in range(0,self.number_of_nodes):
      shell = self.session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      #command = "ip link set eth0 address 0A:AA:00:00:00:" + '{:02x}'.format(i+2) +  " && batctl if add eth0 && ip link set up bat0 && ip addr add 10.0.1." +str(i+2) + "/255.255.255.0 broadcast 10.0.1.255 dev bat0"
      command = "modprobe batman-adv && batctl ra BATMAN_IV && batctl if add eth0 && ip link set up bat0 && ip addr add 10.0.1." +str(i+1) + "/255.255.255.0 broadcast 10.0.1.255 dev bat0"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                    "xterm",
                    "-e",
                    shell], stdin=subprocess.PIPE, shell=False)
      process.append(node)
  
  def createNodesCore(self):
    #creates a terminal window for each node running the main application
    process = []
    for i in range(0,self.number_of_nodes):
      shell = self.session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = "export PYTHONPATH=/home/bruno/Documents/bruno-onera-enac-doctorate/software/pprzlink/lib/v2.0/python && "
      command += "cd /home/bruno/Documents/bruno-onera-enac-doctorate/software/genesis && "
      command += "./main.py drone"+ str(i) + " " + self.application + " " 
      command += str(self.time_scale) + " " + str(self.time_limit) + " random_walk -p " 
      command += self.network  + " ipv4 -b 100 -r node"
      command += " -m " + self.membership
      command += " -f " + self.fault_detector
      shell += " -c '" + command + "'"
      #print(shell)
      node = subprocess.Popen([
                    "xterm",
                    "-hold",
                    "-e",
                    shell], stdin=subprocess.PIPE, shell=False)
                    #"-c",
                    #"mc"
      process.append(node)

  def startNodes(self, time_to_start):
    # Start each node application trying to create an ilusion that they are in sync
    # They receive a time when they should start, so it that they start very close to eachother
    for node in self.nodes_to_start:
      s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      s.connect("/tmp/genesis.sock.drone"+str(node))
      s.send(str(time_to_start).encode())
      data = s.recv(10)
      s.close()
      if (data.decode() == "OK"):
        #print("Got ok from:" + str(node))
        self.nodes_to_start.remove(node)
      elif (data.decode() == "NOK"):
        logging.error("Too fast for this computer, please increase the start_delay in this script")
        sys.exit(1)
      #print(nodes_to_start)

  def createDumps(self, number_of_nodes,dir):
    #create tshark dumps
    for i in range(0,number_of_nodes):
      command = "tshark -a duration:" + str(self.time_limit) + " -i bat0 -w "+ dir +"/drone" + str(i) + ".pcap &"
      node = subprocess.Popen([
                    "ip",
                    "netns",
                    "exec",
                    "drone" + str(i),
                    "bash",
                    "-c",
                    command])

  def tcpdump(self, number_of_nodes,dir):
    #create tcpdumps
    for i in range(0,number_of_nodes):
      command = "timeout " + str(self.time_limit) + " tcpdump -i tap" + str(i) + " -w "+ dir +"/drone" + str(i) + ".pcap &"
      node = subprocess.Popen([
                    "ip",
                    "netns",
                    "exec",
                    "drone" + str(i),
                    "bash",
                    "-c",
                    command])

  def tcpdump_core(self, number_of_nodes,dir):
    #create core tcpdumps
    for i in range(0,number_of_nodes):
      shell = self.session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = "cd /home/bruno/Documents/bruno-onera-enac-doctorate/software/genesis && "
      command += "timeout " + str(self.time_limit) + " tcpdump -i eth0 -w "+ dir +"/drone" + str(i) + ".pcap"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
            "xterm",
            "-hold",
            "-e",
            shell]
            ,stdin=subprocess.PIPE, shell=False)

class ETCDRunner(Runner):

  def __init__(self, 
               number_of_nodes,     # Total number of nodes
               omnet,               # Run omnet simulator?
               core,                # Run CORE emulator?
               disks,               # Create virtual disks?
               dump,                # Use TCP Dump?
               topology,
               omnet_settings):
    self.number_of_nodes = number_of_nodes
    self.omnet = omnet
    self.core = core
    self.disks = disks
    self.dump = dump
    self.omnet_settings = omnet_settings
    self.nodes_digest = {}
    self.topology = topology
    self.iosocket_semaphore = False

  def start(self):
    self.run()

  def run(self):
    'Runs each component of the simulation OMNet or CORE, configures BATMAN in each node, and launches the application'

    #start omnet
    if self.omnet:
      OMNet = self.omnet_run(self.omnet_settings)
      logging.info("Started OMNet++ with PID: " + str(OMNet.pid))    
    
    #start core
    if self.core:
      self.core_topology()
      self.configure_batman()

    #create disks
    if self.disks:
      self.createDisks(self.number_of_nodes)

    #start dumps
    if self.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.omnet:
        self.tcpdump(self.number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.core:
        self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    if self.core:
      #pass
      sthread = threading.Thread(target=self.server_thread, args=())
      sthread.start()

    if self.omnet:
      etcd_nodes = self.spawnEtcdOmnet(self.session, self.number_of_nodes)
    elif self.core:
      etcd_nodes = self.spawnEtcdCore(self.session, self.number_of_nodes)
    #self._auto_job(self.number_of_nodes)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def spawnEtcdCore(self, session, number_of_nodes):
    print("starting ETCD CORE")
    nodes = {}
    cluster = "--initial-cluster "
    for i in range(0,number_of_nodes-1):
      cluster+= "node" + str(i) + "=http://10.0.1."+str(i+1)+":2380,"
    cluster+= "node" + str(number_of_nodes-1) + "=http://10.0.1."+str(number_of_nodes)+":2380 "
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = "/opt/etcd/etcd --data-dir=/mnt/genesis/drone" + str(i) + " --name node" + str(i)
      command += " --initial-advertise-peer-urls http://10.0.1." + str(i+1) + ":2380 "
      command += "--listen-peer-urls http://10.0.1." + str(i+1) + ":2380 "
      command += "--advertise-client-urls http://10.0.1." + str(i+1) + ":2379 "
      command += "--listen-client-urls http://10.0.1." + str(i+1) + ":2379,http://127.0.0.1:2379 "
      command += cluster
      command += "--initial-cluster-state new "
      command += "--initial-cluster-token token-01"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      #"-xrm 'XTerm.vt100.allowTitleOps: false' -title drone" + str(i),
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes

  def spawnEtcdOmnet(self, number_of_nodes):
    nodes = {}
    cluster = "--initial-cluster "
    for i in range(0,number_of_nodes-1):
      cluster+= "node" + str(i) + "=http://10.0.1."+str(i+2)+":2380,"
    cluster+= "node" + str(number_of_nodes-1) + "=http://10.0.1."+str(number_of_nodes+1)+":2380 "
    for i in range(0,number_of_nodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i)
      command += " -hold -e /opt/etcd/etcd --data-dir=/mnt/etcd/node" + str(i) + " --name node" + str(i)
      command += " --initial-advertise-peer-urls http://10.0.1." + str(i+2) + ":2380 "
      command += "--listen-peer-urls http://10.0.1." + str(i+2) + ":2380 "
      command += "--advertise-client-urls http://10.0.1." + str(i+2) + ":2379 "
      command += "--listen-client-urls http://10.0.1." + str(i+2) + ":2379,http://127.0.0.1:2379 "
      command += cluster
      command += "--initial-cluster-state new "
      command += "--initial-cluster-token token-01"
      #print(command)
      #print()
      node = subprocess.Popen([
                          "ip",
                          "netns",
                          "exec",
                          "drone" + str(i),
                          "bash",
                          "-c",
                          command])
      nodes["drone" + str(i)] = node
    return nodes

class TERMRunner(Runner):

  def __init__(self, 
               number_of_nodes,     # Total number of nodes
               omnet,               # Run omnet simulator?
               core,                # Run CORE emulator?
               disks,               # Create virtual disks?
               dump,                # Use TCP Dump?
               topology,
               omnet_settings):
    self.number_of_nodes = number_of_nodes
    self.omnet = omnet
    self.core = core
    self.disks = disks
    self.dump = dump
    self.omnet_settings = omnet_settings
    self.nodes_digest = {}
    self.topology = topology
    self.iosocket_semaphore = False

  def start(self):
    self.run()

  def run(self):
    'Runs each component of the simulation OMNet or CORE, configures BATMAN in each node, and launches the application'

    #start omnet
    if self.omnet:
      OMNet = self.omnet_run(self.omnet_settings)
      logging.info("Started OMNet++ with PID: " + str(OMNet.pid))    
    
    #start core
    if self.core:
      self.core_topology()
      self.configure_batman()

    #create disks
    if self.disks:
      self.createDisks(self.number_of_nodes)

    #start dumps
    if self.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.omnet:
        self.tcpdump(self.number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.core:
        self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    if self.core:
      #pass
      sthread = threading.Thread(target=self.server_thread, args=())
      sthread.start()

    if self.omnet:
      terminals = self.spawnTerminalOmnet(self.number_of_nodes)
    elif self.core:
      terminals = self.spawnTerminalCore(self.session, self.number_of_nodes)
    #self._auto_job(self.number_of_nodes)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def spawnTerminalCore(self, session, number_of_nodes):
    print("Starting Terminals in CORE")
    nodes = {}
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = ""
      #shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      #"-xrm 'XTerm.vt100.allowTitleOps: false' -title drone" + str(i),
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes

  def spawnTerminalOmnet(self, number_of_nodes):
    nodes = {}
    for i in range(0,number_of_nodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i)
      command += " -hold"
      #print()
      node = subprocess.Popen([
                          "ip",
                          "netns",
                          "exec",
                          "drone" + str(i),
                          "bash",
                          "-c",
                          command])
      nodes["drone" + str(i)] = node
    return nodes

class Bus():

  def __init__(self):
    'Initializes the properties of the object'
    #### UTILITIES ############################################################################
    self.callbacks = []
    ##################### END OF DEFAULT SETTINGS ###########################################################

  ############### Public methods ###########################

  def start(self):
    self.state = 'ENABLED'
    self.bus_listener_thread = threading.Thread(target=self._start_event_listener, args=())
    self.bus_listener_thread.start()
    #self._start_event_listener()

  def shutdown(self):
    self._stop()
    self.bus_listener_thread.join(timeout = 2)

  def emmit(self, data):
    bus = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bus.settimeout(1)
    bus.connect("/tmp/genesis_main.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    bus.sendall(struct.pack('!I', length))
    bus.sendall(payload)
    bus.close()

  def register_cb(self, callback):
    self.callbacks.append(callback)
  
  def deregister_cb(self, callback):
    pass

  ############### Private methods ##########################
  def _stop(self):
    self.state = 'DISABLED'
    self.emmit('BYE')

  def _start_event_listener(self):
    #this section is a synchronizer so that all nodes can start ROUGHLY at the same time
    bus_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
      os.remove("/tmp/genesis_main.sock")
    except OSError:
      #traceback.print_exc()
      pass
    try:
      bus_socket.bind("/tmp/genesis_main.sock")
      bus_socket.listen(10000)
    except OSError:
      traceback.print_exc()
    except:
      traceback.print_exc()
    while self.state != "DISABLED":
      conn, addr = bus_socket.accept()
      try:
        lengthbuf = conn.recv(4)
        #print(lengthbuf)
        length, = struct.unpack('!I', lengthbuf)
        data = b''
        while length:
          newbuf = conn.recv(length)
          if not newbuf: return None
          data += newbuf
          length -= len(newbuf)
        #data = conn.recv(65500)
        #print(data)
        for cb in self.callbacks:
          cb(data)
        conn.close()
      except:
        pass
    bus_socket.close()

  def _printinfo(self):
    'Prints general information about the node'
    print()
    print("Network - Using the OS routing and network")
    print("Broadcast IP: " + self.bcast_group)
    print()

def main():
  """
  Main function
  """
  #this function controls all the tasks
  try:
    if args.command.upper() == 'RUN':
      runner, repetitions = _setup()
      _start(runner, repetitions)
      _shutdown()
    elif args.command.upper() == 'NEW':
      _new(args.name)
    elif args.command.upper() == 'CLEAN':
      _clean()
    elif args.command.upper() == 'ETCD':
      runner = _setup_etcd()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'TERM':
      runner = _setup_term()
      _start(runner, 1)
      _shutdown()
  except KeyboardInterrupt:
    logging.error("Interrupted by ctrl+c")
    os._exit(1)
  except SystemExit:
    logging.info("Quiting")
  except:
    logging.error("General error!")
    traceback.print_exc()

def _setup():
  simulation_file = open("./simulation.json","r").read()
  simulations = json.loads(simulation_file)
  for simulation in simulations['simulations']:
    repetitions = simulation['repetitions']
    scenario = simulation['scenario']
    tagbase = simulation['settings']['tagbase']
    application = simulation['settings']['application']
    time_scale = simulation['settings']['timeScale']
    time_limit = simulation['settings']['timeLimit']
    number_of_nodes = simulation['settings']['number_of_nodes']
    mobility = simulation['settings']['mobility']
    fault_detector = simulation['settings']['fault_detector']
    network = simulation['settings']['network']
    membership = simulation['settings']['membership']
    topology = simulation['settings']['topology']
    ip = simulation['settings']['ip']
    verboseLevel = simulation['settings']['verboseLevel']
    battery = simulation['settings']['battery']
    energy = simulation['settings']['energy']
    role = simulation['settings']['role']
    omnet = True if simulation['settings']['omnet'] == "True" else False
    core = True if simulation['settings']['core'] == "True" else False
    disks = True if simulation['settings']['disks'] == "True" else False
    dump = True if simulation['settings']['dump'] == "True" else False
    start_delay = simulation['settings']['start_delay']

    omnet_settings = simulations['omnet_settings']

    ### TODO: Move this to start
    runner = Runner(application, network, membership, time_scale, time_limit, number_of_nodes, omnet, core, disks, dump, start_delay, fault_detector, topology, omnet_settings)
    return runner, repetitions

def _setup_etcd():
  simulation_file = open("./simulation.json","r").read()
  simulations = json.loads(simulation_file)
  topology = simulation['etcd']['topology']
  number_of_nodes = simulation['etcd']['number_of_nodes']
  omnet = True if simulation['etcd']['omnet'] == "True" else False
  core = True if simulation['etcd']['core'] == "True" else False
  disks = True if simulation['etcd']['disks'] == "True" else False
  dump = True if simulation['etcd']['dump'] == "True" else False
  omnet_settings = simulations['omnet_settings']
  ### TODO: Move this to start
  runner = ETCDRunner(number_of_nodes, omnet, core, disks, dump, topology, omnet_settings)
  return runner

def _setup_term():
  simulation_file = open("./simulation.json","r").read()
  simulations = json.loads(simulation_file)
  topology = simulation['term']['topology']
  number_of_nodes = simulation['term']['number_of_nodes']
  omnet = True if simulation['term']['omnet'] == "True" else False
  core = True if simulation['term']['core'] == "True" else False
  disks = True if simulation['term']['disks'] == "True" else False
  dump = True if simulation['term']['dump'] == "True" else False
  omnet_settings = simulations['omnet_settings']
  ### TODO: Move this to start
  runner = TERMRunner(number_of_nodes, omnet, core, disks, dump, topology, omnet_settings)
  return runner

def _start(runner, repetitions):
  logging.info("Starting ...")
  for i in range(0,int(repetitions)):
    runner.start()

def _shutdown():
  pass

def _clean():
  confirm = input("This will erase all old reports. Proceed? [y/N]")
  if confirm.upper() == "Y":
    logging.info("Cleaning all reports in reports folder.")
    try:
      shutil.rmtree("./reports")
      os.mkdir("reports")
      print(username)
      os.system("chown -R " + username + ":" + username + " ./reports")
    except:
      #traceback.print_exc()
      logging.error("Could not clean or recreate report folder")
      return
    logging.info("Done.")
  else:
    logging.info("Skiped.")

def _new(application):
  if application == None:
    logging.error("Application name required.")
  else:
    logging.info("Scafolding: " + str(application))
    try:
      os.mkdir("./classes/apps/" + str(application))
    except FileExistsError:
      logging.error("Another application with same name already exists.")
      pass
      #sys.exit(1)
    except:
      traceback.print_exc()
    
    try:
      files = []
      for (dirpath, dirnames, filenames) in os.walk(localdir + "/scaffold/"):
        files.extend(filenames)
      for file in files:
        #print(file)
        shutil.copyfile(localdir +"/scaffold/" + file,localdir + "/classes/apps/" + str(application) + "/" + file)
      shutil.move(localdir + "/classes/apps/" + str(application) + "/app.py", localdir + "/classes/apps/" + str(application) + "/" + str(application) + ".py")
    except:
      traceback.print_exc()

#import socket, os, math, struct, sys, json, traceback, zlib, fcntl, threading, time, pickle, distutils
#from apscheduler.schedulers.background import BackgroundScheduler

if __name__ == '__main__':  #for main run the main function. This is only run when this main python file is called, not when imported as a class
  try:
    print("Genesis v." + __version__)
    print("Framework for testing distributed algorithms in dynamic networks")
    print()

    parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')
    parser.add_argument("command", help="Main command to execute: run a configured simulation or create a new application.", choices=['run', 'new', 'clean', 'etcd', 'term'])
    parser.add_argument("name", help="New application name", nargs='?')
    parser.add_argument("-l", "--log", help="Log level", choices=['debug', 'info', 'warning', 'error', 'critical'],default="info")
    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper(), format='%(asctime)s -> [%(levelname)s] %(message)s')
    logging.Formatter('%(asctime)s -> [%(levelname)s] %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #logging.basicConfig(level='INFO')
    #logging.info("Starting")

    if os.geteuid() != 0:
      logging.error("This must be run as root or with sudo.")
      sys.exit(1)

    simulation_file = open("simulation.json","r").read()
    simulation = json.loads(simulation_file)
    username = simulation['username']

    localdir = os.path.dirname(os.path.abspath(__file__))
    #############################################################################
    main(); #call scheduler function
  except KeyboardInterrupt:
    logging.error("Interrupted by ctrl+c")
  except SystemExit:
    logging.info("Quiting")
  except:
    traceback.print_exc()
