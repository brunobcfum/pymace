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

from classes.mobility import mobility

class RaspRunner(Runner):

  def __init__(self, emulation):
    self.setup(emulation)
    self.nodes_digest = {}
    self.iosocket_semaphore = False

  def setup(self, emulation):
    self.topology = emulation['rasp']['topology']
    self.number_of_nodes = emulation['rasp']['number_of_nodes']
    self.core = True if emulation['rasp']['core'] == "True" else False
    self.disks = True if emulation['rasp']['disks'] == "True" else False
    self.dump = True if emulation['rasp']['dump'] == "True" else False
    self.mobility_model = emulation['rasp']['mobility']
    self.kernel = emulation['rasp']['kernel']
    self.image = emulation['rasp']['image_sufix']
    self.dtb = emulation['rasp']['dtb']
    self.mac_sufix = emulation['rasp']['mac_sufix']
    self.tap_interface = emulation['rasp']['tap_interface']
    self.Mobility = mobility.Mobility(self, self.mobility_model)

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

    time.sleep(0.5)
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
      command = "qemu-system-arm"
      command += " -kernel " + self.kernel
      command += " -dtb " + self.dtb
      command += " -m 256 -M versatilepb -cpu arm1176"  # Has to be hardcoded for now since only compatible known
      command += " -serial stdio"
      command += " -append \"rw console=ttyAMA0 root=PARTUUID=4d3ee428-02 rootfstype=ext4  loglevel=8 rootwait fsck.repair=yes memtest=1\""
      command += " -drive file=" + self.image + str(i) + ".img,format=raw"
      command += " -no-reboot"
      command += " -net nic,macaddr=" + self.mac_sufix + str('{0:0{1}X}'.format(i,2))# + " -net user"
      command += " -net tap,ifname=" + self.tap_interface + ",script=no,downscript=no"
      print(command)
      shell += " -c '" + command + "'"
      node = subprocess.Popen([
                      "xterm",
                      "-e",
                      shell], stdin=subprocess.PIPE, shell=False)
      nodes["drone" + str(i)] = node
    return nodes
