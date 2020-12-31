#!/usr/bin/env python3

""" 
Prompt class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.8"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, struct, sys, traceback, threading, time, readline
from collections import deque

class Prompt:

    def __init__(self, node):
        self.lock=True
        self.history = deque([],100) #logbook of all messages received

    def prompt(self,node):
        'Simple command prompt * Maybe can be changed to use a prompt lib for better functionallity'
        try:
            while self.lock==True:
                inp = input(node.prompt_str)
                command = inp.split()
                self.history.append(command)
                try:
                    if (len(command))>=1:
                        if command[0] == 'help':
                            self._printhelp()
                        elif command[0] == 'clear':
                            print("\033c")
                            print()
                        elif command[0] == 'app':
                            node.Application._prompt(command)  
                        elif command[0] == 'visible':
                            try:
                                node.Membership.printvisible() 
                            except:
                                self.print_alert('Nothing to show')
                                pass
                        elif command[0] == 'info':
                            node.printinfo()
                        elif command[0] == 'member':
                            node.Membership._prompt(command)
                        elif command[0] == 'fault':
                            node.FaultDetector._prompt(command)
                        elif command[0] == 'net':
                            node.Network._prompt(command)
                        elif command[0] == 'quit':
                            node.lock = False
                            #node.shutdown()
                            sys.stdout.write('Quitting')
                            while True:
                                sys.stdout.write('.')
                                sys.stdout.flush()
                                time.sleep(1)
                        elif command[0] == 'debug':
                            node.Application.toggleDebug()
                            node.FaultDetector.toggleDebug()
                        elif command[0] == 'disable':
                            node.Application.disable()
                            node.FaultDetector.disable()
                        elif command[0] == 'enable':
                            node.Application.enable()
                            node.FaultDetector.enable()
                        else:
                            self.print_error("Invalid command!")
                        #elif command[0] == 'battery':
                        #    node.Battery.printinfo()    
                        #elif command[0] == 'scheduler':
                        #    try:
                        #        node.Membership.scheduler.print_jobs()
                        #    except:
                        #        self.print_alert("Not available with this network")
                        #elif command[0] == 'backlog':
                        #    try:
                        #        print(node.Membership.backlog)
                        #    except:
                        #        self.print_alert("Not available with this network")
                        #elif command[0] == 'msg':
                        #    node.Membership.print_msg_table()
                        #elif command[0] == 'topology':
                        #    try:
                        #        node.Membership.printTopology() 
                        #    except:
                        #        self.print_alert('Nothing to show')
                        #        pass
                except:
                    print('General error, probably the emulation have not started yet. When using CORE and BATMAN we need to wait 26s to start.')
        except:
            traceback.print_exc()
            node.lock = False
            self.print_alert("Exiting!")

    def _printhelp(self):
        'Prints help message'
        print()
        print("Distributed node")
        print()
        print("Interface commands: ")
        print()
        print("info      - Display general information about the node")
        print("net       - Display help from the network")
        print("member    - Display help from the membership control")
        print("fault     - Display help from the fault detector")
        print("app       - Display help from application")
        #print("visible   - Display the list of visible neighbours")
        print("debug     - Enable debug mode")
        print("clear     - Clear the display")
        print("help      - Diplay this help message")
        print("quit      - Exit the agent")
        print()

    def print_error(self,text):
        'Print error message with special format'
        print()
        print("\033[1;31;40m"+text+"  \n")
        print("\033[0;37;40m")

    def print_alert(self,text):
        'Print alert message with special format'
        print()
        print("\033[1;32;40m"+text+"  \n")
        print("\033[0;37;40m")

def print_error(text):
    'Print error message with special format'
    print()
    print("\033[1;31;40m"+text+"  \n")
    print("\033[0;37;40m")

def print_alert(text):
    'Print alert message with special format'
    print()
    print("\033[1;32;40m"+text+"  \n")
    print("\033[0;37;40m")

def print_info(text):
    'Print info message with special format'
    print()
    print("\033[1;34;40m"+text+"  \n")
    print("\033[0;37;40m")