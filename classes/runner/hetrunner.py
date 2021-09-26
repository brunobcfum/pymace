""" 
HET Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import traceback, os, logging, time, subprocess, threading, sys
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
    self.setup(scenario)

  def setup(self, scenario):
    #self.topology = scenario['setup']['topology']
    self.number_of_nodes = scenario['settings']['number_of_nodes']
    self.dump = True if scenario['settings']['dump'] == "True" else False
    self.nodes = scenario['nodes']
    self.fixed_core_settings = self.get_fixed_settings(scenario)
    self.mobile_core_settings = self.get_mobile_settings(scenario)
    self.Mobility = mobility.Mobility(self, 'random_walk')
    self._setup_nodes(self.nodes)

    #self.serial = True if scenario['riot']['serial'] == "True" else False
    #self.disks = True if scenario['riot']['disks'] == "True" else False
    #self.dump = True if scenario['riot']['dump'] == "True" else False
    #self.mobility_model = scenario['riot']['mobility']
    #self.app_dir = scenario['riot']['app_dir']
    #self.app = scenario['riot']['app']
    #self.Mobility = mobility.Mobility(self, self.mobility_model)

  def _setup_nodes(self, nodes):
    for node in nodes:
      try:
        #print(node['settings']['x'])
        if (node['extra']['mobility'] != "none"):
          self.node_options_mobile.append(NodeOptions(name=node['settings']['type'] + str(node['settings']['_id'])))
          self.node_options_mobile[len(self.node_options_mobile) - 1].set_position(node['settings']['x'], node['settings']['y'])
        else:
          self.node_options_fixed.append(NodeOptions(name=node['settings']['type'] + str(node['settings']['_id'])))
          self.node_options_fixed[len(self.node_options_fixed) - 1].set_position(node['settings']['x'], node['settings']['y'])
          self.fixed_nodes.append(FixedNode(
                 coordinates = [node['settings']['x'], node['settings']['y'], 0],
                 tagname = node['settings']['type'] + str(node['settings']['_id']),
                 tag_number = node['settings']['_id'],
                 node_type = node['type'],
                 function = node['function']))
          #print(self.fixed_nodes)
      except:
        #traceback.print_exc()
        print("Missing settings key in nodes. Aborting simulation.")
    #sys.exit(1)

  def start(self):
    #pass
    self.run()

  def get_fixed_settings(self, scenario):
    settings = {
      "range": scenario['fixed_core_settings']['radius'],
      "bandwidth": scenario['fixed_core_settings']['bandwidth'],
      "delay": scenario['fixed_core_settings']['delay'],
      "jitter": scenario['fixed_core_settings']['jitter'],
      "error": scenario['fixed_core_settings']['error']
    }
    return settings

  def get_mobile_settings(self, scenario):
    settings = {
      "range": scenario['mobile_core_settings']['radius'],
      "bandwidth": scenario['mobile_core_settings']['bandwidth'],
      "delay": scenario['mobile_core_settings']['delay'],
      "jitter": scenario['mobile_core_settings']['jitter'],
      "error": scenario['mobile_core_settings']['error']
    }
    return settings

  def setup_core(self):
    os.system("core-cleanup")
    prefixes = IpPrefixes("10.0.0.0/24")
    prefixes_mobile = IpPrefixes("12.0.0.0/24")
    self.coreemu = CoreEmu()
    self.session = self.coreemu.create_session()
    # must be in configuration state for nodes to start, when using "node_add" below
    self.session.set_state(EventTypes.CONFIGURATION_STATE)
    fixed_wlan_options = NodeOptions(name='uwlan', x=200, y=200)
    mobile_wlan_options = NodeOptions(name='mwlan', x=0, y=0)
    self.fixed_wlan = self.session.add_node(WlanNode,options=fixed_wlan_options )
    self.mobile_wlan = self.session.add_node(WlanNode,options=mobile_wlan_options )
    self.modelname = BasicRangeModel.name
    self.session.mobility.set_model_config(self.fixed_wlan.id, BasicRangeModel.name,self.fixed_core_settings)
    self.session.mobility.set_model_config(self.mobile_wlan.id, BasicRangeModel.name,self.mobile_core_settings)

    for node_opt in self.node_options_fixed:
      self.core_nodes_fixed.append(self.session.add_node(CoreNode, options=node_opt))

    for node_opt in self.node_options_mobile:
      self.core_nodes_mobile.append(self.session.add_node(CoreNode, options=node_opt))

    for node in self.core_nodes_fixed:
      interface = prefixes.create_iface(node)
      interface2 = prefixes_mobile.create_iface(node)
      self.session.add_link(node.id, self.fixed_wlan.id, iface1_data=interface)
      self.session.add_link(node.id, self.mobile_wlan.id, iface1_data=interface2)

    for node in self.core_nodes_mobile:
      interface = prefixes_mobile.create_iface(node)
      self.session.add_link(node.id, self.mobile_wlan.id, iface1_data=interface)

    self.Mobility.register_core_nodes(self.core_nodes_mobile)
    #self.Mobility.start()
    self.session.instantiate()
    #self.coreemu.shutdown()
    

  def add_one_node(self, node):
    pass

  def configure_batman(self):
    pass

  def server_thread(self):
    'Starts a thread with the Socket.io instance that will serve the HMI'
    self.iosocket = iosocket.Socket(self.core_nodes_mobile, self.mobile_wlan, self.session, self.modelname, self.nodes_digest, self.iosocket_semaphore, self)

  def run(self):
    """
    Runs the emulation of a heterogeneous scenario
    """

    #start core
    self.setup_core()
    self.configure_batman()

    #start dumps
    if self.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    
    sthread = threading.Thread(target=self.server_thread, args=())
    sthread.start()
  
    #self.configure_bridge()
    #self.configure_serial(self.number_of_nodes)
    #riot_nodes = self.run_riot(self.session, self.number_of_nodes, self.app_dir, self.app)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def configure_serial(self, number_of_nodes):
    pass

  def configure_bridge(self):
    process = []
    for i in range(0,self.number_of_nodes):
      shell = self.session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command =  "ip tuntap add tap0 mode tap"
      command += " && ip link add br0 type bridge"
      command += " && ip link set br0 up"
      command += " && ip link set tap0 up"
      command += " && ip link set tap0 master br0"
      command += " && ip link set bat0 master br0"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                    "xterm",
                    "-e",
                    shell], stdin=subprocess.PIPE, shell=False)
      process.append(node)

  def run_riot(self, session, number_of_nodes, app_dir, app):
    print("Starting RIOT Application: " + app)
    nodes = {}
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = app_dir
      command += "/" + app
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes
