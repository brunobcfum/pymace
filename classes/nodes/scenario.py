from classes.nodes.fixed_node import FixedNode
from classes.nodes.mobile_node import MobileNode
from classes.mobility import node_mobility
from classes.runner.bus import Bus

#Core libs
from core.emulator.data import IpPrefixes, NodeOptions
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode
from core.location.mobility import BasicRangeModel

#Other libs
import sys, subprocess, os

class Scenario():
  def __init__(self, scenario_json) -> None:
    self.list_of_fixed_nodes = []
    self.number_of_nodes = scenario_json['settings']['number_of_nodes']
    self.username = scenario_json['settings']['username']
    self.disks_folder = scenario_json['settings']['disks_folder']
    self.dump = True if scenario_json['settings']['dump'] == "True" else False
    self._nodes = scenario_json['nodes']
    self.fixed_core_settings = self.get_fixed_settings(scenario_json)
    self.mobile_core_settings = self.get_mobile_settings(scenario_json)
    self.wlans = {}
    self.node_options_fixed = []
    self.node_options_mobile = []
    self.fixed_wlan = WlanNode
    self.mobile_wlan = WlanNode
    self.networks = {}
    self.nodes = {}
    self.core_nodes = {}
    self.core_nodes_by_name= {}
    self.node_options = {}
    self.prefixes = {}
    self.load_networks(scenario_json)
    self.load_nodes(scenario_json)
    self.etcd_cluster = {}
    self._setup_nodes(self._nodes)

  def load_networks(self, scenario_json):
    networks = scenario_json['networks']
    for network in networks:
      self.networks[network['name']] = {}
      self.networks[network['name']] = network
      #self.networks[network['name']]['routing'] = network['routing']
      self.prefixes[network['name']] = IpPrefixes(network['prefix'])
    #print(self.networks)
    #sys.exit(1)

  def load_nodes(self, scenario_json):
    nodes = scenario_json['nodes']
    counter = 1
    for node in nodes:
      self.nodes[node['name']] = {}
      self.nodes[node['name']]['settings'] = node['settings']
      self.nodes[node['name']]['function'] = node['function']
      self.nodes[node['name']]['type'] = node['type']
      self.nodes[node['name']]['extra'] = node['extra']
      self.nodes[node['name']]['name'] = node['name']
      self.nodes[node['name']]['id'] = counter
      counter += 1
      #[node['settings'], node['function'], node['type'], node['extra']]
    #print(self.nodes)
    #sys.exit(1)

  def get_number_nodes(self):
    return 0

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

  def _setup_nodes(self, nodes):
    for node in nodes:
      try:
        #print(node['settings']['x'])
        if (node['extra']['mobility'] != "none"):
          self.node_options_mobile.append(NodeOptions(name=node['settings']['type'] + str(node['settings']['_id'])))
          self.node_options_mobile[len(self.node_options_mobile) - 1].set_position(node['settings']['x'], node['settings']['y'])
          self.mobile_nodes.append(MobileNode(
                 coordinates = [node['settings']['x'], node['settings']['y'], 0],
                 tagname = node['settings']['type'] + str(node['settings']['_id']),
                 tag_number = node['settings']['_id'],
                 node_type = node['type'],
                 function = node['function']))
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

  def setup_nodes(self, session):
    for node in self.nodes:
      if self.nodes[node]['extra']['network'] not in self.node_options.keys():
        self.node_options[self.nodes[node]['extra']['network']] = []
      self.node_options[self.nodes[node]['extra']['network']].append(NodeOptions(name=self.nodes[node]['name'], x=self.nodes[node]['settings']['x'], y=self.nodes[node]['settings']['y']))
      #self.node_options[self.nodes[node]['extra']['network']][len(self.node_options[self.nodes[node]['extra']['network']]) - 1].set_position(self.nodes[node]['settings']['x'], self.nodes[node]['settings']['y'])

    for network in self.node_options:
      if network not in self.core_nodes.keys():
        self.core_nodes[network] = []
     
      for node_opt in self.node_options[network]:
        core_node = session.add_node(CoreNode, options=node_opt)
        self.core_nodes_by_name[node_opt.name] = core_node
        self.core_nodes[network].append(core_node)

  def setup_links(self, session):
    ### TODO temporary solution fix later
    for network in self.core_nodes:
      if network == "fixed":
        for node in self.core_nodes[network]:
          interface = self.prefixes[network].create_iface(node)
          interface2 = self.prefixes["mobile"].create_iface(node)
          try:
            session.add_link(node.id, self.wlans[network].id, iface1_data=interface)
            session.add_link(node.id, self.wlans["mobile"].id, iface1_data=interface2)
          except:
            print(node.name)
            print(self.wlans[network].id)
      else: 
        for node in self.core_nodes[network]:
          interface = self.prefixes[network].create_iface(node)
          session.add_link(node.id, self.wlans[network].id, iface1_data=interface)

  def setup_wlans(self, session):
    for network in self.networks:
      options = NodeOptions(name=network, x=0, y=0)
      lan = session.add_node(WlanNode,options=options)
      self.wlans[network] = lan
      session.mobility.set_model_config(lan.id, BasicRangeModel.name,self.networks[network]['settings'])

  def start_applications(self, session):
    for node in self.nodes:
      functions = self.nodes[node]['function']
      for function in functions:
        id = int(self.nodes[node]['settings']['_id']) + 1
        if function == 'terminal':
          self.start_terminal(session, id, node)
        elif function == 'disk':
          disk = self.create_disk(id, node)
        elif function == 'etcd':
          self.etcd_cluster[node] = {}
          prefix = self.networks[self.nodes[node]['extra']['network']]['prefix']
          prefix = prefix.split("/")[0]
          prefix = prefix.split(".")
          prefix[2] = str(int(prefix[2]) + 1)
          ip = prefix.copy()
          ip[3] = str(id)
          ip = '.'.join(ip)
          self.etcd_cluster[node]["ip"] = ip
          self.etcd_cluster[node]["prefix"] = prefix
          self.etcd_cluster[node]["disk"] = disk
          self.etcd_cluster[node]["id"] = id
          
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
    os.system("umount " + disk)
    os.system("rm -rf " + disk)
    os.system("mkdir " + disk)
    command = "mount -t tmpfs -o size=512m tmpfs " + disk + " &"
    node = subprocess.Popen([
                    "bash",
                    "-c",
                    command])
    return disk

  def start_routing(self, session):
    for network in self.networks:
      #print(self.networks[network])
      if self.networks[network]['routing'].upper() == 'NONE':
        continue
      elif self.networks[network]['routing'].upper() == 'BATMAN':
        for node in self.nodes:
          node_network = self.nodes[node]['extra']['network']
          if node_network == 'fixed':
            id = int(self.nodes[node]['settings']['_id']) + 1
            self.configure_batman(session, self.networks[network]['prefix'], id)

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
    print("starting ETCD")
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

  def get_core_node(self, node):
    pass

  def get_core_nodes(self):
    return self.core_nodes    

  def get_wlans(self):
    return self.wlans
    
  def configure_mobility(self, session):
    for node in self.nodes:
      if self.nodes[node]['extra']['mobility'] == "none":
        continue
      else:
        dimensions = [self.nodes[node]['extra']['mobility']['zone_x'],self.nodes[node]['extra']['mobility']['zone_y'],self.nodes[node]['extra']['mobility']['zone_z']]
        velocity = [self.nodes[node]['extra']['mobility']['velocity_lower'],self.nodes[node]['extra']['mobility']['velocity_upper']]
        mobility = node_mobility.Mobility(self, self.nodes[node]['extra']['mobility']['model'], dimensions, velocity)
        mobility.register_core_node(self.core_nodes_by_name[node])
