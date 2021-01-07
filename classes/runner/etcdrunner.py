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

class ETCDRunner(Runner):

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
      etcd_nodes = self.spawnEtcdOmnet(self.session, self.number_of_nodes)
    elif self.core:
      etcd_nodes = self.spawnEtcdCore(self.session, self.number_of_nodes)
    #self._auto_job(self.number_of_nodes)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

  def spawnEtcdCore(self, session, number_of_nodes):
    print("starting ETCD CORE")
    nodes = {}
    cluster = "--initial-cluster "
    for i in range(0,number_of_nodes-1):
      cluster+= "node" + str(i) + "=http://10.0.1."+str(i+1)+":2380,"
    cluster+= "node" + str(number_of_nodes-1) + "=http://10.0.1."+str(number_of_nodes)+":2380 "
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = "/opt/etcd/etcd --data-dir=/mnt/pymace/drone" + str(i) + " --name node" + str(i)
      command += " --initial-advertise-peer-urls http://10.0.1." + str(i+1) + ":2380 "
      command += "--listen-peer-urls http://10.0.1." + str(i+1) + ":2380 "
      command += "--advertise-client-urls http://10.0.1." + str(i+1) + ":2379 "
      command += "--listen-client-urls http://10.0.1." + str(i+1) + ":2379,http://127.0.0.1:2379 "
      command += cluster
      command += "--initial-cluster-state new "
      command += "--initial-cluster-token token-01"
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      #"-xrm 'XTerm.vt100.allowTitleOps: false' -title drone" + str(i),
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes

  def spawnEtcdOmnet(self, number_of_nodes):
    nodes = {}
    cluster = "--initial-cluster "
    for i in range(0,number_of_nodes-1):
      cluster+= "node" + str(i) + "=http://10.0.1."+str(i+2)+":2380,"
    cluster+= "node" + str(number_of_nodes-1) + "=http://10.0.1."+str(number_of_nodes+1)+":2380 "
    for i in range(0,number_of_nodes):
      command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i)
      command += " -hold -e /opt/etcd/etcd --data-dir=/mnt/etcd/node" + str(i) + " --name node" + str(i)
      command += " --initial-advertise-peer-urls http://10.0.1." + str(i+2) + ":2380 "
      command += "--listen-peer-urls http://10.0.1." + str(i+2) + ":2380 "
      command += "--advertise-client-urls http://10.0.1." + str(i+2) + ":2379 "
      command += "--listen-client-urls http://10.0.1." + str(i+2) + ":2379,http://127.0.0.1:2379 "
      command += cluster
      command += "--initial-cluster-state new "
      command += "--initial-cluster-token token-01"
      #print(command)
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