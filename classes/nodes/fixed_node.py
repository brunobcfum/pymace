from classes.nodes.gen_node import GenericNode
from dataclasses import dataclass

@dataclass()
class FixedNode(GenericNode):

  def is_mobile(self):
    return false