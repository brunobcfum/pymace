from dataclasses import dataclass, field
from typing import List
from core.emulator.data import NodeOptions
from core.nodes.base import CoreNode
from classes.virtual_gps import VirtualGPS
from classes.mobility.node_mobility import Mobility

@dataclass()
class GenericNode():
  coordinates: List[float]
  options: NodeOptions = None
  corenode: CoreNode = None
  gps: VirtualGPS = None
  mobility_model: Mobility = None
  lat: float = None
  lon: float = None
  alt: float = None
  tagname: str = None
  tag_number: int = None
  node_type: str = None
  function: List[str] = None
  name: str = None
  nodetype: str = None
  disks: bool = False
  dump: bool = False
  dump_delay: int = None
  dump_duration: int = None
  mobility: str = None
  network: List[str] = None
  max_position: List[float] = field(default_factory=lambda: [5000,5000,5000])
  velocity: List[float] = None

  #PRIVATE

  #PUBLIC

  def update_position(self, coordinates):
    if ((coordinates[0] < self.max_position[0] and coordinates[0] >= 0) and 
        (coordinates[1] < self.max_position[1] and coordinates[1] >= 0) and 
        (coordinates[2] < self.max_position[2] and coordinates[2] >= 0)):
      self.coordinates = coordinates

  def get_position(self):
    return self.position

  def set_position(self, pos):
    self.coordinates[0] = pos[0]
    self.coordinates[1] = pos[1]
    self.gps.set_position(pos)
  
  def get_name(self):
    return self.tagname

  def get_tag_number(self):
    return self.tag_number