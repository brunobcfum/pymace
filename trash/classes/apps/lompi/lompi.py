#!/usr/bin/env python3

""" 
Paxos applications class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, random, struct, sys, json, traceback, zlib, fcntl, time, psutil, threading
from apscheduler.schedulers.background import BackgroundScheduler

class App:

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        self.bcast_group = '10.0.0.255' #broadcast ip address
        self.port = 56555 # UDP port
        self.max_packet = 65535 #max packet size to listen
        #### SENSOR ###############################################################################
        self.value = 0 # this is the sensor read value
        self.sleep_s = 15 + (random.random()*5) #seconds
        self.state = "INIT" #current state
        self.second = second
        self.sleeptime = self.sleep_s * self.second #time between sensor reads in ms
        ##################### END OF DEFAULT SETTINGS ###########################################################
        self.t2 = threading.Thread(target=self._listener, args=())
        self.t2.start()
        #self._setup() #Try to get settings from file
        #self.scheduler.add_job(self.awake, 'interval', [Node],  seconds=(self.sleeptime /1000), id='awake')

    def _listener(self):
        'This method opens a UDP socket to receive data. It runs in infinite loop as long as the node is up'
        addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
        listen_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM) #UDP
        port = self.port + int(self.Node.tag[-1])
        listen_socket.bind(('', self.port))
        self.myip = self._get_ip('enp8s0')
        while self.Node.lock: #this infinity loop handles the received packets
            payload, sender = listen_socket.recvfrom(self.max_packet)
            payload = json.loads(payload.decode())
            sender_ip = str(sender[0])
            self.packets += 1
            self._packet_handler(payload, sender_ip)
        listen_socket.close()

    def _setup(self):
        settings_file = open("settings.json","r").read()
        settings = json.loads(settings_file)

    def _get_ip(self,iface = 'eth0'):
        'This should be in routing layer'
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

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()


    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (LOMPI)")
        print("CPU: \t\t{0:5.2f}".format(psutil.cpu_percent()))
        print("Memory: \t" + str(psutil.virtual_memory()[2]))
        print()

