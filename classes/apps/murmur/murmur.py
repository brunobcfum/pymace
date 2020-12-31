#!/usr/bin/env python3

""" 
This is a scaffolded application. Implement any desired behaviour here.
Node start in INIT and run initiate to startup the communication graph
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import sys, json, traceback, time, threading, asyncio, random, pickle
from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt
from classes.network import network_sockets

class App():

  def __init__(self, Node, tag, time_scale, second):
    'Initializes the properties of the Node object'
    #### Genesis Common 
    random.seed(tag)
    self.Node = Node
    self.tag = tag
    self.tag_number = int(self.tag[5:])
    self.debug = False
    self.multiplier = time_scale
    self.scheduler = BackgroundScheduler()
    ### Application variables
    self.g_sample = 3
    self.state = "INIT"
    ##################### Constructor actions  #########################
    self._setup()

  ############# Public methods ########################

  def start(self):
    self.scheduler.start()
    self.tcp_interface = network_sockets.TcpInterface(self._packet_handler, debug=True, port=self.murmur_port, interface='')
    self.tcp_interface.start()
    self._auto_job()
    self._initiate()

  def shutdown(self):
    self.scheduler.shutdown()
    self.tcp_interface.shutdown()

  def toggleDebug(self):
    self.debug = not self.debug
    if (self.debug): 
      print("MyApp -> Debug mode set to on")
    elif (not self.debug): 
      print("MyApp -> Debug mode set to off")

  def printinfo(self):
    'Prints general information about the application'
    print()
    print("Application stats (MyApp)")
    print("Role: \t\t" + self.Node.role)
    print()

  ############# Private methods #######################

  def _pb_broadcast(self, value):
    print('pb_broadcast')
    for neighbour in self.Node.Membership.visible:
      self.tcp_interface.send(neighbour[0], value.encode(), 1)

  def _pb_deliver(self):
    pass

  def _initiate(self):
    #self.tcp_interface = network_sockets.TcpInterface(self._packet_handler, debug=True, port=self.murmur_port, interface='')
    pass

  def _packet_handler(self, payload, sender_ip):
    payload = pickle.loads(payload)
    msg_id = payload[0]
    encoded_payload = payload[1]
    print(msg_id)
    print(encoded_payload)
    #try:
    #    payload = pickle.loads(encoded_payload)
    #except:
    #    payload = json.loads(encoded_payload.decode())
    #pdu = payload[0]
    #if pdu == 1: # Got a proposal package
    #    self._handle_prop(payload, sender_ip)
    #    self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'PROPOSAL' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    #elif pdu == 2: #got an ACK package
    #    self._handle_prom(payload, sender_ip)
    #    self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    #elif pdu == 3: #got an ACK package
    #    self._handle_accept(payload, sender_ip)
    #    self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    #elif pdu == 4: #got an ACK package
    #    self._handle_accepted(payload, sender_ip)
    #    self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'ACCEPTED' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))

    #print(payload.decode())
    print(sender_ip)

  def _setup(self):
    settings_file = open("./classes/apps/murmur/settings.json","r").read()
    settings = json.loads(settings_file)
    self.sample = settings['sample']
    self.murmur_port = 55999

  def _auto_job(self):
    'Loads batch jobs from files. File must correspond to node name'
    try:
      jobs_file = open("./classes/apps/murmur/job_" + self.Node.tag + ".json","r").read()
      jobs_batch = json.loads(jobs_file)
      loop = asyncio.get_event_loop()
      for job in jobs_batch["jobs"]["oneshot"]:
        loop.create_task(self._auto_job_add(job['start'],job['type'],job['value']))
      loop.run_forever()
      loop.close()
    except:
      #print("No jobs batch for me")
      pass
      #traceback.print_exc()

  async def _auto_job_add(self, delay, jobtype, value):
    'Adds batch jobs to the scheduler'
    await asyncio.sleep(delay * self.Node.multiplier)
    self._add_job(jobtype, value)

  def _add_job(self, jobtype='help', value=None):
    'Adds manual jobs'
    if jobtype == 'help':
      try:
        self._printhelp()
      except:
        traceback.print_exc()

    if jobtype == 'broadcast':
      try:
        self._pb_broadcast(value)
      except:
        traceback.print_exc()

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()

  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for My Application")
    print()
    print("help                - Print this help message")
    print()
