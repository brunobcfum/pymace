from classes.nodes.gen_node import GenericNode
from dataclasses import dataclass

@dataclass()
class MobileNode(GenericNode):

  def is_mobile(self):
    return True