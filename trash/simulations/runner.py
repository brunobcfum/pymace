#!/usr/bin/python3
#
""" 
Main scenario runner is part of a thesis on distributed systems
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import threading, sys, time, random, os, traceback, json, shutil, argparse, subprocess, signal
import rest, socket, auxiliar

def topology(args):
    
  #start omnet
  if args.omnet:
    OMNet = omnet(args, settings)
  print("Started OMNet++ with PID: " + str(OMNet.pid))    
  #create disks
  if args.disks:
    createDisks(number_of_nodes)

  #start terminals
  if args.terminal:
    terminal(args)

  #get simdir
  simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)

  #create nodes
  createNodes(number_of_nodes, application, protocol)

  #wait for nodes to start and create socket. This is only needed for slow computers.
  backoff = 0
  started = False
  time.sleep(1)
  starting_time = time.time() + start_delay
  while (len(nodes_to_start) > 0):
    time.sleep(backoff) 
    try:
      #firing up the nodes
      startNodes(starting_time)
    except SystemExit:
      os.system("sudo killall xterm")
      sys.exit(1)
    except:
      print("Too fast... backing off: " + str(backoff))
      backoff += 0.2

  #start dumps
  if args.dump:
    #createDumps(number_of_nodes, "./reports/" + simdir + "/tracer")
    tcpdump(number_of_nodes, "./reports/" + simdir + "/tracer")
  #this keeps the script on a lock until all nodes had finished.
  path ="./reports/" + simdir + "/finished"
  print("Checking for nodes finished in: " + path)
  Aux = auxiliar.Auxiliar(path, number_of_nodes)
  lock=True
  while lock==True:
    lock = Aux.check_finished()
    time.sleep(1)

  # shutdown session
  print("Simulation finished. Killing all processes")
  os.system("sudo killall xterm")


def omnet(args, settings):
  #this opens a terminal windows with omnet running
  omnet = subprocess.Popen([
                "xterm",
                "-hold",
                "-e",
                "taskset -c 6 inet -u Cmdenv -n " + settings['omnet_include_path'] + " " + settings['ini_file']]
                , stdin=subprocess.PIPE, shell=False)
  return omnet

def terminal(args):
  #open extra terminal windows in each node
  for i in range(0,args.numberOfNodes):
    command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T client" + str(i) + " &"
    node = subprocess.Popen([
                  "ip",
                  "netns",
                  "exec",
                  "drone" + str(i),
                  "bash",
                  "-c",
                  command])
def createDisks(number_of_nodes):
  #create virtual disk for each node
  for i in range(0,number_of_nodes):
    command = "mount -t tmpfs -o size=512m tmpfs /mnt/genesis/drone" + str(i) + " &"
    node = subprocess.Popen([
                  "bash",
                  "-c",
                  command])

def createNodes(number_of_nodes, application, protocol):
  #creates a terminal window for each node running the main application
  process = []
  for i in range(0,number_of_nodes):
    command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T drone" + str(i) 
    command += " -hold -e ./main.py drone"+ str(i) + " " + application + " " 
    command += str(time_scale) + " " + str(time_limit) + " random_walk -p " 
    command += protocol  + " ipv4 -b 100 -r node"
    command += " -m " + membership + " &"
    node = subprocess.Popen([
                  "ip",
                  "netns",
                  "exec",
                  "drone" + str(i),
                  "bash",
                  "-c",
                  command])
    process.append(node)

def startNodes(time_to_start):
  # Start each node application trying to create an ilusion that they are in sync
  # They receive a time when they should start, so it that they start very close to eachother
  for node in nodes_to_start:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/tmp/genesis.sock.drone"+str(node))
    s.send(str(time_to_start).encode())
    data = s.recv(10)
    s.close()
    if (data.decode() == "OK"):
      #print("Got ok from:" + str(node))
      nodes_to_start.remove(node)
    elif (data.decode() == "NOK"):
      print("Too fast for this computer, please increase the start_delay in this script")
      sys.exit()
    #print(nodes_to_start)

def createDumps(number_of_nodes,dir):
  #create virtual disk for each node 
  for i in range(0,number_of_nodes):
    command = "tshark -a duration:" + str(time_limit) + " -i bat0 -w "+ dir +"/drone" + str(i) + ".pcap &"
    node = subprocess.Popen([
                  "ip",
                  "netns",
                  "exec",
                  "drone" + str(i),
                  "bash",
                  "-c",
                  command])

def tcpdump(number_of_nodes,dir):
  #
  for i in range(0,number_of_nodes):
    command = "timeout " + str(time_limit) + " tcpdump -i bat0 -w "+ dir +"/drone" + str(i) + ".pcap &"
    node = subprocess.Popen([
                  "ip",
                  "netns",
                  "exec",
                  "drone" + str(i),
                  "bash",
                  "-c",
                  command])

if __name__ == "__main__":
  try:
    print("This is a testing agent for dist. sched. in dynamic networks")
    print("genesis mobility v." + __version__)
    print()

    parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')

    parser.add_argument("application", help="Which application you want to use")
    parser.add_argument("time_scale", help="Time scaler to make the application run faster(<1) or slower(>1)", type=float)
    parser.add_argument("time_limit", help="Simulation runtime limit in seconds", type=int)
    parser.add_argument("numberOfNodes", help="Number of nodes to test", type=int)
    parser.add_argument("-t", "--terminal", action="store_true", help="Opens a terminal in each node")
    parser.add_argument("-o", "--omnet", action="store_true", help="Starts OMNet++")
    parser.add_argument("-d", "--disks", action="store_true", help="Creates virtual disks")
    parser.add_argument("-u", "--dump", action="store_true", help="Creates dumps")
    parser.add_argument("-v", "--verbosity", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--protocol", type=str, help="Communication protocol", default="sockets")
    parser.add_argument("-m", "--membership", type=str, help="Membership control", default="local")

    settings_file = open("settings.json","r").read()
    settings = json.loads(settings_file)

    args = parser.parse_args()
    application = args.application
    protocol = args.protocol
    membership = args.membership
    time_scale = args.time_scale
    time_limit = args.time_limit
    number_of_nodes = args.numberOfNodes
    nodes_to_start = list(range(number_of_nodes))
    start_delay = 4
    #print(nodes_to_start)
    topology(args)

  except KeyboardInterrupt:
    print("Interrupted by ctrl+c")
