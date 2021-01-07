""" 
Terminal Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import  traceback, os, logging, time, subprocess, threading
from classes.runner.runner import Runner

from core.nodes.base import CoreNode

class TERMRunner(Runner):

  def __init__(self, 
               number_of_nodes,     # Total number of nodes
               omnet,               # Run omnet simulator?
               core,                # Run CORE emulator?
               disks,               # Create virtual disks?
               dump,                # Use TCP Dump?
               topology,
               omnet_settings):
    self.number_of_nodes = number_of_nodes
    self.omnet = omnet
    self.core = core
    self.disks = disks
    self.dump = dump
    self.omnet_settings = omnet_settings
    self.nodes_digest = {}
    self.topology = topology
    self.iosocket_semaphore = False

  def start(self):
    self.run()

  def run(self):
    'Runs each component of the simulation OMNet or CORE, configures BATMAN in each node, and launches the application'

    #start omnet
    if self.omnet:
      OMNet = self.omnet_run(self.omnet_settings)
      logging.info("Started OMNet++ with PID: " + str(OMNet.pid))    
    
    #start core
    if self.core:
      self.core_topology()
      self.configure_batman()

    #create disks
    if self.disks:
      self.createDisks(self.number_of_nodes)

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

    if self.omnet:
      terminals = self.spawnTerminalOmnet(self.number_of_nodes)
    elif self.core:
      terminals = self.spawnTerminalCore(self.session, self.number_of_nodes)
    #self._auto_job(self.number_of_nodes)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def spawnTerminalCore(self, session, number_of_nodes):
    print("Starting Terminals in CORE")
    nodes = {}
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = ""
      #shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      #"-xrm 'XTerm.vt100.allowTitleOps: false' -title drone" + str(i),
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes

  def spawnTerminalOmnet(self, number_of_nodes):
    nodes = {}
    for i in range(0,number_of_nodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i)
      command += " -hold"
      #print()
      node = subprocess.Popen([
                          "ip",
                          "netns",
                          "exec",
                          "drone" + str(i),
                          "bash",
                          "-c",
                          command])
      nodes["drone" + str(i)] = node
    return nodes
