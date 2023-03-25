""" 
Scenario class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

from classes.nodes.gen_node import GenericNode
from classes.mobility.node_mobility import Mobility
from classes.runner.bus import Bus

#Core libs
from core.emulator.data import IpPrefixes, NodeOptions
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode
from core.location.mobility import BasicRangeModel
from classes.virtual_gps import VirtualGPS

from core.emane.ieee80211abg import EmaneIeee80211abgModel
from core.emane.rfpipe import EmaneRfPipeModel
from core.emane.tdma import EmaneTdmaModel
from core.emane.nodes import EmaneNet

#Other libs
import sys, subprocess, os, traceback, pprint

class Scenario():
  def __init__(self, scenario_json) -> None:
    self.list_of_fixed_nodes = []
    self.number_of_nodes = scenario_json['settings']['number_of_nodes']
    self.username = scenario_json['settings']['username']
    self.disks_folder = scenario_json['settings']['disks_folder']
    self.dump = True if scenario_json['settings']['dump'] == "True" else False
    self._nodes = scenario_json['nodes']
    self.wlans = {}
    self.node_options_fixed = []
    self.node_options_mobile = []
    self.fixed_wlan = WlanNode
    self.mobile_wlan = WlanNode
    self.networks = {}
    self.core_nodes = {}
    self.core_nodes_by_name= {}
    self.node_options = {}
    self.prefixes = {}
    self.etcd_cluster = {}
    self.mace_nodes = []
    self.load_networks(scenario_json)
    self.load_nodes(scenario_json)
    self.cwd = os.getcwd()

  def load_networks(self, scenario_json):
    networks = scenario_json['networks']
    for network in networks:
      self.networks[network['name']] = {}
      self.networks[network['name']] = network
      self.prefixes[network['name']] = IpPrefixes(network['prefix'])

  def load_nodes(self, scenario_json):
    nodes = scenario_json['nodes']
    for node in nodes:
      try: 
        self.mace_nodes.append(GenericNode(
          coordinates = [node['settings']['x'], node['settings']['y'], 0],
          tagname = node['settings']['type'] + str(node['settings']['_id']),
          tag_number = node['settings']['_id'],
          node_type = node['type'],
          function = node['function'],
          name = node['name'],
          nodetype = node['type'],
          disks = True if (node['extra']['disks'] == "True") else False,
          dump = True if (node['extra']['dump']['start'] == "True") else False,
          dump_delay = int(node['extra']['dump']['delay']),
          dump_duration = int(node['extra']['dump']['duration']),
          mobility = node['extra']['mobility'],
          network = node['extra']['network'],
          max_position = None if node['extra']['mobility'] == "none" else [node['extra']['mobility']['zone_x'], node['extra']['mobility']['zone_y'], node['extra']['mobility']['zone_z']],
          velocity = None if node['extra']['mobility'] == "none" else [node['extra']['mobility']['velocity_lower'], node['extra']['mobility']['velocity_upper']]
        ))
      except:
        traceback.print_exc()

  def setup_nodes(self, session):
    for node in self.mace_nodes:
      node.options = NodeOptions(name=node.name, x=node.coordinates[0], y=node.coordinates[1])
      core_node = session.add_node(CoreNode, options=node.options)
      node.corenode = core_node
      node.gps = VirtualGPS(node.name, node.tag_number)
      node.gps.start()
      node.set_position([node.coordinates[0],node.coordinates[1]])

  def setup_links(self, session):
    for node in self.mace_nodes:
      for net in node.network:
        interface = self.prefixes[net].create_iface(node.corenode)
        session.add_link(node.corenode.id, self.wlans[net].id, iface1_data=interface)

  def setup_wlans(self, session):
    for network in self.networks:
      options = NodeOptions(name=network, x=0, y=0)
      lan = session.add_node(WlanNode,options=options)
      self.wlans[network] = lan
      session.mobility.set_model_config(lan.id, BasicRangeModel.name,self.networks[network]['settings'])

  def setup_wlan_emane(self, session):
    session.location.setrefgeo(47.57917, -122.13232, 2.0)
    session.location.refscale = 150.0
    for network in self.networks:
      options = NodeOptions(x=200, y=200, emane=EmaneIeee80211abgModel.name)
      lan = session.add_node(EmaneNet, options=options)
      modelname = EmaneIeee80211abgModel.name
      config = session.emane.get_configs()
      config.update({"eventservicettl": "2"})
      wifi_options = {
        "unicastrate": "12",
        "multicastrate": "12",
        "mode":"1",
      }
      self.wlans[network] = lan
      session.emane.set_model_config(lan.id, EmaneIeee80211abgModel.name, wifi_options)
      #session.mobility.set_model_config(lan.id, BasicRangeModel.name,self.networks[network]['settings'])
      config = session.emane.get_model_config(lan.id, EmaneIeee80211abgModel.name)
      pp = pprint.PrettyPrinter(indent=4)
      pp.pprint (config)
      #sys.exit(1)

  def start_applications(self, session):
    for node in self.mace_nodes:
      for function in node.function:
        if function == 'terminal':
          self.start_terminal(session, node.corenode.id, node.name)
        elif function == 'disk':
          disk = self.create_disk(node.corenode.id, node.name)
        elif function == 'etcd':
          self.etcd_cluster[node.name] = {}
          prefix = self.networks['fixed']['prefix'] #TODO fix
          prefix = prefix.split("/")[0]
          prefix = prefix.split(".")
          prefix[2] = str(int(prefix[2]) + 1)
          ip = prefix.copy()
          ip[3] = str(node.corenode.id)
          ip = '.'.join(ip)
          self.etcd_cluster[node.name]["ip"] = ip
          self.etcd_cluster[node.name]["prefix"] = prefix
          self.etcd_cluster[node.name]["disk"] = disk
          self.etcd_cluster[node.name]["id"] = node.corenode.id
        else:
          self.custom_application(session, node.corenode.id, function)
          
    if len(self.etcd_cluster) > 0:
      self.start_etcd(session)

  def start_terminal(self, session, i, node):
    ### TODO: add all application starts to inside node class
    nodes = {}
    shell = session.get_node(i, CoreNode).termcmdstring(sh="/bin/bash")
    command = ""
    node_process = subprocess.Popen([
                    "xterm",
                    "-e",
                    shell], stdin=subprocess.PIPE, shell=False)
    nodes[node] = node_process
    return nodes

  def create_disk(self,  i, node):
    #create virtual disk for each node
    disk = self.disks_folder + node
    os.system("umount " + disk + "  > /dev/null 2>&1 || /bin/true")
    os.system("rm -rf " + disk)
    os.system("mkdir -p " + disk)
    command = "mount -t tmpfs -o size=512m tmpfs " + disk + " &"
    node = subprocess.Popen([
                    "bash",
                    "-c",
                    command])
    return disk

  def start_routing(self, session):
    for node in self.mace_nodes:
      for net in node.network:
        if self.networks[net]['routing'].upper() == 'NONE':
          continue
        elif self.networks[net]['routing'].upper() == 'BATMAN':
          self.configure_batman(session, self.networks[net]['prefix'], node.corenode.id)

  def configure_batman(self, session, network_prefix, id):
    #Configure Batman only on fixed network
    network_prefix = network_prefix.split("/")[0]
    network_prefix = network_prefix.split(".")
    network_prefix[2] = str(int(network_prefix[2]) + 1)
    ip = network_prefix.copy()
    ip[3] = str(id)
    ip = '.'.join(ip)
    broadcast = network_prefix.copy()
    broadcast[3] = '255'
    broadcast = '.'.join(broadcast)
    network_prefix = '.'.join(network_prefix)
    ###TODO Change this to do only on fixed nodes
    shell = session.get_node(id, CoreNode).termcmdstring(sh="/bin/bash")
    command = "modprobe batman-adv && batctl ra BATMAN_IV && batctl if add eth0 && ip link set up bat0 && ip addr add " + ip + "/255.255.255.0 broadcast " + broadcast + " dev bat0"
    shell += " -c '" + command + "'"
    node = subprocess.Popen([
                  "xterm",
                  "-e",
                  shell], stdin=subprocess.PIPE, shell=False)

  def start_etcd(self, session):
    cluster_opt = "--initial-cluster "
    cluster = []
    for node in self.etcd_cluster:
      cluster.append(node + "=http://" + self.etcd_cluster[node]['ip']+":2380")
    cluster = ','.join(cluster)
    cluster = cluster_opt + cluster
    for node in self.etcd_cluster:
      shell = session.get_node(self.etcd_cluster[node]['id'], CoreNode).termcmdstring(sh="/bin/bash")
      command = "/opt/etcd/bin/etcd --data-dir=" + self.etcd_cluster[node]['disk'] 
      command += " --name " + node
      command += " --initial-advertise-peer-urls http://" + self.etcd_cluster[node]['ip']+":2380 "
      command += "--listen-peer-urls http://" + self.etcd_cluster[node]['ip']+":2380 "
      command += "--advertise-client-urls http://" + self.etcd_cluster[node]['ip']+":2379 "
      command += "--listen-client-urls http://" + self.etcd_cluster[node]['ip']+":2379,http://127.0.0.1:2379 "
      command += cluster
      command += " --initial-cluster-state new "
      command += "--initial-cluster-token token-01"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)

  def custom_application(self, session, i, application):
    shell = session.get_node(i, CoreNode).termcmdstring(sh="/bin/bash")
    shell = shell.split(" ")
    shell.append("-c")
    command = application
    shell.append(command)
    node = subprocess.Popen(shell, stdin=subprocess.PIPE, shell=False)

  def tcpdump(self, session, dir):
    """ 
    Method for starting a tcpdump session

    Parameters
    ----------
    session - CORE session created in runner
    dir - 

    Returns
    --------

    """
    for node in self.mace_nodes:
      if node.dump:
        shell = session.get_node(node.corenode.id, CoreNode).termcmdstring(sh="/bin/bash")
        command = "cd " + self.cwd + " && "
        #TODO: change eth0 to be configurable
        command += "sleep " + str(node.dump_delay) + " && timeout " + str(node.dump_duration) + " tcpdump -i eth0 -w "+ dir + node.name + ".pcap"
        shell += " -c '" + command + "'"
        node = subprocess.Popen([
              "xterm",
              "-hold",
              "-e",
              shell]
              ,stdin=subprocess.PIPE, shell=False)

  def get_core_nodes(self):
    return self.core_nodes    

  def get_wlans(self):
    return self.wlans

  def get_networks(self):
    return self.networks

  def get_mace_nodes(self):
    return self.mace_nodes
    
  def configure_mobility(self, session):
    for node in self.mace_nodes:
      if node.mobility == "none":
        pass
      else:
        node.mobility_model = Mobility(self, node.mobility['model'], node.max_position, node.velocity)
        node.mobility_model.register_core_node(node.corenode)
        node.mobility_model.register_mace_node(node)
        node.mobility_model.configure_mobility()
