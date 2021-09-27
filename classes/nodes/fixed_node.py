from classes.nodes.gen_node import GenericNode
from dataclasses import dataclass

@dataclass()
class FixedNode(GenericNode):
  def __init__(self):
    pass

  def is_mobile(self):
    return False