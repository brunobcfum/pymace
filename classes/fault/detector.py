#!/usr/bin/env python3

""" 
Fault detector class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, struct, sys, json, traceback, zlib, fcntl, threading, time, pickle, distutils, random
from apscheduler.schedulers.background import BackgroundScheduler
from classes import tools
from classes.network import network_sockets

class FaultDetector():
  def __init__(self, Node):
    'Initializes the properties of the object'
    self.scheduler = BackgroundScheduler()
    #### NODE ###############################################################################
    self.Node = Node
    #### DETECTOR ##############################################################################
    self.running = []
    self.suspect = []
    self.faulty = []
    self.fault_callbacks = []
    self.leader = ''
    #### UTILITIES ############################################################################
    self.myip = ''
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()

  ############### Public methods ###########################
  def start(self):
    self.scheduler.start()

  def shutdown(self):
    self.scheduler.shutdown()

  def toggleDebug(self):
    'Toggle debug flag'
    self.debug = not self.debug
    if (self.debug): 
      print("Fault Detector -> Debug mode set to on")
    elif (not self.debug): 
      print("Fault Detector -> Debug mode set to off")

  def register_cb(self, cb):
    self.fault_callbacks.append(cb)

  def set_leader(self, leader):
    self.leader = leader

  def get_running(self):
    return self.running

  def get_suspect(self):
    return self.suspect

  def get_faulty(self):
    return self.faulty

  ############### Private methods ##########################

  def _setup(self):
    settings_file = open("./classes/fault/settings.json","r").read()
    settings = json.loads(settings_file)
    self.timeout = settings['timeout']
    self.pickup = settings['pickup']
    self.beacon_interval = settings['beacon_interval']
    self.fault_port = settings['port']
    self.echo_sample_size = settings['echo_sample_size']
    self.echo_threshold = settings['echo_threshold']

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self._printinfo()
      elif command[1] == 'running':
        self._print_running()
      elif command[1] == 'suspect':
        self._print_suspect()
      elif command[1] == 'faulty':
        self._print_faulty()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printinfo()

  def _printinfo(self):
    'Prints general information about the node'
    print()
    print("Fault Detector - Simple")
    print("Running nodes: " + str(len(self.running)))
    print("Suspect nodes: " + str(len(self.suspect)))
    print("Faulty nodes: " + str(len(self.faulty)))
    print("Echo sample size: " + str(self.echo_sample_size))
    print()

  def _printhelp(self):
    'Prints help about the application'
    print()
    print("Options for Fault Detector")
    print()
    print("help                - Print this help message")
    print("info                - Print overall information")
    print("runnning            - Print list or running")
    print("suspect             - Print list or suspect")
    print("faulty              - Print list or faulty")
    print()

  def _print_running(self):
    for node in self.running:
      print(node)

  def _print_suspect(self):
    for key in self.suspect:
      print(str(key) + " -> " + str(self.suspect[key]))

  def _print_faulty(self):
    for node in self.faulty:
      print(node)

class Simple(FaultDetector):
  def __init__(self, Node):
    'Initializes the properties of the object'
    random.seed('this is fault detector')
    self.scheduler = BackgroundScheduler()
    #### NODE ###############################################################################
    self.Node = Node
    #### DETECTOR ##############################################################################
    self.running = []
    self.suspect = {}
    self.faulty = []
    self.debug = False
    self.callbacks = []
    self.echo_subscribers = []
    self.fault_callbacks = []
    self.leader = ''
    #### UTILITIES ############################################################################
    self.myip = ''
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()
    self.fault_interface = network_sockets.TcpPersistent(self._fault_callback, debug=True, port=self.fault_port, interface='')
    self.fault_broadcast = network_sockets.TcpPersistent(self._fault_callback, debug=False, port=self.fault_port+1, interface='')
    self.scheduler.add_job(self._send_beacon, 'interval', seconds=self.beacon_interval, id='beacon')
    self.scheduler.add_job(self._refresh, 'interval', seconds=self.beacon_interval * 3, id='refresh')

  def start(self):
    self.fault_interface.start()
    self.fault_broadcast.start()
    self.scheduler.start()
    self._initialize()

  def shutdown(self):
    self.scheduler.shutdown()
    self.fault_interface.shutdown()
    self.fault_broadcast.shutdown()

  def disable(self):
    self.scheduler.shutdown()
    self.fault_interface.shutdown()
    self.fault_broadcast.shutdown()

  def enable(self):
    self.fault_interface = network_sockets.TcpPersistent(self._fault_callback, debug=False, port=self.fault_port, interface='')
    self.fault_broadcast = network_sockets.TcpPersistent(self._fault_callback, debug=False, port=self.fault_port+1, interface='')
    self.fault_interface.start()
    self.fault_broadcast.start()
    self.scheduler = BackgroundScheduler()
    self.scheduler.add_job(self._send_beacon, 'interval', seconds=self.beacon_interval, id='beacon')
    self.scheduler.add_job(self._refresh, 'interval', seconds=self.beacon_interval * 3, id='refresh')
    self.scheduler.start()

  ###########################################################################################################
 
  def _initialize(self):
    for node in self.Node.Membership.get_servers():
      if node[0] != self.Node.Network.myip:
        self.running.append([node[0],int(time.time()*1000)])
    buffer = self._pack_echo_subscribe()
    nodes = self.Node.Membership.get_servers()
    self.running = nodes[:]
    for node in nodes:
      if node[0] == self.Node.Network.myip:
        nodes.remove(node)
    echo_sample = random.sample(nodes, self.echo_sample_size)
    while len(echo_sample) > 0:
      for node in echo_sample:
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        response = self.fault_interface.send(node[0], buffer, msg_id)
        try:
          response = pickle.loads(response)
          response = pickle.loads(response[1])
          if response[0] == 'OK':
            echo_sample.remove(node)
        except:
          pass
          #traceback.print_exc()

  def _refresh(self):
    temp = list(self.running)
    tools.printxy(2,1,"R:" + str(len(self.running)) + " S:" + str(len(self.suspect)) + " F:" + str(len(self.faulty))+"  | ")

  def _suspect_thread(self, node):
    start = int(time.time()*1000)
    while int(time.time()*1000) - start < self.timeout:
      try:
        if len(self.suspect[node]) >= self.echo_sample_size // self.echo_threshold:
          #detected fault
          self._fault_detected(node)
          return
      except KeyError:
        return
      except:
        traceback.print_exc()
    #timeout, mode suspected to faulty. If it is ok, it will be fixed
    self._fault_detected(node)

  def _fault_detected(self, node):
    self.faulty.append(node)
    if node == self.leader:
      for cb in self.fault_callbacks:
        while True:
          if not any(node == x[0] for x in self.running):
            cb(node)
            break
    del(self.suspect[node])

  def _send_echo(self, faulty_node):
    buffer = self._pack_echo(faulty_node)
    msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
    echo_job = list(self.echo_subscribers)
    tries = 5
    while len(echo_job) > 0 and tries > 0:
      for node in echo_job:
        if (faulty_node != node) and (node not in self.faulty) and (node not in self.suspect):
          response = self.fault_interface.send(node, buffer, msg_id)
          try:
            response = pickle.loads(response)
            response = pickle.loads(response[1])
            if response[0] == 'OK':
              echo_job.remove(node)
          except:
            print(response)
            #traceback.print_exc()
        else:
          echo_job.remove(node)
      tries -= 1

  def _pack_echo(self, faulty_node):
    echo_pack = pickle.dumps([2, faulty_node, self.Node.tag])
    return echo_pack

  def _pack_echo_subscribe(self):
    echo_pack_subscribe = pickle.dumps([1, self.Node.tag])
    return echo_pack_subscribe

  def _pack_beacon(self):
    'Method for packing beacon'
    beacon_pack = pickle.dumps([0, self.Node.tag])
    return beacon_pack

  def _send_beacon(self):
    'Method for sending beacon'
    msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
    buffer = self._pack_beacon()
    for node in self.Node.Membership.get_servers():
      if node[0] != self.Node.Network.myip:
        beacont = threading.Thread(target=self._beacon_thread, args=(node, buffer, msg_id))
        beacont.start()

  def _beacon_thread(self, node, buffer, msg_id):
    start = time.monotonic_ns()
    response = self.fault_broadcast.send(node[0], buffer, msg_id, 1)
    end = time.monotonic_ns()
    total = (end - start) / 1000000 #miliseconds
    self.Node.Membership.update_node(node[0], total)
    try:
      response = pickle.loads(response)
    except:
      pass
    try:
      if response[0] == 'TIMEOUT':
        'We suspect a failure'
        if (node[0] not in self.suspect) and (node[0] not in self.faulty):
          self.suspect[node[0]] = []
          suspect_thread = threading.Thread(target=self._suspect_thread, args=(node[0],))
          suspect_thread.start()
        self._send_echo(node[0]) 
        self.running.remove(node)
      else:
        if node not in self.running:
          self.running.append(node)
        if node[0] in self.suspect:
          del(self.suspect[node[0]])
        if node[0] in self.faulty:
          self.faulty.remove(node[0])

    except:
      'not timeout'
      pass

  def _fault_callback(self, payload, sender_ip, connection):
    'Callback for when receiving a packet on fault detector'
    try:
      payload = pickle.loads(payload)
    except:
      if self.debug: print("Fault detector -> Received an empty or malformed payload")
    msg_id = payload[0]
    if payload[0] == 'bye':
      response = 'bye'
      length = len(pickle.dumps(response))
      connection.sendall(struct.pack('!I', length))
      connection.sendall(pickle.dumps(response))
      connection.close()
      return
    encoded_payload = payload[1]
    try:
      payload = pickle.loads(encoded_payload)
      pdu = payload[0]
    except:
      payload = json.loads(encoded_payload.decode())
      pdu = payload[0]
    if pdu == 0:
      if sender_ip != self.Node.Network.myip:
        #Beacon pdu do something
        response = pickle.dumps(['OK'])
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        self.fault_broadcast.respond(response, msg_id, connection)

    elif pdu == 1:
      #subscribe
      if sender_ip not in self.echo_subscribers:
        self.echo_subscribers.append(sender_ip)
      if sender_ip in self.echo_subscribers:
        self.fault_interface.respond(pickle.dumps(['OK']),tools.create_id(time.monotonic_ns(), self.Node.tag),connection)
      else:
        self.fault_interface.respond(pickle.dumps(['NOK']),tools.create_id(time.monotonic_ns(), self.Node.tag),connection)
    elif pdu == 2:
      #Echo
      suspect = payload[1]
      try:
        if suspect not in self.faulty:
          if suspect not in self.suspect:
            for node in self.running:
              if node[0] == sender_ip:
                self.running.remove(node)
            self.suspect[suspect] = [sender_ip]
            suspect_thread = threading.Thread(target=self._suspect_thread, args=(suspect,))
            suspect_thread.start()
          else:
            for node in self.running:
              if node[0] == sender_ip:
                self.running.remove(node)
            self.suspect[suspect].append(sender_ip)
        else:
          response = pickle.dumps(['OK'])
          msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
          self.fault_interface.respond(response, msg_id, connection)
          return
      except:
        traceback.print_exc()
        #self.suspect[suspect] = [sender_ip]
      try:  
        if sender_ip in self.suspect[suspect]:
          response = pickle.dumps(['OK'])
          msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
          self.fault_interface.respond(response, msg_id, connection)
        else:
          response = pickle.dumps(['NOK'])
          msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
          self.fault_interface.respond(response, msg_id, connection)
      except KeyError:
        response = pickle.dumps(['NOK'])
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        self.fault_interface.respond(response, msg_id, connection)
    else:
      if self.debug: print("Fault detector -> Got an invalid PDU on fault detector")


  def _printhelp(self):
    'Prints help about the application'
    print()
    print("Options for Fault Detector")
    print()
    print("help                - Print this help message")
    print("info                - Print overall information")
    print("runnning            - Print list or running")
    print("suspect             - Print list or suspect")
    print("faulty              - Print list or faulty")
    print("echo                - Print my echo subscribers")
    print()

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self._printinfo()
      elif command[1] == 'running':
        self._print_running()
      elif command[1] == 'suspect':
        self._print_suspect()
      elif command[1] == 'faulty':
        self._print_faulty()
      elif command[1] == 'echo':
        self._print_echo()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printinfo()

  def _print_echo(self):
    for node in self.echo_subscribers:
      print(node)

class Fast(FaultDetector):
  def __init__(self, Node):
    'Initializes the properties of the object'
    random.seed('this is fault detector')
    self.scheduler = BackgroundScheduler()
    #### NODE ###############################################################################
    self.Node = Node
    #### DETECTOR ##############################################################################
    self.running = []
    self.suspect = {}
    self.faulty = []
    self.debug = False
    self.callbacks = []
    self.echo_subscribers = []
    self.fault_callbacks = []
    self.leader = ''
    #### UTILITIES ############################################################################
    self.myip = ''
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()
    self.fault_interface = network_sockets.TcpPersistent(self._fault_callback, debug=False, port=self.fault_port, interface='')
    self.fault_broadcast = network_sockets.UdpInterface(self._fault_callback, debug=False, port=self.fault_port, interface='')
    self.scheduler.add_job(self._send_beacon, 'interval', seconds=self.beacon_interval, id='beacon')
    self.scheduler.add_job(self._refresh, 'interval', seconds=self.beacon_interval * 3, id='refresh')

  def start(self):
    self.fault_interface.start()
    self.fault_broadcast.start()
    self.scheduler.start()
    self._initialize()

  def shutdown(self):
    self.scheduler.shutdown()
    self.fault_interface.shutdown()
    self.fault_broadcast.shutdown()

  def disable(self):
    self.scheduler.shutdown()
    self.fault_interface.shutdown()
    self.fault_broadcast.shutdown()

  def enable(self):
    self.fault_interface = network_sockets.TcpPersistent(self._fault_callback, debug=False, port=self.fault_port, interface='')
    self.fault_broadcast = network_sockets.UdpInterface(self._fault_callback, debug=False, port=self.fault_port, interface='')
    self.fault_interface.start()
    self.fault_broadcast.start()
    self.scheduler = BackgroundScheduler()
    self.scheduler.add_job(self._send_beacon, 'interval', seconds=self.beacon_interval, id='beacon')
    self.scheduler.add_job(self._refresh, 'interval', seconds=self.beacon_interval * 1, id='refresh')
    self.scheduler.start()

  ###########################################################################################################
 
  def _initialize(self):
    for node in self.Node.Membership.get_servers():
      if node[0] != self.Node.Network.myip:
        self.running.append([node[0],int(time.time()*1000)])
    buffer = self._pack_echo_subscribe()
    nodes = self.Node.Membership.get_servers()
    for node in nodes:
      if node[0] == self.Node.Network.myip:
        nodes.remove(node)
    echo_sample = random.sample(nodes, self.echo_sample_size)
    while len(echo_sample) > 0:
      for node in echo_sample:
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        response = self.fault_interface.send(node[0], buffer, msg_id)
        try:
          response = pickle.loads(response)
          response = pickle.loads(response[1])
          if response[0] == 'OK':
            echo_sample.remove(node)
        except:
          traceback.print_exc()

  def _refresh(self):
    temp = list(self.running)
    for node in temp:
      if int(time.time()*1000) - node[1] > self.pickup:
        if node[0] not in self.suspect:
          self.suspect[node[0]] = []
        suspect_thread = threading.Thread(target=self._suspect_thread, args=(node[0],))
        suspect_thread.start()
        self.running.remove(node)
        threading.Thread(target=self._send_echo, args=(node[0],)).start()
        #self._send_echo(node[0])
      
    tools.printxy(2,1,"R:" + str(len(self.running)) + " S:" + str(len(self.suspect)) + " F:" + str(len(self.faulty))+"  | ")

  def _suspect_thread(self, node):
    start = int(time.time()*1000)
    while int(time.time()*1000) - start < self.timeout:
      try:
        if len(self.suspect[node]) >= self.echo_sample_size // self.echo_threshold:
          #detected fault
          self._fault_detected(node)
          return
      except KeyError:
        return
      except:
        traceback.print_exc()
    #timeout, mode suspected to faulty. If it is ok, it will be fixed
    self._fault_detected(node)

  def _fault_detected(self, node):
    self.faulty.append(node)
    if node == self.leader:
      for cb in self.fault_callbacks:
        cb(node)
    del(self.suspect[node])

  def _send_echo(self, faulty_node):
    buffer = self._pack_echo(faulty_node)
    msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
    echo_job = list(self.echo_subscribers)
    tries = 5
    while len(echo_job) > 0 and tries > 0:
      for node in echo_job:
        if (faulty_node != node) and (node not in self.faulty) and (node not in self.suspect):
          response = self.fault_interface.send(node, buffer, msg_id)
          try:
            response = pickle.loads(response)
            response = pickle.loads(response[1])
            if response[0] == 'OK':
              echo_job.remove(node)
          except:
            pass
            #print(response)
            #traceback.print_exc()
        else:
          echo_job.remove(node)
      tries -= 1

  def _pack_echo(self, faulty_node):
    echo_pack = pickle.dumps([2, faulty_node, self.Node.tag])
    return echo_pack

  def _pack_echo_subscribe(self):
    echo_pack_subscribe = pickle.dumps([1, self.Node.tag])
    return echo_pack_subscribe

  def _pack_beacon(self):
    'Method for packing beacon'
    beacon_pack = pickle.dumps([0, self.Node.tag])
    return beacon_pack

  def _send_beacon(self):
    'Method for sending beacon'
    msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
    buffer = self._pack_beacon()
    self.fault_broadcast.send(self.Node.Network.bcast_group, buffer, msg_id)

  def _fault_callback(self, payload, sender_ip, connection):
    'Callback for when receiving a packet on fault detector'
    try:
      payload = pickle.loads(payload)
    except:
      if self.debug: print("Fault detector -> Received an empty or malformed payload")
    msg_id = payload[0]
    if payload[0] == 'bye':
      response = 'bye'
      length = len(pickle.dumps(response))
      connection.sendall(struct.pack('!I', length))
      connection.sendall(pickle.dumps(response))
      connection.close()
      return
    encoded_payload = payload[1]
    try:
      payload = pickle.loads(encoded_payload)
      pdu = payload[0]
    except:
      payload = json.loads(encoded_payload.decode())
      pdu = payload[0]
    if pdu == 0:
      if sender_ip != self.Node.Network.myip:
        #Beacon pdu do something
        found = False
        for node in self.running:
          if sender_ip == node[0]:
            node[1] = int(time.time()*1000)
            found = True
        if not found:
          self.running.append([sender_ip, int(time.time()*1000)])
        if sender_ip in self.suspect:
          del(self.suspect[sender_ip])
        if sender_ip in self.faulty:
          self.faulty.remove(sender_ip)
    elif pdu == 1:
      #subscribe
      if sender_ip not in self.echo_subscribers:
        self.echo_subscribers.append(sender_ip)
      if sender_ip in self.echo_subscribers:
        self.fault_interface.respond(pickle.dumps(['OK']),tools.create_id(time.monotonic_ns(), self.Node.tag),connection)
      else:
        self.fault_interface.respond(pickle.dumps(['NOK']),tools.create_id(time.monotonic_ns(), self.Node.tag),connection)
    elif pdu == 2:
      #Echo
      suspect = payload[1]
      try:
        if suspect not in self.faulty:
          if suspect not in self.suspect:
            self.suspect[suspect] = [sender_ip]
          else:
            self.suspect[suspect].append(sender_ip)
        else:
          response = pickle.dumps(['OK'])
          msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
          self.fault_interface.respond(response, msg_id, connection)
          return
      except:
        traceback.print_exc()
        #self.suspect[suspect] = [sender_ip]
      if sender_ip in self.suspect[suspect]:
        response = pickle.dumps(['OK'])
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        self.fault_interface.respond(response, msg_id, connection)
      else:
        response = pickle.dumps(['NOK'])
        msg_id = tools.create_id(time.monotonic_ns(), self.Node.tag)
        self.fault_interface.respond(response, msg_id, connection)
    else:
      if self.debug: print("Fault detector -> Got an invalid PDU on fault detector")

  def _printhelp(self):
    'Prints help about the application'
    print()
    print("Options for Fault Detector")
    print()
    print("help                - Print this help message")
    print("info                - Print overall information")
    print("runnning            - Print list or running")
    print("suspect             - Print list or suspect")
    print("faulty              - Print list or faulty")
    print("echo                - Print my echo subscribers")
    print()

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self._printinfo()
      elif command[1] == 'running':
        self._print_running()
      elif command[1] == 'suspect':
        self._print_suspect()
      elif command[1] == 'faulty':
        self._print_faulty()
      elif command[1] == 'echo':
        self._print_echo()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printinfo()

  def _print_echo(self):
    for node in self.echo_subscribers:
      print(node)
      