#!/usr/bin/env python3

""" 
Main script for the pymace framework
"""

__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.6"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import  sys, traceback, json, os, argparse, logging, shutil, time, subprocess, socket, auxiliar, threading, requests, pickle, struct

from classes.runner import runner
from classes.runner.termrunner import TERMRunner
from classes.runner.etcdrunner import ETCDRunner
from classes.runner.vmrunner import VMRunner
from classes.runner.dockerrunner import DockerRunner
from classes.runner.bus import Bus


def main():
  """
  Main function
  """
  try:
    if args.command.upper() == 'RUN':
      runner, repetitions = _setup()
      _start(runner, repetitions)
      _shutdown()
    elif args.command.upper() == 'NEW':
      _new(args.name)
    elif args.command.upper() == 'CLEAN':
      _clean()
    elif args.command.upper() == 'ETCD':
      runner = _setup_etcd()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'TERM':
      runner = _setup_term()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'VM':
      runner = _setup_vm()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'DOCKER':
      runner = _setup_docker()
      _start(runner, 1)
      _shutdown()
  except KeyboardInterrupt:
    logging.error("Interrupted by ctrl+c")
    os._exit(1)
  except SystemExit:
    logging.info("Quiting")
  except:
    logging.error("General error!")
    traceback.print_exc()

def _setup():
  """ 
  Method for reading the main settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used
  repetitions - The number of repetitions of the emulation session

  """
  emulation_file = open("./emulation.json","r").read()
  emulations = json.loads(emulation_file)
  for emulation in emulations['emulations']:
    repetitions = emulation['repetitions']
    scenario = emulation['scenario']
    tagbase = emulation['settings']['tagbase']
    application = emulation['settings']['application']
    time_scale = emulation['settings']['timeScale']
    time_limit = emulation['settings']['timeLimit']
    number_of_nodes = emulation['settings']['number_of_nodes']
    mobility = emulation['settings']['mobility']
    fault_detector = emulation['settings']['fault_detector']
    network = emulation['settings']['network']
    membership = emulation['settings']['membership']
    topology = emulation['settings']['topology']
    ip = emulation['settings']['ip']
    verboseLevel = emulation['settings']['verboseLevel']
    battery = emulation['settings']['battery']
    energy = emulation['settings']['energy']
    role = emulation['settings']['role']
    omnet = True if emulation['settings']['omnet'] == "True" else False
    core = True if emulation['settings']['core'] == "True" else False
    disks = True if emulation['settings']['disks'] == "True" else False
    dump = True if emulation['settings']['dump'] == "True" else False
    start_delay = emulation['settings']['start_delay']

    omnet_settings = emulations['omnet_settings']

    ### TODO: Move this to start
    runner = Runner(application, network, membership, time_scale, time_limit, number_of_nodes, omnet, core, disks, dump, start_delay, fault_detector, topology, omnet_settings,mobility)
    return runner, repetitions

def _setup_etcd():
  """ 
  Method for reading the ETCD settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used

  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  topology = emulation['etcd']['topology']
  number_of_nodes = emulation['etcd']['number_of_nodes']
  omnet = True if emulation['etcd']['omnet'] == "True" else False
  core = True if emulation['etcd']['core'] == "True" else False
  disks = True if emulation['etcd']['disks'] == "True" else False
  dump = True if emulation['etcd']['dump'] == "True" else False
  omnet_settings = emulation['omnet_settings']
  mobility = emulation['etcd']['mobility']
  ### TODO: Move this to start
  runner = ETCDRunner(number_of_nodes, omnet, core, disks, dump, topology, omnet_settings,mobility)
  return runner

def _setup_term():
  """ 
  Method for reading the terminal settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used


  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  topology = emulation['term']['topology']
  number_of_nodes = emulation['term']['number_of_nodes']
  omnet = True if emulation['term']['omnet'] == "True" else False
  core = True if emulation['term']['core'] == "True" else False
  disks = True if emulation['term']['disks'] == "True" else False
  dump = True if emulation['term']['dump'] == "True" else False
  omnet_settings = emulation['omnet_settings']
  mobility = emulation['term']['mobility']
  ### TODO: Move this to start
  runner = TERMRunner(number_of_nodes, omnet, core, disks, dump, topology, omnet_settings,mobility)
  return runner

