#!/usr/bin/python3

__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, logging

class Auxiliar:
    """
    A class for stocking auxiliary methods

    Attributes
    ----------
    path : str
        the main path used for reports
    number_of_nodes : int
        the number of nodes to be considered

    Methods
    -------
    check_finished()
        check if all nodes finished the sessionS
    """
    def __init__(self, path, number_of_nodes):
        """
        Parameters
        ----------
        path : str
            the main path used for reports
        number_of_nodes : int
            the number of nodes to be considered
        """
        self.path = path
        self.nodesfinished = 0
        self.number_of_nodes = number_of_nodes

    def check_finished(self):
        """
        Check if nodes have finished the session

        Returns
        --------
        boolean - true when all nodes have finished

        """
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


if __name__ == "__main__":
    print("Please use pymace.py to run the emulation sessions")