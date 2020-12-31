#!/usr/bin/python3
#
""" 
Auxiliar functions for running simulations
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, logging

class Auxiliar:

    def __init__(self, path, number_of_nodes):
        self.path = path
        self.nodesfinished = 0
        self.number_of_nodes = number_of_nodes

    def check_finished(self):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            files.extend(filenames)
            break
        if len(files) >= self.number_of_nodes:
            #print('should be finished')
            return False
        if len(files) > self.nodesfinished:
            self.nodesfinished = len(files)
            logging.info(str(self.nodesfinished) + " nodes finished")
        return True

    def setupNamespaces():
        pass

    def startOmnet():
        pass

    def startGenesis():
        pass

if __name__ == "__main__":
    print("Please use genesis.py to run the simulation")