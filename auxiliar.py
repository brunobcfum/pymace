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
    
    - **parameters**, **types**, **return** and **return types**::

          :param arg1: description
          :param arg2: description
          :type arg1: type description
          :type arg1: type description
          :return: return description
          :rtype: the return type description

    - and to provide sections such as **Example** using the double commas syntax::

          :Example:

          followed by a blank line !

      which appears as follow:

      :Example:

      followed by a blank line

    - Finally special sections such as **See Also**, **Warnings**, **Notes**
      use the sphinx syntax (*paragraph directives*)::

          .. seealso:: blabla
          .. warnings also:: blabla
          .. note:: blabla
          .. todo:: blabla

    .. note::
        There are many other Info fields but they may be redundant:
            * param, parameter, arg, argument, key, keyword: Description of a
              parameter.
            * type: Type of a parameter.
            * raises, raise, except, exception: That (and when) a specific
              exception is raised.
            * var, ivar, cvar: Description of a variable.
            * returns, return: Description of the return value.
            * rtype: Return type.

    .. note::
        There are many other directives such as versionadded, versionchanged,
        rubric, centered, ... See the sphinx documentation for more details.

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