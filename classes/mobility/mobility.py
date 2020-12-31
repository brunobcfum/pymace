#!/usr/bin/env python3

import pickle, socket, traceback, struct

class Mobility():
  def __init__ (self, Node):
    self.Node = Node
    self.name = "MOB"

  def start(self):
    self.Node.Bus.register_cb(self.event_callback)

  def shutdown(self):
    pass

  def event_callback(self, data):
    'This function is a callback for the bus'
    data = pickle.loads(data)
    try:
      if data[0] == 'BROADCAST' or data[0] == self.name:
        if data[1] == 'POSITION':
          data[0] = 'BROADCAST'
          self.emmit_to_host(data)
          #print(data[2])
    except:
      traceback.print_exc()
      pass

  def emmit_to_host(self, data):
    bus = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bus.settimeout(1)
    bus.connect("/tmp/genesis_main.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    bus.sendall(struct.pack('!I', length))
    bus.sendall(payload)
    bus.close()