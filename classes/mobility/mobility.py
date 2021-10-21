#!/usr/bin/env python3

import pickle, socket, traceback, struct, threading
from apscheduler.schedulers.background import BackgroundScheduler
from classes.mobility.pymobility.models.mobility import *
from classes import pprz_interface

class Mobility():
  def __init__ (self, Node, model):
    self.Node = Node
    self.name = "MOB"
    self.mobility_model = model
    self.core_nodes = []
    self.scheduler = BackgroundScheduler()
    self.update_interval = 0.1
    #self.scheduler.add_job(self.mobility_update, 'interval', seconds=0.5, id='update')
    self.mobility_thread = threading.Thread(target=self.mobility_update, args=())
    self.x_dim = 220
    self.y_dim = 220
    self.velocity_lower = 0.1
    self.velocity_upper = 3
    self.lock = True

  def register_core_nodes(self, nodes):
    self.core_nodes = nodes
    self.configure_mobility()

  def configure_mobility(self):
    if self.mobility_model.upper() == 'RANDOM_WAYPOINT':
      self.mobility_object = random_waypoint(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ), velocity=(self.velocity_lower, self.velocity_upper), wt_max=1.0)
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'RANDOM_WALK':
      self.mobility_object = random_walk(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ), velocity=self.velocity_upper, distance=self.velocity_upper)
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'TRUNCATED_LEVY':
      self.mobility_object = truncated_levy_walk(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ))
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'HETEROGENEOUS_TRUNCATED_LEVY':
      self.mobility_object = heterogeneous_truncated_levy_walk(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ))
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'GAUSS_MARKOV':
      self.mobility_object = gauss_markov(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ))
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'RANDOM_DIRECTION':
      self.mobility_object = random_direction(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ), velocity=(self.velocity_lower, self.velocity_upper), wt_max=1.0)
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'REFERENCE_POINT_GROUP':
      self.mobility_object = reference_point_group(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ), velocity=(self.velocity_lower, self.velocity_upper))
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'TVC':
      self.mobility_object = tvc(len(self.core_nodes), dimensions=(self.x_dim , self.y_dim ), velocity=(self.velocity_lower, self.velocity_upper))
      self.mobility_thread.start()
    elif self.mobility_model.upper() == 'PAPARAZZI':
      self.PprzInterface = pprz_interface.Interface(None)
      self.PprzInterface.register_callback(self.paparazzi_mobility_update)
      self.PprzInterface.start()

  def mobility_update(self):
    while self.lock:
      positions = next(self.mobility_object)
      it = 0
      for node in self.core_nodes:
        node.setposition(positions[it][0],positions[it][1])
        it += 1

  def paparazzi_mobility_update(self, data):
    for node in self.core_nodes:
      if data[0]+1 == node.id:
       #print("=====================================MOBILITY==========================================")
        node.setposition(data[1], data[2])

  def start(self):
    try:
      #Not applicable to every type of emulation
      self.Node.Bus.register_cb(self.event_callback)
    except:
      pass

  def shutdown(self):
    #self.scheduler.shutdown()
    self.lock = False
    self.mobility_thread.join()

  def event_callback(self, data):
    'This function is a callback for the bus'
    data = pickle.loads(data)
    try:
      if data[0] == 'BROADCAST' or data[0] == self.name:
        if data[1] == 'POSITION':
          data[0] = 'BROADCAST'
          self.emmit_to_host(data)
    except:
      traceback.print_exc()
      pass

  def emmit_to_host(self, data):
    bus = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bus.settimeout(1)
    bus.connect("/tmp/pymace_main.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    bus.sendall(struct.pack('!I', length))
    bus.sendall(payload)
    bus.close()