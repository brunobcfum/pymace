""" 
Terminal Runner class
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"


import  traceback, os, logging, time, subprocess, threading


class Bus():

  def __init__(self):
    'Initializes the properties of the object'
    #### UTILITIES ############################################################################
    self.callbacks = []
    ##################### END OF DEFAULT SETTINGS ###########################################################

  ############### Public methods ###########################

  def start(self):
    self.state = 'ENABLED'
    self.bus_listener_thread = threading.Thread(target=self._start_event_listener, args=())
    self.bus_listener_thread.start()
    #self._start_event_listener()

  def shutdown(self):
    self._stop()
    self.bus_listener_thread.join(timeout = 2)

  def emmit(self, data):
    bus = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bus.settimeout(1)
    bus.connect("/tmp/pymace_main.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    bus.sendall(struct.pack('!I', length))
    bus.sendall(payload)
    bus.close()

  def register_cb(self, callback):
    self.callbacks.append(callback)
  
  def deregister_cb(self, callback):
    pass

  ############### Private methods ##########################
  def _stop(self):
    self.state = 'DISABLED'
    self.emmit('BYE')

  def _start_event_listener(self):
    #this section is a synchronizer so that all nodes can start ROUGHLY at the same time
    bus_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
      os.remove("/tmp/pymace_main.sock")
    except OSError:
      #traceback.print_exc()
      pass
    try:
      bus_socket.bind("/tmp/pymace_main.sock")
      bus_socket.listen(10000)
    except OSError:
      traceback.print_exc()
    except:
      traceback.print_exc()
    while self.state != "DISABLED":
      conn, addr = bus_socket.accept()
      try:
        lengthbuf = conn.recv(4)
        #print(lengthbuf)
        length, = struct.unpack('!I', lengthbuf)
        data = b''
        while length:
          newbuf = conn.recv(length)
          if not newbuf: return None
          data += newbuf
          length -= len(newbuf)
        #data = conn.recv(65500)
        #print(data)
        for cb in self.callbacks:
          cb(data)
        conn.close()
      except:
        pass
    bus_socket.close()

  def _printinfo(self):
    'Prints general information about the node'
    print()
    print("Network - Using the OS routing and network")
    print("Broadcast IP: " + self.bcast_group)
    print()