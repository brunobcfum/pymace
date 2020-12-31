#!/usr/bin/python3
#
""" 
Main scenario runner is part of a thesis on distributed systems
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.4"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import threading, sys, time, random, os, traceback, json, shutil, argparse, subprocess, signal
import rest, socket, auxiliar

def topology(args):
        
    #start omnet
    if args.omnet:
        omnet(args, settings)
    
    #create disks
    if args.disks:
        createDisks(number_of_nodes)

    #start terminals
    if args.terminal:
        terminal(args)

def omnet(args, settings):
    #this opens a terminal windows with omnet running
    omnet = subprocess.Popen([
                                #"xfce4-terminal",
                                #"--title=OMNet++",
                                #"--hold",
                                "xterm",
                                #"-xrm 'XTerm.vt100.allowTitleOps: false'",
                                #"-T omnet",
                                "-hold",
                                "-e",
                                #"ls"])
                                "inet -u Cmdenv -n " + settings['omnet_include_path'] + " " + settings['ini_file']]
                                , stdin=subprocess.PIPE, shell=False)

def terminal(args):
    #open extra terminal windows in each node
    for i in range(0,args.numberOfNodes):
        command = "xterm -xrm 'XTerm.vt100.allowTitleOps: false' -T client" + str(i) + " &"
        node = subprocess.Popen([
                                    "ip",
                                    "netns",
                                    "exec",
                                    "drone" + str(i),
                                    "bash",
                                    "-c",
                                    command])
def createDisks(number_of_nodes):
    #create virtual disk for each node 
    for i in range(0,number_of_nodes):
        command = "mount -t tmpfs -o size=512m tmpfs /mnt/genesis/drone" + str(i) + " &"
        node = subprocess.Popen([
                                    "bash",
                                    "-c",
                                    command])

if __name__ == "__main__":
    try:
        print("This is a testing agent for dist. sched. in dynamic networks")
        print("genesis mobility v." + __version__)
        print()

        parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')


        parser.add_argument("numberOfNodes", help="Number of nodes to test", type=int)
        parser.add_argument("-t", "--terminal", action="store_true", help="Opens a terminal in each node")
        parser.add_argument("-o", "--omnet", action="store_true", help="Starts OMNet++")
        parser.add_argument("-d", "--disks", action="store_true", help="Creates virtual disks")
        parser.add_argument("-v", "--verbosity", action="store_true", help="Verbose output")
        parser.add_argument("-p", "--protocol", type=str, help="Communication protocol", default="sockets")

        settings_file = open("settings.json","r").read()
        settings = json.loads(settings_file)

        args = parser.parse_args()
        protocol = args.protocol
        number_of_nodes = args.numberOfNodes
        #print(args)
        topology(args)

    except KeyboardInterrupt:
        print("Interrupted by ctrl+c")
        #logger.logfile.close()


