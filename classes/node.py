#!/usr/bin/env python3

""" 
Node class - This is the main class, where all other objects are agregated
This should be a singleton - Only one node object per simulated node in the network
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.4"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, random, json, traceback, time
# My classes
from classes.battery import battery
from classes import tracer
# The network classes should include everything related to network that is not related to application level
from classes.network import network_sockets, network_pprz_udp, network_pprz_tcp
from classes.membership import membership_pprz_udp, membership_pprz_tcp, membership_sockets
from classes.bus import bus
from classes.fault import detector
from classes import pprz_interface
from classes.mobility import mobility
# Applications classes for each required application to be tested

from classes.apps.traffic import traffic
from classes.apps.blockchain import blockchain
from classes.apps.pprz import pprz, pprz_t
from classes.apps.paxos import paxos
from classes.apps.multipaxos import multipaxos
from classes.apps.rsm import rsm
from classes.apps.murmur import murmur
from classes.apps.dbrb import dbrb

class Node:
  def __init__(self, tag, energy_model, application, role, time_scale, initBattery, ip, net, membership='local', fault_detector='simple'):
    'Initializes the properties of the Node object'
    random.seed(tag)
    ##################### DEFAULT SETTINGS ####################################################################
    self.lock  = True # when this is false the simulation stops
    self.stop = False
    self.prompt_str = tag + "#>"
    #### Simulation specific ##################################################################################
    self.multiplier = time_scale #time multiplier for the simulator
    self.second = 1000 * self.multiplier #duration of a second in ms // this is the simulation second. If value is 1000, it means that one second is 1000 mili seconds
    #### NODE #################################################################################################
    self.role = role #are we a node or a ua?
    self.tag = tag #the name of the sensor
    self.load = 0 # processor load
    #### UTILITIES ############################################################################################
    self.simulation_seconds = 0 # this is the total time spent in the simulation time
    self.simulation_tick_seconds = 0 # this is the total time spent in real world time
    self.simulation_mseconds = 0 # this is the total time spent in the simulation time
    ##################### END OF DEFAULT SETTINGS #############################################################
    self._setup() #Try to get settings from file
    self.stats = [0]

    self.Battery = battery.Battery(initBattery, role, energy_model) #create battery object 
    self.Bus = bus.Bus(self) #create bus object

    ### TODO ####
    ### This should be done with a base network, expanded dependind if sockets or pprzlink
    if net.upper() == 'SOCKETS':
      self.Network = network_sockets.Network(self, ip) #create network object
    elif net.upper() == 'PPRZ_UDP':
      self.Network = network_pprz_udp.Network(self, ip) #create network object
    elif net.upper() == 'PPRZ_TCP':
      self.Network = network_pprz_tcp.Network(self, ip) #create network object
    else:
      print("invalid network protocol...using sockets")
      self.Network = network_sockets.Network(self, ip) #create network object

    ### TODO ####
    ### This should be done with a base membership, expanded dependind if sockets or pprzlink

    if (membership.upper() == 'LOCAL') and (net.upper() == 'SOCKETS'):
      self.Membership = membership_sockets.Local(self, ip) #create membership object
    elif (membership.upper() == 'GLOBAL') and (net.upper() == 'SOCKETS'):
      self.Membership = membership_sockets.Global(self, ip) #create membership object
    elif (membership.upper() == 'DBRB') and (net.upper() == 'SOCKETS'):
      self.Membership = membership_sockets.DBRB(self, ip) #create membership object


    if (fault_detector.upper() == 'SIMPLE'):
      self.FaultDetector = detector.Simple(self) #create fault detector
    elif (fault_detector.upper() == 'FAST'):
      self.FaultDetector = detector.Fast(self) #create fault detector

    ### TODO ####
    ### This should be done with a base app, the other apps inherit and expand. 

    if application.upper() == 'TRAFFIC':
      self.Application = traffic.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'BLOCKCHAIN':
      self.Application = blockchain.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'PPRZLINK':
      self.Application = pprz_t.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'PAXOS':
      self.Application = paxos.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'MULTIPAXOS':
      self.Application = multipaxos.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'RSM':
      self.Application = rsm.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'MURMUR':
      self.Application = murmur.App(self, self.tag, self.multiplier, self.second) #create network object
    elif application.upper() == 'DBRB':
      self.Application = dbrb.App(self, self.tag, self.multiplier, self.second) #create network object
    else:
      print("application not found...quitting")
      os._exit(1)


    #if pprz_interface:
    self.PprzInterface = pprz_interface.Interface(self)
    self.Mobility = mobility.Mobility(self)

    self.Tracer = tracer.Tracer(self, self.tag) #create tracer object 

  def printinfo(self):
    'Prints general information about the node'
    print()
    print("Node stats")
    print("nodename:\t\t"+self.tag)
    print("node role:\t\t"+self.role)
    print("elapsed time: \t\t" + str(self.simulation_seconds)+ " s in virtual time")
    #print("elapsed time: \t\t" + str(self.simulation_tick_seconds)+ " s in real time")
    print()
    self.Application.printinfo()

  def _setup(self):
    pass

  def start(self):
    time.sleep(27) #this is here only because of CORE
    self.Tracer.start()
    self.Bus.start()
    self.Battery.start()
    self.Membership.start()
    self.FaultDetector.start()
    self.Application.start()
    self.PprzInterface.start()
    self.Mobility.start()

  def shutdown(self):
    self.Mobility.shutdown()
    self.PprzInterface.shutdown()
    self.Application.shutdown()
    self.Membership.shutdown()
    self.FaultDetector.shutdown()
    self.Battery.shutdown()
    self.Bus.shutdown()
    self.Tracer.shutdown()
    self.stop = True


