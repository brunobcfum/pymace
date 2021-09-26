from dataclasses import dataclass, field
from typing import List

@dataclass()
class GenericNode():
  coordinates: List[float]
  lat: float = None
  lon: float = None
  alt: float = None
  tagname: str = None
  tag_number: int = None
  node_type: str = None
  function: str = None
  max_position: List[float] = field(default_factory=lambda: [5000,5000,5000])


  #PRIVATE

  #PUBLIC

  def update_position(self, coordinates):
    if ((coordinates[0] < self.max_position[0] and coordinates[0] >= 0) and 
        (coordinates[1] < self.max_position[1] and coordinates[1] >= 0) and 
        (coordinates[2] < self.max_position[2] and coordinates[2] >= 0)):
      self.position = coordinates

  def get_position(self):
    return self.position

  
  def get_name(self):
    return self.tagname

  def get_tag_number(self):
    return self.tag_number