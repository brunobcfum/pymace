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

from classes.runner.runner import Runner
from classes.runner.termrunner import TERMRunner
from classes.runner.etcdrunner import ETCDRunner
from classes.runner.vmrunner import VMRunner
from classes.runner.armrunner import ARMRunner
from classes.runner.rasprunner import RaspRunner
from classes.runner.dockerrunner import DockerRunner
from classes.runner.riotrunner import RIOTRunner
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
    elif args.command.upper() == 'RASP':
      runner = _setup_rasp()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'ARM':
      runner = _setup_arm()
      _start(runner, 1)
      _shutdown()
    elif args.command.upper() == 'RIOT':
      runner = _setup_riot()
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
    ### TODO: Move this to start
    runner = Runner(emulation)
    return runner, repetitions

def _setup_riot():
  """ 
  Method for reading the RIOT settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used

  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  ### TODO: Move this to start
  runner = RIOTRunner(emulation)
  return runner

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
  ### TODO: Move this to start
  runner = ETCDRunner(emulation)
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
  ### TODO: Move this to start
  runner = TERMRunner(emulation)
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
  ### TODO: Move this to start
  runner = VMRunner(emulation)
  return runner

def _setup_rasp():
  """ 
  Method for reading the raspbian settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used


  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  ### TODO: Move this to start
  runner = RaspRunner(emulation)
  return runner

def _setup_arm():
  """ 
  Method for reading the arm vm settings

  Parameters
  ----------

  Returns
  --------
  runner - The runner that will be used


  """
  emulation_file = open("./emulation.json","r").read()
  emulation = json.loads(emulation_file)
  ### TODO: Move this to start
  runner = ARMRunner(emulation)
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
  ### TODO: Move this to start
  runner = DockerRunner(emulation)
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
    parser.add_argument("command", help="Main command to execute: run a configured emulation or create a new application.", choices=['run', 'new', 'clean', 'etcd', 'term', 'vm', 'docker', 'rasp', 'arm', 'riot'])
    parser.add_argument("name", help="New application name", nargs='?')
    parser.add_argument("-l", "--log", help="Log level", choices=['debug', 'info', 'warning', 'error', 'critical'],default="info")
    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper(), format='%(asctime)s -> [%(levelname)s] %(message)s')
    logging.Formatter('%(asctime)s -> [%(levelname)s] %(message)s')
    logger = logging.getLogger()
    #logger.setLevel(logging.INFO)
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
