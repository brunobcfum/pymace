#!/usr/bin/env python3

""" 
Pprz application class is part of a thesis work about distributed systems 

This application is just to test pprzlink with genesis. Pprzlink should be created as a network application

"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, struct, json, traceback, fcntl, time, threading

import pprzlink.udp
import pprzlink.messages_xml_map as messages_xml_map
import pprzlink.message as message

from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt
from ping3 import ping, verbose_ping
from struct import pack
from struct import unpack

class App:

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.Node.role = "LISTENER"
        self.tag = tag
        self.NodeNumber = int(self.Node.tag[-1])
        self.debug = False
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        self.down_port = 56555 # UDP/TCP port
        self.up_port = 56444 # UDP port
        #### APP ################################################################################################
        self.udp_stat = [0,0]
        #### DRONE ##############################################################################################
        self.sequence = 0
        self.last_proposal_received = 0
        self.state = "IDLE" #current state
        ##################### END OF DEFAULT SETTINGS ###########################################################
        self._setup()
        self.udp_thread = threading.Thread(target=self._udp_listener, args=())
        self.udp_thread.start()
        self.udp_sender_thread = threading.Thread(target=self._udp_sender, args=())
        self.udp_sender_thread.start()

    ############### Public methods ###########################

    def start(self):
        'Called by main. Starts the application'
        self.scheduler.start()

    def shutdown(self):
        'Called by main. Stops the application'
        self.scheduler.shutdown()
        self.udp_thread.join(timeout = 2)

    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (PPRZLink)")
        print()
        print("Nothing implemented yet")
        print()

    def _printhelp(self):
        'Prints help information about the application'
        print()
        print("Options for (PPRZLink)")
        print()
        print("help                 - Print this help message")
        print("info                 - Print information regarding application")
        print("ping [ip] [pprz_id]  - Send a ping no a IP with timeout of 5")
        print()

    ############### Private methods ###########################

    def _setup(self):
        'Called by constructor. Finish the initial setup'
        settings_file = open("./classes/apps/pprz/settings.json","r").read()
        settings = json.loads(settings_file)
        self.up_port = int(settings['upPort'])
        self.down_port = int(settings['downPort'])
        #self.logfile = open(self.tag + "_target_report.csv","w")

    def _udp_listener(self):
        'This method opens a UDP socket to receive data.'
        self.udp = pprzlink.udp.UdpMessagesInterface(
                self._packet_handler,            # Callback function
                uplink_port = self.up_port,      # Port we send messages to 
                downlink_port = self.down_port,    # Port used to receive messages
                interface_id = self.NodeNumber # Numerical id of the interface (ac_id)
                )
        self.udp.start()

    def _udp_sender(self):
        'This method opens a UDP socket to send data.'
        self.udp_sender = pprzlink.udp.UdpMessagesInterface(
                self._packet_handler,          # Callback function
                uplink_port = self.down_port,    # Port we send messages to 
                downlink_port = self.up_port,  # Port used to receive messages
                interface_id = self.NodeNumber# Numerical id of the interface (ac_id)
                )
        self.udp_sender.start()

    def _packet_handler(self,sender,address,msg,length,receiver_id=None, component_id=None):
        # If it is a PING send a PONG, else print message information
        if msg.name=="PING":
            print("Received PING from %i %s [%d Bytes]" % (sender, address, length))
            pong = message.PprzMessage('telemetry', 'PONG')
            print ("Sending back %s to %s:%d (%d)" % (pong,address[0],address[1],sender))
            self.udp.send(pong, receiver_id, address[0], receiver = sender)
        else:
            print("Received message from %i %s [%d Bytes]: %s" % (sender, address, length, msg))

    def _ping(self, destinationIP, destinationNode):
        'Pings a node'
        # Create a PING message
        ping = message.PprzMessage('datalink', 'PING')

        self.udp_sender.send(
            ping,           # The message to send
            self.NodeNumber,   # Our numerical id
            destinationIP, # The IP address of the destination
            destinationNode  # The id of the destination
            )

    def _prompt(self, command):
        'Application command prompt options. Called from main prompt'
        if (len(command))>=2:
            if command[1] == 'help':
                self._printhelp()
            elif command[1] == 'ping':
                try:
                    self._ping(command[2], int(command[3]))
                except IndexError:
                    self._printhelp()
            elif command[1] == 'info':
                self.printinfo()
            else:
                print("Invalid Option")
                self._printhelp()
        elif (len(command))==1:
            self._printhelp()
