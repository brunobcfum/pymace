#!/usr/bin/env python3

""" 
Tracer class is part of a thesis work about distributed systems 

This appliaction is a tracer that keeps logs that can be used later for analysis
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, struct, sys, traceback, time

class Tracer:

  def __init__(self, Node, tag):
    #Creates folder
    self.Node = Node
    self.Tag = tag
    self.simdir = str(time.localtime().tm_year) + "_" + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_mday) + "_" + str(time.localtime().tm_hour) + "_" + str(time.localtime().tm_min)
    self._create_folders(self.simdir)
    #self.start()

  def start(self):
    #Opens file
    self.tracefile = open("reports/" + self.simdir + "/" + "tracer/net_trace_" + self.Tag + ".csv","w")
    self.tracefile.write('time;id;direction;packet;size;sender/receiver\n')
    self.app_tracefile = open("reports/" + self.simdir + "/" + "tracer/app_trace_" + self.Tag + ".csv","w")
    self.app_tracefile.write('time;text\n')
    self.status_tracefile = open("reports/" + self.simdir + "/" + "tracer/status_trace_" + self.Tag + ".csv","w")


  def shutdown(self):
    #Closes file
    self.tracefile.flush()
    self.app_tracefile.flush()
    self.status_tracefile.flush()
    self.tracefile.close()
    self.app_tracefile.close()
    self.status_tracefile.close()


  def add_trace(self, data):
    #Add entry to file
    self.tracefile.write(str(int(time.time()*1000)) + ';' + data + '\n')

  def add_app_trace(self, data):
    #Add entry to file
    self.app_tracefile.write(str(int(time.time()*1000)) + ';' + data + '\n')

  def add_status_trace(self, status):
    #Add entry to file
    self.status_tracefile.write(status + '\n')

  def _create_folders(self, simdir):
    try:
      os.mkdir("reports/" + simdir)
      #print("Tracer folder created.")
    except FileExistsError:
      pass
      #print("Tracer folder created.")
    except:
      traceback.print_exc()

    try:
      os.mkdir("reports/" + simdir + "/tracer")
      #print("Tracer folder created.")
    except FileExistsError:
      pass
      #print("Tracer folder created.")
    except:
      traceback.print_exc()
      sys.exit(1)

