""" 
RIOT Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import traceback, os, logging, time, subprocess, threading
from classes.runner.runner import Runner

from core.nodes.base import CoreNode

from classes.mobility import mobility

class RIOTRunner(Runner):

  def __init__(self, emulation):
    self.setup(emulation)
    self.nodes_digest = {}
    self.iosocket_semaphore = False

  def setup(self, emulation):
    self.topology = emulation['riot']['topology']
    self.number_of_nodes = emulation['riot']['number_of_nodes']
    self.core = True if emulation['riot']['core'] == "True" else False
    self.serial = True if emulation['riot']['serial'] == "True" else False
    self.disks = True if emulation['riot']['disks'] == "True" else False
    self.dump = True if emulation['riot']['dump'] == "True" else False
    self.mobility_model = emulation['riot']['mobility']
    self.app_dir = emulation['riot']['app_dir']
    self.app = emulation['riot']['app']
    self.Mobility = mobility.Mobility(self, self.mobility_model)

  def start(self):
    self.run()

  def run(self):
    """
    Runs the emulation of RIOT OS Applications
    """

    #start core
    if self.core:
      self.core_topology()
      self.configure_batman()

    #start dumps
    if self.dump:
      #get simdir
      simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
      #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.omnet:
        self.tcpdump(self.number_of_nodes, "./reports/" + simdir + "/tracer")
      if self.core:
        self.tcpdump_core(self.number_of_nodes, "./reports/" + simdir + "/tracer")

    if self.core:
      #pass
      sthread = threading.Thread(target=self.server_thread, args=())
      sthread.start()

    #self.configure_bridge()
    self.configure_serial(self.number_of_nodes)
    riot_nodes = self.run_riot(self.session, self.number_of_nodes, self.app_dir, self.app)

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