def _setup_vm():
  """ 
  Method for reading the virtual machine settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used


  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  topology = emulation['vm']['topology']
  number_of_nodes = emulation['vm']['number_of_nodes']
  core = True if emulation['vm']['core'] == "True" else False
  disks = True if emulation['vm']['disks'] == "True" else False
  dump = True if emulation['vm']['dump'] == "True" else False
  mobility = emulation['vm']['mobility']
  ### TODO: Move this to start
  runner = VMRunner(number_of_nodes, core, disks, dump, topology, mobility)
  return runner

def _setup_docker():
  """ 
  Method for reading the docker settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used


  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  topology = emulation['docker']['topology']
  number_of_nodes = emulation['docker']['number_of_nodes']
  core = True if emulation['docker']['core'] == "True" else False
  dump = True if emulation['docker']['dump'] == "True" else False
  mobility = emulation['docker']['mobility']
  ### TODO: Move this to start
  runner = DockerRunner(number_of_nodes, core, dump, topology, mobility)
  return runner

def _start(runner, repetitions):
  """ 
  Method for starting the session

  Parameters
  ----------

  Returns
  --------

  """
  logging.info("Starting ...")
  for i in range(0,int(repetitions)):
    runner.start()

def _shutdown():
  """ 
  Method for shuting down the session

  Parameters
  ----------

  Returns
  --------

  """
  pass

def _clean():
  """ 
  Method for cleaning up

  Parameters
  ----------

  Returns
  --------

  """
  confirm = input("This will erase all old reports. Proceed? [y/N]")
  if confirm.upper() == "Y":
    logging.info("Cleaning all reports in reports folder.")
    try:
      shutil.rmtree("./reports")
      os.mkdir("reports")
      print(username)
      os.system("chown -R " + username + ":" + username + " ./reports")
    except:
      #traceback.print_exc()
      logging.error("Could not clean or recreate report folder")
      return
    logging.info("Done.")
  else:
    logging.info("Skiped.")

def _new(application):
  """ 
  Method for creating a new application

  Parameters
  ----------

  Returns
  --------

  """
  if application == None:
    logging.error("Application name required.")
  else:
    logging.info("Scafolding: " + str(application))
    try:
      os.mkdir("./classes/apps/" + str(application))
    except FileExistsError:
      logging.error("Another application with same name already exists.")
      pass
      #sys.exit(1)
    except:
      traceback.print_exc()
    
    try:
      files = []
      for (dirpath, dirnames, filenames) in os.walk(localdir + "/scaffold/"):
        files.extend(filenames)
      for file in files:
        #print(file)
        shutil.copyfile(localdir +"/scaffold/" + file,localdir + "/classes/apps/" + str(application) + "/" + file)
      shutil.move(localdir + "/classes/apps/" + str(application) + "/app.py", localdir + "/classes/apps/" + str(application) + "/" + str(application) + ".py")
    except:
      traceback.print_exc()


if __name__ == '__main__':  
  try:
    print("pymace v." + __version__)
    print("Framework for testing distributed algorithms in dynamic networks")
    print()

    parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')
    parser.add_argument("command", help="Main command to execute: run a configured emulation or create a new application.", choices=['run', 'new', 'clean', 'etcd', 'term', 'vm', 'docker'])
    parser.add_argument("name", help="New application name", nargs='?')
    parser.add_argument("-l", "--log", help="Log level", choices=['debug', 'info', 'warning', 'error', 'critical'],default="info")
    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper(), format='%(asctime)s -> [%(levelname)s] %(message)s')
    logging.Formatter('%(asctime)s -> [%(levelname)s] %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #logging.basicConfig(level='INFO')
    #logging.info("Starting")

    if os.geteuid() != 0:
      logging.error("This must be run as root or with sudo.")
      sys.exit(1)

    emulation_file = open("emulation.json","r").read()
    emulation = json.loads(emulation_file)
    username = emulation['username']

    localdir = os.path.dirname(os.path.abspath(__file__))
    #############################################################################
    main(); #call scheduler function
  except KeyboardInterrupt:
    logging.error("Interrupted by ctrl+c")
  except SystemExit:
    logging.info("Quiting")
  except:
    traceback.print_exc()
