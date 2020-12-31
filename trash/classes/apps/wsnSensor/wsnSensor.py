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

    def __init__(self, Node, tag, role, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        #### SENSOR ###############################################################################
        self.value = 0 # this is the sensor read value
        self.sleep_s = 15 + (random.random()*5) #seconds
        self.status = "AWAKE" #current status sleep/awake
        self.second = second
        self.sleeptime = self.sleep_s * self.second #time between sensor reads in ms
        ##################### END OF DEFAULT SETTINGS ###########################################################
        self.setup() #Try to get settings from file
        self.scheduler.add_job(self.awake, 'interval', [Node],  seconds=(self.sleeptime /1000), id='awake')

    def sensor_read(self, Node):
        #simulate reading sensor
        start = time.monotonic_ns()/1000000
        self.value = random.random()*100
        #self.computational_energy += self.battery_drainer(self.modemSleep_current, start, self.sensor_energy)
        Node.Battery.sensor_reading_energy += Node.Battery.battery_drainer(Node.Battery.modemSleep_current, start, Node.Battery.sensor_energy)
        Node.Network.dispatch(self.value)
        Node.Network.protocol_stats[0] += 1

    def awake(self, Node):
        #do my work
        self.status = "AWAKE"
        Node.Network.awake_callback()#tells Network that I'awake. In real hardware that would be an interrupt
        #if (self.role!="sink"):
        self.sensor_read(Node) #read new sensor value
        self.sleep(Node)

    def receive(self, payload):
        if self.Node.role == "sink":
            self.sink(payload)

    def sink(self, payload): #This should be in the application level, not here
        # This method does not use energy, only for simulation statistics
        if len(self.Node.Network.messages_delivered) > 0: 
            for element in range(len(self.Node.Network.messages_delivered)): #check if it's a new message
                if self.Node.Network.messages_delivered[element][0] == payload[1]: #we already delivered that one
                    self.Node.Network.messages_delivered[element][4] += 1 #increment counter
                    if (payload[8]>self.Node.Network.messages_delivered[element][5]): #calculate max and min hops
                        self.Node.Network.messages_delivered[element][5]=payload[8]
                    elif (payload[8]<self.Node.Network.messages_delivered[element][6]):
                        self.Node.Network.messages_delivered[element][6]=payload[8]
                    self.Node.Network.protocol_stats[2] += 1
                    not_delivered = False
                    break
                else: #new message
                    not_delivered = True
        else: #fresh list, add directly
            not_delivered = True
            #print("I'm a sink and got a message to dispatch")
        if not_delivered:
            self.Node.Network.messages_delivered.append([payload[1],payload[2],payload[4],self.Node.simulation_seconds,1,payload[8],payload[8]]) #add with counter 1
            self.Node.Network.protocol_stats[2] += 1
            self.Node.Network.tSinkCurrent = 0
          
    def sleep(self, Node):
        #sleep
        self.status = "SLEEP" 
        Node.Battery.sleeping_energy += Node.Battery.battery_drainer(0, 0 , Node.Battery.modemSleep_current * (self.sleep_s / 3600)) #using sleep = awake energy for now

    def setup(self):
        settings_file = open("settings.json","r").read()
        settings = json.loads(settings_file)
        self.sleep_s = settings['base_sleep_time_s'] + (random.random()*5) 
        self.sleeptime = self.sleep_s * self.second

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

