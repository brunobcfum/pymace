from classes.nodes.fixed_node import FixedNode
from classes.nodes.mobile_node import MobileNode

#Core libs
from core.emulator.data import IpPrefixes, NodeOptions
from core.nodes.base import CoreNode
from core.nodes.network import WlanNode
from core.location.mobility import BasicRangeModel

#Other libs
import sys

class Scenario():
  def __init__(self, scenario_json) -> None:
    self.list_of_fixed_nodes = []
    self.number_of_nodes = scenario_json['settings']['number_of_nodes']
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
    self.code_nodes = {}
    self.node_options = {}
    self.prefixes = {}
    self.load_networks(scenario_json)
    self.load_nodes(scenario_json)
    self._setup_nodes(self._nodes)

  def load_networks(self, scenario_json):
    networks = scenario_json['networks']
    for network in networks:
      self.networks[network['name']] = network['settings']
      self.prefixes[network['name']] = IpPrefixes(network['prefix'])
    #print(self.networks)
    #sys.exit(1)

  def load_nodes(self, scenario_json):
    nodes = scenario_json['nodes']
    for node in nodes:
      self.nodes[node['name']] = {}
      self.nodes[node['name']]['settings'] = node['settings']
      self.nodes[node['name']]['function'] = node['function']
      self.nodes[node['name']]['type'] = node['type']
      self.nodes[node['name']]['extra'] = node['extra']
      
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
      #print(self.nodes[node]['extra']['network'])
      if self.nodes[node]['extra']['network'] not in self.node_options.keys():
        self.node_options[self.nodes[node]['extra']['network']] = []
      self.node_options[self.nodes[node]['extra']['network']].append(NodeOptions(name=self.nodes[node]['settings']['type'] + str(self.nodes[node]['settings']['_id'])))
      self.node_options[self.nodes[node]['extra']['network']][len(self.node_options[self.nodes[node]['extra']['network']]) - 1].set_position(self.nodes[node]['settings']['x'], self.nodes[node]['settings']['y'])

    for network in self.node_options:
      if network not in self.code_nodes.keys():
        self.code_nodes[network] = []
      
      for node_opt in self.node_options[network]:
        self.code_nodes[network].append(session.add_node(CoreNode, options=node_opt))

    #print(self.node_options)
    #sys.exit(1)


  def setup_links(self, session):
    ### TODO temporary solution fix later
    for network in self.code_nodes:
      if network == "fixed":
        for node in self.code_nodes[network]:
          interface = self.prefixes[network].create_iface(node)
          interface2 = self.prefixes["mobile"].create_iface(node)
          session.add_link(node.id, self.wlans[network].id, iface1_data=interface)
          session.add_link(node.id, self.wlans["mobile"].id, iface1_data=interface2)

      else: 
        for node in self.code_nodes[network]:
          interface = self.prefixes[network].create_iface(node)
          session.add_link(node.id, self.wlans[network].id, iface1_data=interface)

    #pass

  def setup_wlans(self, session):
    for network in self.networks:
      options = NodeOptions(name=network, x=0, y=0)
      #print(self.networks[network])
      lan = session.add_node(WlanNode,options=options)
      self.wlans[network] = lan
      session.mobility.set_model_config(lan.id, BasicRangeModel.name,self.networks[network])
    #sys.exit(1)
    return
    fixed_wlan_options = NodeOptions(name='utm_wlan', x=200, y=200)
    mobile_wlan_options = NodeOptions(name='uas_wlan', x=0, y=0)
    ### TODO append directly later
    self.fixed_wlan = session.add_node(WlanNode,options=fixed_wlan_options)
    self.mobile_wlan = session.add_node(WlanNode,options=mobile_wlan_options)
    self.wlans.append(self.fixed_wlan)
    self.wlans.append(self.mobile_wlan)
    session.mobility.set_model_config(self.fixed_wlan.id, BasicRangeModel.name,self.fixed_core_settings)
    session.mobility.set_model_config(self.mobile_wlan.id, BasicRangeModel.name,self.mobile_core_settings)


  def get_wlans(self):
    return self.wlans

  def get_fixed_wlan(self):
    return self.fixed_wlan

  def get_mobile_wlan(self):
    return self.mobile_wlan

  def get_fixed_node_opts(self):
    return self.node_options_fixed

  def get_mobile_node_opts(self):
    return self.node_options_mobile