""" 
Docker Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import  traceback, os, logging, time, subprocess, threading, json

from classes.runner.runner import Runner
from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, NodeOptions
from core.emulator.enumerations import EventTypes
from core.nodes.docker import DockerNode
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode
from core.location.mobility import BasicRangeModel

from core.emane.ieee80211abg import EmaneIeee80211abgModel
from core.emane.nodes import EmaneNet

class DockerRunner(Runner):
  """
  A class for creating nodes running docker images
  ...

  Attributes
  ----------
  core : Boolean
      Using core as emulator?
  dump : Boolean
      Create network dump with tcpdump?
  number_of_nodes : int
      The number of nodes to be considered
  topology: json object
      A JSON opbject containing the topology
  radius: int
      The range radius of the wireless radio

  Methods
  -------
  check_finished()
      check if all nodes finished the sessionS
  """
  def __init__(self, 
               number_of_nodes,     # Total number of nodes
               core,                # Run CORE emulator?
               dump,                # Use TCP Dump?
               topology,            # Topology chosen in configuration file
               radius):             # Range radius of the wireless radio
    """
    Parameters
    ----------
    core : Boolean
        Using core as emulator?
    dump : Boolean
        Create network dump with tcpdump?
    number_of_nodes : int
        The number of nodes to be considered
    topology: json object
        A JSON opbject containing the topology
    radius: int
        The range radius of the wireless radio
    nodes_digest: dictionary
        A dict that stores a digest about each node
    nodes: list
        A list that stores all nodes objects
    """
    self.number_of_nodes = number_of_nodes
    self.core = core
    self.dump = dump
    self.nodes_digest = {}
    self.topology = topology
    self.iosocket_semaphore = False
    self.radius = radius
    self.nodes = []

  def start(self):
    self.run()

  def run(self):
    os.system("core-cleanup")
    self.coreemu = CoreEmu()
    self.session = self.coreemu.create_session()
    self.session.set_state(EventTypes.CONFIGURATION_STATE)

    topology_file = open("./topologies/" + self.topology + ".json","r").read()
    topology = json.loads(topology_file)
    topo = []
    for node in topology:
      topo.append([int(node['x']), int(node['y'])])
    #start dumps
    if self.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.omnet:
        self.tcpdump(self.number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.core:
        self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")


    # create nodes and interfaces
    try:
      node_options=[]
      for i in range(0,self.number_of_nodes):
        node_options.append(NodeOptions(name='drone'+str(i),model=None, image="bruno/ubuntu"))
      prefixes = IpPrefixes(ip4_prefix="10.0.0.0/24")

      for i in range(0,self.number_of_nodes):
        node_options[i].set_position(topo[i][0],topo[i][1])
      
      options = NodeOptions(x=200, y=200)
      
      for node_opt in node_options:
        self.nodes.append(self.session.add_node(DockerNode, options=node_opt))
      
      self.wlan = self.session.add_node(WlanNode,options=options)
      self.modelname = BasicRangeModel.name
      self.session.mobility.set_model_config(self.wlan.id, BasicRangeModel.name,
          {
              "range": self.radius,
              "bandwidth": "433300000",
              "delay": "300",
              "jitter": "0",
              "error": "0",
          },
      )

      for node in self.nodes:
        interface = prefixes.create_iface(node)
        self.session.add_link(node.id, self.wlan.id, iface1_data=interface)

      # instantiate
      self.session.instantiate()

      sthread = threading.Thread(target=self.server_thread, args=())
      sthread.start()
    finally:
      input("continue to shutdown")
      logging.info("Simulation finished. Killing all processes")
      self.coreemu.shutdown()

    os.system("chown -R " + username + ":" + username + " ./reports")

