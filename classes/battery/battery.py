#!/usr/bin/env python3

""" 
Battery class is part of a thesis work about distributed systems 

This is supposed to be used as a energy model for the system when / if needed
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, random, struct, sys, json, traceback, hashlib
import time
from apscheduler.schedulers.background import BackgroundScheduler

class Battery:

    def __init__(self, battery_mul, role, energy_model, full_energy = 50, voltage = 3.7):
        #### UPDATER ###############################################################################
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._updater, 'interval', seconds=1, id='updater')
        #### ELECTRICAL ###############################################################################
        self.voltage = voltage
        self.joules = 3600 # Wh to Joules
        self.battery_full_energy = full_energy * self.voltage * 3.6  # Joules
        self.battery_energy  = self.battery_full_energy * (battery_mul / 100) 
        self.battery_percent = self.battery_energy / self.battery_full_energy   
        #TODO: Add Battery drain option
        #self.deepSleep_current = energy_model['deepSleep_current'] 
        #self.modemSleep_current = energy_model['modemSleep_current'] 
        #self.awake_current = energy_model['awake_current'] 
        #self.rx_current = energy_model['rx_current'] 
        #self.tx_current = energy_model['tx_current'] 
        #self.sensor_energy = energy_model['sensor_energy'] #25mA / 3600s  -> this value in mAh every second
        #self.processor_multiplier = energy_model['multiplier']
        #### ENERGY ###############################################################################
        self.computational_energy = 0  #this accumulates the energy spent in calculations
        self.communication_energy = 0  #this accumulates the energy spent in communication
        self.sensor_reading_energy = 0  #this accumulates the energy spent in reading the sensor
        self.sleeping_energy = 0  #this accumulates the energy spent in sleeping
        self.tx_time = 30 / 3600000 # this time is in hours
        self.rx_time = 40 / 3600000 # this time is in hours
        #### SETUP ###############################################################################
        self.setup(battery_mul,role)

    def battery_drainer(self, current_A, start_time, fixed_Ah=0):
        finish = time.monotonic_ns()/1000000
        delta = (finish - start_time) * self.processor_multiplier # this is in millisenconds
        delta = (delta / 3600000) # this is in hours
        drain = ((delta * current_A) + fixed_Ah) * self.voltage * self.joules # Converting to Joules
        self.battery_energy = self.battery_energy - drain # this has to be in joules
        return drain

    def setup(self,battery_mul, role):
        settings_file = open("./classes/battery/settings.json","r").read()
        settings = json.loads(settings_file)
        self.voltage = settings['battery_voltage']
        self.battery_full_energy = settings['node_battery_mAh'] * self.voltage * 3.6  
        self.battery_energy  = self.battery_full_energy * (battery_mul / 100) 
        self.battery_percent = self.battery_energy / self.battery_full_energy 
        self.tx_time = settings['tx_time_ms'] / 3600000 
        self.rx_time = settings['rx_time_ms'] / 3600000 

    def _updater(self): #update battery level every sim second
        self.battery_percent = round((self.battery_energy / self.battery_full_energy) * 100)

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()

    def printinfo(self):
        'Prints general information about the node'
        print()
        print("Battery status")
        print()
        print("battery level: \t\t{0:5.2f} Joules".format(self.battery_energy))
        print("battery level: \t\t{0:5.2f} %".format(self.battery_percent))
        print("energy in comp:\t\t{0:8.5f} J".format(self.computational_energy))
        print("energy in comm:\t\t{0:8.5f} J".format(self.communication_energy))
        print("energy in sleep:\t{0:8.5f} J".format(self.sleeping_energy))
        print("energy in sensor:\t{0:8.5f} J".format(self.sensor_reading_energy))
        print()