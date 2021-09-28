""" 
HET Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import traceback, os, logging, time, subprocess, threading, sys
from typing import Sequence
from classes.runner.runner import Runner

from .. import iosocket

from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, NodeOptions
from core.emulator.enumerations import NodeTypes, EventTypes
from core.location.mobility import BasicRangeModel
from core import constants
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode

from core.emane.ieee80211abg import EmaneIeee80211abgModel
from core.emane.rfpipe import EmaneRfPipeModel
from core.emane.tdma import EmaneTdmaModel
from core.emane.nodes import EmaneNet

from classes.mobility import mobility
from classes.runner.bus import Bus

from classes.nodes.fixed_node import FixedNode
from classes.nodes.scenario import Scenario

class HETRunner(Runner):

  def __init__(self, scenario):
    self.nodes_digest = {}
    self.iosocket_semaphore = False
    self.fixed_nodes = []
    self.mobile_nodes = []
    self.node_options_fixed = []
    self.node_options_mobile = []
    self.core_nodes_fixed = []
    self.core_nodes_mobile = []
    self.prefixe_fixed = "10.0.0.0/24"
    self.prefixe_mobile = "12.0.0.0/24"
    self.running = True
    self.setup(scenario)

  def setup(self, scenario):
    self.scenario = Scenario(scenario)
    self.Mobility = mobility.Mobility(self, 'RANDOM_DIRECTION')

  def callback(self):
    print("hello")

  def start(self):
    #pass
    self.run()

  def setup_core(self):
    os.system("core-cleanup")
    prefixes = IpPrefixes(self.prefixe_fixed)
    prefixes_mobile = IpPrefixes(self.prefixe_mobile)
    self.coreemu = CoreEmu()
    self.session = self.coreemu.create_session()
    # must be in configuration state for nodes to start, when using "node_add" below
    self.session.set_state(EventTypes.CONFIGURATION_STATE)

    #Called mobility by CORE, by it is actually more like the radio model
    self.modelname = BasicRangeModel.name

    self.scenario.setup_nodes(self.session)
    self.scenario.setup_wlans(self.session)
    self.scenario.setup_links(self.session)

    list_mobile_nodes = []
    core_nodes = self.scenario.get_core_nodes()
    for network in core_nodes:
      if network == "mobile":
        self.Mobility.register_core_nodes(core_nodes[network])
    self.Mobility.start()
    self.session.instantiate()
    self.session.write_nodes()
    #self.coreemu.shutdown()
    
  def add_one_node(self, node):
    pass

  def configure_batman(self, network_prefix, list_of_nodes):
    #Configure Batman only on fixed network
    network_prefix = network_prefix.split("/")[0]
    network_prefix = network_prefix.split(".")
    network_prefix[2] = str(int(network_prefix[2]) + 1)
    network_prefix = '.'.join(network_prefix)
    process = []
    ###TODO Change this to do only on fixed nodes
    for node in list_of_nodes:
      shell = self.session.get_node(node, CoreNode).termcmdstring(sh="/bin/bash")
      #command = "ip link set eth0 address 0A:AA:00:00:00:" + '{:02x}'.format(i+2) +  " && batctl if add eth0 && ip link set up bat0 && ip addr add 10.0.1." +str(i+2) + "/255.255.255.0 broadcast 10.0.1.255 dev bat0"
      command = "modprobe batman-adv && batctl ra BATMAN_IV && batctl if add eth0 && ip link set up bat0 && ip addr add " + network_prefix +str(node) + "/255.255.255.0 broadcast 10.0.1.255 dev bat0"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                    "xterm",
                    "-e",
                    shell], stdin=subprocess.PIPE, shell=False)
      process.append(node)

  def server_thread(self):
    'Starts a thread with the Socket.io instance that will serve the HMI'
    mobile_lan = self.scenario.get_wlans()['mobile']
    mobile_core_nodes = self.scenario.get_core_nodes()['mobile']
    fixed_lan = self.scenario.get_wlans()['fixed']
    fixed_core_nodes = self.scenario.get_core_nodes()['fixed']
    nodes = mobile_core_nodes + fixed_core_nodes
    #setattr(self, "iosocket", iosocket.Socket([], mobile_lan, self.session, self.modelname, self.nodes_digest, self.iosocket_semaphore, self))
    self.iosocket = iosocket.Socket(nodes, mobile_lan, self.session, self.modelname, self.nodes_digest, self.iosocket_semaphore, self, self.callback)
    #self.iosocket_fixed = iosocket.Socket(fixed_core_nodes, mobile_lan, self.session, self.modelname, self.nodes_digest, self.iosocket_semaphore, self)

  def run(self):
    """
    Runs the emulation of a heterogeneous scenario
    """

    #Setup and Start core
    self.setup_core()

    #start dumps
    if self.scenario.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    #Start socketio thread
    sthread = threading.Thread(target=self.server_thread, args=())
    sthread.start()

    #Start routing and applications
    self.scenario.start_routing(self.session)
    self.scenario.start_applications(self.session)

    while self.running:
      time.sleep(0.1)

    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    self.coreemu.shutdown()
    os.system("sudo killall xterm")
    os.system("chown -R " + self.scenario.username + ":" + self.scenario.username + " ./reports")

