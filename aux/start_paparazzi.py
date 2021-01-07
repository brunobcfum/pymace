#!/usr/bin/env python3 

""" 
Script for starting a paparazzi simulation
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import subprocess

command = "cd /opt/Programas/paparazzi/ && export PAPARAZZI_HOME=$PWD && export PAPARAZZI_SRC=$PWD &&"
command += " /opt/Programas/paparazzi/sw/simulator/pprzsim-launch -a ardrone2 -t nps &"
command += " /opt/Programas/paparazzi/sw/ground_segment/tmtc/server -n &" 
command += " /opt/Programas/paparazzi/sw/ground_segment/tmtc/link -udp -udp_broadcast -udp_port 56042 &" 
command += " /opt/Programas/paparazzi/sw/ground_segment/cockpit/gcs -layout large_left_col.xml"
node = subprocess.Popen([
            "bash",
            "-c",
            command], stdin=subprocess.PIPE, shell=False)
