#!/usr/bin/env python3

""" 
Main Application class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, struct, json, traceback, fcntl, time, threading

from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt
from ping3 import ping, verbose_ping
from struct import pack
from struct import unpack

class BaseApp:

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
        self.state = "IDLE" #current state
