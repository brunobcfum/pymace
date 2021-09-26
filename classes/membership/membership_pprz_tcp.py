#!/usr/bin/env python3

""" 
Router class is part of a thesis work about distributed systems 
"""
__author__ = "Julie Morvan"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Julie Morvan"
__email__ = "julie.morvan999@hotmail.fr"

import socket, os, math, struct, sys, json, traceback, zlib, fcntl, threading, time, pickle
from apscheduler.schedulers.background import BackgroundScheduler

import pprzlink.tcp
import pprzlink.messages_xml_map as messages_xml_map
import pprzlink.message as message
from pprzlink.pprz_transport import PprzTransport

class Network():

    def __init__(self, Node, ip):
        'Initializes the properties of the Node object'
        self.scheduler = BackgroundScheduler()
        #### NODE ###############################################################################
        self.Node = Node
        self.NodeNumber = self.Node.tag_number
        self.visible = [] # our visible neighbours
        self.ever_visible = [] # our visible neighbours
        self.visibility_lost = []
        self.messages_created = [] # messages created by each node
        self.messages = []
        self.average = 0
        self.topology = [] 
        self.down_port = 57555 # UDP/TCP port
        self.up_port = 57444 # UDP port
        #### NETWORK ##############################################################################
        self.ip = ip 
        if self.ip == 'IPV4':
            self.bcast_group = '10.0.0.255' # broadcast ip address
        elif self.ip == 'IPV6':
            self.bcast_group = 'ff02::1'
        self.port = 56123 # UDP port 
        self.max_packet = 65535 # max packet size to listen
        #### UTILITIES ############################################################################
        self.protocol_stats = [0,0,0,0] # created, forwarded, delivered, discarded
        self.errors = [0,0,0]
        self.myip = ''
        #### Layer specific ####################################################################
        self.ttl = 16 #not used now
        self.fanout_max = 3
        self.mode = "NDM" #close neighbouhood discover mode
        self.packets = 0
        self.traffic = 0
        self.helloInterval = 0.2
        self.visible_timeout =  self.helloInterval * 5 #timeout when visible neighbours should be removed from list in s TODO make it setting
        ##################### END OF DEFAULT SETTINGS ###########################################################
        self._setup()
        self.listener_thread = threading.Thread(target=self._listener, args=())
        self.sender_thread = threading.Thread(target=self._sender, args=())
        self.scheduler.add_job(self._sendHello, 'interval', seconds=self.helloInterval, id='membership')
        self.scheduler.add_job(self._analyse_visible, 'interval', seconds=0.1, id='membership_analysis')
  
    ############### Public methods ###########################

    def start(self):
        self.listener_thread.start()
        self.sender_thread.start()
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()
        self.listener_thread.join(timeout=2)
        self.sender_thread.join(timeout=2)

    def printinfo(self):
        'Prints general information about the node'
        print()
        print("STUB - Using the OS routing and network")
        print("Broadcast IP: " + self.bcast_group)
        print()

    def printvisible(self):
        print("Visible neighbours at:" + str(self.Node.simulation_seconds) )
        print("===============================================================================")
        print("|Node ID   |Battery   |State   |Processor   |Memory   |Last seen   |Address")
        print("-------------------------------------------------------------------------------")
        for member in range(len(self.visible)): # print characteristic or the neighbours
            print("|" + self.visible[member][0] + "    |" + str(self.visible[member][1]) + "        |" + str(self.visible[member][2]) + "       |" + str(self.visible[member][3]) + "          |" + str(self.visible[member][4]) + "       |" + str(self.visible[member][5])+ "          |" + str(self.visible[member][6]))
        print("===============================================================================")
    
    ############### Private methods ##########################

    def _setup(self):
        settings_file = open("./classes/network/settings.json","r").read()
        settings = json.loads(settings_file)
        self.port = settings['networkPort']
        self.bcast_group = settings['ipv4bcast']
        self.helloInterval = settings['helloInterval']
        self.visible_timeout = settings['visibleTimeout']

    def _listener(self):
        'This method uses pprzlink to receive data.'
        #self.udp = pprzlink.udp.UdpMessagesInterface(
        self.tcp = pprzlink.tcp.TcpMessagesInterface(
            self._packet_handler,            # Callback
            uplink_port = self.up_port,      # Port we send messages to 
            downlink_port = self.down_port,  # Port used to receive messages
            verbose = False,
            interface_id = self.NodeNumber   # Numerical id of the interface
            )
        self.tcp.start()

    def _sender(self):
        'Uses pprzlink to send data'
        self.tcp_sender = pprzlink.tcp.TcpMessagesInterface(
                self._packet_handler,          # Callback function
                uplink_port = self.down_port,  # Port we send messages to 
                downlink_port = self.up_port,  # Port used to receive messages
                interface_id = self.NodeNumber # Numerical id of the interface
                )
        self.tcp_sender.start()

    def _packet_handler(self, sender, address, msg, length, receiver_id = None, component_id = None):
        'When a message of type genesis is received from neighbours this method unpacks and handles it'
        if msg.name == "HELLO":
            # Unpack the hello message
            node = b''.join(msg.get_field(0)).decode()
            battery = msg.get_field(1)
            state = msg.get_field(2)
            processor = msg.get_field(3)
            memory = msg.get_field(4)
            if (node != self.Node.fulltag):
                if len(self.visible) > 0: # List no empty, check if already there
                    not_there = 1
                    for element in range(len(self.visible)):
                        if node == self.visible[element][0]: # If already there: update
                            self.visible[element][5] = self.Node.simulation_seconds # refresh timestamp
                            self.visible[element][4] = memory # refresh memory
                            self.visible[element][3] = processor # refresh processor load
                            self.visible[element][2] = state # refresh state
                            self.visible[element][1] = battery # refresh battery
                            not_there = 0
                            break
                    if not_there: # If not there: add the node to the neighbours
                        self.visible.append([node, battery, state, processor, memory, self.Node.simulation_seconds, address[0]])
                else: # Empty neighbours list, add the node to the neighbours
                    self.visible.append([node, battery, state, processor, memory, self.Node.simulation_seconds, address[0]])
        else:
            print('not hello')

    def _createHello(self):
        _hello = message.PprzMessage('genesis', 'HELLO')
        _hello.set_value_by_name("nodeid", self.Node.fulltag) # associate values to the different fields of the HELLO message
        _hello.set_value_by_name("battery", 85)
        _hello.set_value_by_name("state", 1)
        _hello.set_value_by_name("cpu_load", 50)
        _hello.set_value_by_name("used_memory", 25)
        self.messages_created.append([hex(1),self.Node.simulation_seconds])
        return _hello
	
    def _sendHello(self):
        self.tcp_sender.send(self._createHello(), self.NodeNumber, self.bcast_group, 255) # send hello message to broadcast
        self._update_visible()
    
    def _setbcast(self, bcast):
        self.bcast_group = bcast

    def _update_visible(self):
        for member in range(len(self.visible)):
            if (self.Node.simulation_seconds - self.visible[member][5] > self.visible_timeout):
                del self.visible[member]
                break

    def _analyse_visible(self):
        for member in range(len(self.visible)):
            found = 0
            for ever_member in range(len(self.ever_visible)):
                if self.visible[member][0] == self.ever_visible[ever_member][0]:
                    found = 1
                    if self.ever_visible[ever_member][5] != 0:
                        #calculate absense
                        abesense = int(time.time() * 1000) - self.ever_visible[ever_member][5]
                        #store absense for report
                        self.visibility_lost.append([self.ever_visible[ever_member][0], abesense])
                        self.ever_visible[ever_member][5] = 0
            if found == 0:
                self.ever_visible.append([self.visible[member][0], 0, 0, 0, 0, 0,0])
        for ever_member in range(len(self.ever_visible)):
            found = 0
            for member in range(len(self.visible)):
                if self.visible[member][0] == self.ever_visible[ever_member][0]:
                    found = 1
            if found == 0:
                if self.ever_visible[ever_member][5] == 0:
                    self.ever_visible[ever_member][1] -= 1 # values to modify later (battery - 1)
                    self.ever_visible[ever_member][2] += 1 # (state + 1)
                    self.ever_visible[ever_member][3] += 1 # (processor load + 1)
                    self.ever_visible[ever_member][4] -= 1 # (memory - 1)
                    self.ever_visible[ever_member][5] = int(time.time() * 1000)

    def _print_ever(self):
        for member in self.ever_visible:
            print(member)

    def _prompt(self, command):
        if (len(command)) >= 2:
            if command[1] == 'help':
                self._printhelp()
            elif command[1] == 'info':
                self.printinfo()
            elif command[1] == 'bcast':
                self._setbcast(command[2])
            elif command[1] == 'ever':
                self._print_ever()
            elif command[1] == 'lost':
                for member in self.visibility_lost:
                    print(member)
            else:
                print("Invalid Option")
                self._printhelp()
        elif (len(command)) == 1:
            self.printinfo()  

    def _get_ip(self,iface = 'eth0'):
        'Gets IP address'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd = sock.fileno()
        SIOCGIFADDR = 0x8915
        ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
        try:
            res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
        except:
            traceback.print_exc()
            return None
        ip = struct.unpack('16sH2x4s8x', res)[2]
        return socket.inet_ntoa(ip)
