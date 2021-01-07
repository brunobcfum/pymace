#!/usr/bin/env python3

import logging

from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, NodeOptions
from core.emulator.enumerations import EventTypes
from core.nodes.docker import DockerNode

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    coreemu = CoreEmu()
    session = coreemu.create_session()
    session.set_state(EventTypes.CONFIGURATION_STATE)

    # create nodes and interfaces
    try:
        prefixes = IpPrefixes(ip4_prefix="10.83.0.0/16")
        options = NodeOptions(model=None, image="bruno/ubuntu")

        # create node one
        node1 = session.add_node(DockerNode, options=options)
        interface1_data = prefixes.create_iface(node1)

        # create node two
        node2 = session.add_node(DockerNode, options=options)
        interface2_data = prefixes.create_iface(node2)

        # add link
        session.add_link(node1.id, node2.id, interface1_data, interface2_data)

        # instantiate
        session.instantiate()
    finally:
        input("continue to shutdown")
        coreemu.shutdown()