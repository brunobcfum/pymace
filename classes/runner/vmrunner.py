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

class VMRunner(Runner):

  def __init__(self, 
               number_of_nodes,     # Total number of nodes
               core,                # Run CORE emulator?
               disks,               # Create virtual disks?
               dump,                # Use TCP Dump?
               topology):
    self.number_of_nodes = number_of_nodes
    self.core = core
    self.disks = disks
    self.dump = dump
    self.nodes_digest = {}
    self.topology = topology
    self.iosocket_semaphore = False

  def start(self):
    self.run()

  def run(self):
    """
    Runs the emulation of Virtual machines running QEMU
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

    self.configure_bridge()
    qemu_nodes = self.spawnQEMU(self.session, self.number_of_nodes)

    while True:
      time.sleep(0.1)
    # shutdown session
    logging.info("Simulation finished. Killing all processes")
    if self.core:
      self.coreemu.shutdown()

    os.system("sudo killall xterm")
    os.system("chown -R " + username + ":" + username + " ./reports")

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

  def spawnQEMU(self, session, number_of_nodes):
    print("Starting QEMU")
    nodes = {}
    for i in range(0,number_of_nodes):
      shell = session.get_node(i+1, CoreNode).termcmdstring(sh="/bin/bash")
      command = "qemu-system-x86_64"
      command += " -m 2048" 
      command += " -boot d -enable-kvm -smp 3"
      command += " -hda /opt/vms/linux_x86_" + str(i+1) + ".img"
      command += " -device e1000,netdev=mynet1,mac=DE:AD:BE:EF:00:0" + str(i+1)
      command += " -netdev tap,id=mynet1,ifname=tap0,script=no" 
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes