#!/usr/bin/env python3

""" 
Node class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, random, struct, sys, json, traceback, zlib, fcntl, time
from apscheduler.schedulers.background import BackgroundScheduler

class App:

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        self.topology = [] #our visibble neighbours
        #### TIME STUFF ###############################################################################
        self.second = second
        ##################### END OF DEFAULT SETTINGS ###########################################################
        #self.scheduler.add_job(self.awake, 'interval', seconds=(self.sleeptime /1000), id='awake')
        #self.run()

    def run(self):
        #simulate reading sensor
        start = time.monotonic_ns()/1000000
        topologyPayload = json.dumps(["topodisc" , self.Node.tag, 0])
        #self.computational_energy += self.battery_drainer(self.modemSleep_current, start, self.sensor_energy)
        self.Node.Battery.sensor_reading_energy += self.Node.Battery.battery_drainer(self.Node.Battery.modemSleep_current, start, self.Node.Battery.sensor_energy)
        self.Node.Network.dispatch(topologyPayload, ttl=50)
        self.Node.Network.protocol_stats[0] += 1

    def receive(self, payload):
        try:
            payload = json.loads(payload)
        except:
            pass
        if type(payload) == list:
            if payload[0] == "topodisc":
                if payload[1] != seld.Node.tag:
                    payload[2] +=1
                    if len(self.topology) > 0: #list no empty, check if already there
                        not_there = True
                        for element in range(len(self.topology)):
                            if payload[1] == self.topology[element][1]: #if there...
                                pass
                                """  if payload[2]
                                not_there = 0
                                break """
                        if not_there:
                            self.topology.append([sender_ip, self.Node.simulation_seconds, 0])
                    else: #Empty neighbours list, add 
                        self.topology.append(payload)
                print(payload)

    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (WSNSensor)")
        print("current value: \t\t{0:5.2f}".format(self.value))
        print("vsleep time: \t\t{0:5.2f}".format(self.sleeptime/self.multiplier)+ " ms in virtual time")
        print("rsleep time: \t\t{0:5.2f}".format(self.sleeptime)+ " ms in real time")
        print()

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()

