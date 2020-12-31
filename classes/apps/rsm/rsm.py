#!/usr/bin/env python3

""" 
Paxos applications class is part of a thesis work about distributed systems
Possible states: WRITE
Read from leader
This is a simple yet fairly complete implementation of a read one write all algorithm.
It uses a consensus algorithm to ensure secyrity guarantees. For now it is implemented 
with multipaxos, but since it is modular, other algorithms can be implemented.
It can work in cooperation with a failure detection algorithm to coordinate leader election.
The reason for using leaders is due to the fact that Paxos can deal well with concurrent
requests which hurts the termination property. For that, ranked leader election was implemented
and always the nodes with higher ID will eventually be elected. To ensure consistency during eventual partitions,
Paxos is also used during leader election.
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, sys, json, traceback, zlib, fcntl, time, threading, pickle, asyncio, os, struct
from apscheduler.schedulers.background import BackgroundScheduler
from classes.network import network_sockets
from classes import prompt
from classes.apps.paxos import paxos
from classes.apps.multipaxos import multipaxos
from collections import deque

class App:

  def __init__(self, Node, tag, time_scale, second):
    'Initializes the properties of the application object'
    random.seed(tag)
    self.tag = tag
    self.Node = Node
    self.name = "RSM"
    self.multiplier = time_scale
    self.scheduler = BackgroundScheduler()
    self.max_packet = 65535 #max packet size to listen
    self.debug = False
    #### NODE ###############################################################################
    self.value = 0 # this is the sensor read value
    self.state = "INIT" #current state
    self.second = second
    #self.job_queue = deque([],maxlen=10000) #create a job queue
    self.job_queue = []
    self.job_hist = []
    self.servers = []
    self.leaders = []
    self.storage = {}
    self.storage['teste'] = 1337
    self.job_timeout = 10
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()
    self.consensus = multipaxos.App(self.Node, tag, self.multiplier, self.second)
    self.ranking = self.consensus.tag_number
    self.client_interface = network_sockets.TcpPersistent(self._packet_handler, debug=False, port=self.client_port, interface='')
    self.rsm_interface = network_sockets.TcpPersistent(self._packet_handler, debug=False, port=self.rsm_port, interface='')
    #self.scheduler.add_job(self._check_jobs, 'interval', seconds=self.job_timeout / 2, id='jobs')
    self.scheduler.add_job(self._check_servers, 'interval', seconds=2, id='servers')
    self.starttd = threading.Thread(target=self._first_leader_thread, args=())

  def _check_jobs(self):
    for job in self.job_queue:
      if int(time.time()) - job[3] > self.job_timeout:
        response = ['TIMEOUT']
        length = len(pickle.dumps(response))
        try: 
          job[1].sendall(struct.pack('!I', length))
          job[1].sendall(pickle.dumps(response))
        except:
          pass
        finally:
          job[2] = 'TIMEOUT'
          self.job_hist.append(job)
          self.job_queue.remove(job)

  def start(self):
    'Starts the execution of the application'
    self.Node.Bus.register_cb(self.event_callback)
    self.Node.FaultDetector.register_cb(self._fault_callback)
    self.scheduler.start()
    self.client_interface.start()
    self.rsm_interface.start()
    self.rsmlog_start()
    self.consensus.rsm_start()
    self.starttd.start()
    self._auto_job()

  def shutdown(self):
    'Shutdown applicaiton'
    self.rsmlog_shutdown()
    self.client_interface.shutdown()
    self.rsm_interface.shutdown()
    self.consensus.shutdown()
    self.scheduler.shutdown()

  def disable(self):
    'Disable the node for tests'
    self.previous_state = self.get_state()
    self.set_state('DISABLED')
    self.consensus.disable()
    self.client_interface.shutdown()
    self.rsm_interface.shutdown()

  def enable(self):
    'Enable disabled node'
    if self.state == 'DISABLED':
      self.set_state('ENABLED')
      self.consensus.enable()
      self.client_interface = network_sockets.TcpPersistent(self._packet_handler, debug=False, port=self.client_port, interface='')
      self.client_interface.start()
      self.rsm_interface = network_sockets.TcpPersistent(self._packet_handler, debug=False, port=self.rsm_port, interface='')
      self.rsm_interface.start()
      self.set_state(self.previous_state)
    else:
      print("Node not disabled. Skiping...")

  def read(self, key):
    'Function that reads stored key'
    try:
      value = self.storage[key]
      return [1, value]
    except:
      return [0]

  def write(self, key, value, connection, jobid):
    'Write key/value on my self or on leader'
    lock = threading.Lock()
    if jobid == None:
      jobid = hex(self._create_id())
    lock.acquire()
    self.job_queue.append([jobid, connection, '', int(time.time())])
    lock.release()
    if self._am_i_leader():
      self.request_consensus(['WRITE', key, value, jobid])
    else:
      response = self.ask_to_leader(['WRITE', key, value, jobid])
      if response[0] == 'FAIL':
        for job in self.job_queue:
          if job[0] == jobid:
            job[2] = 'FAILED'
        try:
          length = len(pickle.dumps(response))
          connection.sendall(struct.pack('!I', length))
          connection.sendall(pickle.dumps(response))
          connection.close()
        except:
          traceback.print_exc()

  def ask_to_leader(self, payload):
    'Forwards the request to the leader, if it exists'
    bytes_to_send = pickle.dumps(payload)
    if self.who_is_leader() != '':
      self.rsm_interface.send(self.who_is_leader(), bytes_to_send, self._create_id())
      self.Node.Tracer.add_trace('LEADER_FWD'+';'+'SEND' + ';' + str('WRITE') + ';' + str(sys.getsizeof(payload)) + ';' + str(self.who_is_leader()))
      return ['OK']
    else:
      return ['FAIL']
  
  def request_consensus(self, proposal):
    'Request consensus from the consensus class'
    self.consensus.propose(proposal)

  def proposal_callback(self, response):
    'Deprecated'
    if self.debug: print("callback -> " + str(response))

  def who_is_leader(self):
    'Get the leader from consensus class'
    return self.consensus.get_leader()

  def request_consensus_last_state(self):
    'Request from consensus object the last state'
    last_state = self.consensus.last_state()
    if last_state == None:
      #initial state
      print("Paxos hasn't confirmed any new state")
    else:
      print("Paxos last confirmed state is: " + str(last_state))

  def set_state(self, state):
    'Change current state'
    self.state = state

  def get_state(self):
    'Get current state'
    return self.state
  
  def toggleDebug(self):
    'Toggle debug flag'
    self.debug = not self.debug
    if (self.debug): 
      print("RSM -> Debug mode set to on")
    elif (not self.debug): 
      print("RSM -> Debug mode set to off")
    self.consensus.toggleDebug()

  def event_callback(self, data):
    'This function is a callback for the bus'
    data = pickle.loads(data)
    lock = threading.Lock()
    try:
      if data[0] == 'BROADCAST' or data[0] == self.name:
        if data[1] == 'COMMIT':
          if data[2][0] == 'WRITE':
            if self.debug: print('Event callback -> ' + 'Received WRITE from BUS')
            lock.acquire()
            self.storage[data[2][1]] = data[2][2]
            for job in self.job_queue:
              if job[0] == data[2][3]:
                connection = job[1]
                length = len(pickle.dumps(['OK']))
                try:
                  connection.sendall(struct.pack('!I', length))
                  connection.sendall(pickle.dumps(['OK']))
                  connection.close()
                  job[2] = 'FINISHED'
                  self.job_hist.append(job)
                  self.job_queue.remove(job)
                except:
                  print("event_callback -> could not send ok back to client")
                  pass
            lock.release()
            #print(data)
          elif data[2][0] == 'LEADER':
            if data[2][1] == self.tag:
              self._set_as_leader()
              #TODO: can't rely on this
              self.emmit_leader_bus(int(self.tag[5:]))
            else:
              if self.consensus.get_role() == 'LEADER':
                self._set_as_follower()
        elif data[1] == 'BCAST_LEADER':
          self.emmit_leader_bus(int(self.tag[5:]))
    except:
      print(data)
      traceback.print_exc()

  def rsmlog_start(self):
    'Starts tracing for application'
    self.rsm_logfile = open("reports/" + self.Node.Tracer.simdir + "/" + "tracer/rsm_log_" + self.tag + ".csv","w")

  def rsmlog_shutdown(self):
    'Stops tracing for application'
    for entry in self.consensus.consensus_log:
      if entry != None:
        self.rsm_logfile.write(str(self.consensus.consensus_log.index(entry)) + ';' + str(entry) + '\n')
    self.rsm_logfile.flush()
    self.rsm_logfile.close()


  ###############################################################################################


  def emmit_leader_bus(self, leader):
    self.emmit_to_host(['BROADCAST', 'LEADER', leader])

  def emmit_to_host(self, data):
    bus = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bus.settimeout(1)
    bus.connect("/tmp/genesis_main.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    bus.sendall(struct.pack('!I', length))
    bus.sendall(payload)
    bus.close()

  def _setup(self):
    'Initial setup'
    self.myip = self.Node.Network.myip
    settings_file = open("./classes/apps/rsm/settings.json","r").read()
    settings = json.loads(settings_file)
    self.client_port = settings['clientPort']
    self.rsm_port = settings['rsmPort']
    self.max_packet = settings['maxPacket']
    self.network = settings['network']
    self.bcast_group = settings['network'] + "255"

  def _am_i_leader(self):
    'Check if I am the leader'
    if self.Node.Network.myip == self.who_is_leader():
      return True
    return False
   
  def _check_servers(self):
    'Creating my quorum based in the membership class, which is an implementation of a membership protocol'
    self.servers = []
    for node in self.Node.Membership.get_servers():
      if node[0] != self.myip:
        self.servers.append(node[0])

  def _auto_job(self):
    'Loads batch jobs from files. File must correspond to node name'
    try:
      jobs_file = open("./classes/apps/rsm/job_" + self.Node.tag + ".json","r").read()
      jobs_batch = json.loads(jobs_file)
      if len(jobs_batch["jobs"]) == 0:
        return
      loop = asyncio.get_event_loop()
      for job in jobs_batch["jobs"]:
        loop.create_task(self._auto_job_add(job['start'],job['type'],job['key'],job['value']))
      loop.run_forever()
      loop.close()
    except:
      #traceback.print_exc()
      #print("No jobs batch for me")
      pass

  async def _auto_job_add(self, delay, jobtype, key, value):
    'Adds batch jobs to the scheduler'
    await asyncio.sleep(delay * self.Node.multiplier)
    self._add_job(jobtype, key, value)

  def _add_job(self, jobtype, key, value):
    'Run the auto jobs'
    if jobtype.upper() == 'LEADER':
      try:
        self._set_as_leader()
      except:
        traceback.print_exc()
    elif jobtype.upper() == 'WRITE':
      try:
        self.request_consensus([jobtype.upper(),key, value])
      except:
        traceback.print_exc()
    elif jobtype.upper() == 'DISABLE':
      try:
        self.disable()
      except:
        traceback.print_exc()
    elif jobtype.upper() == 'ENABLE':
      try:
        self.enable()
      except:
        traceback.print_exc()

  def _read(self, key):
    'Tries to read from local storage'
    try:
      value = self.storage[key]
    except KeyError:
      return ['NOK','KeyError']
    return ['OK',value]

  def _create_id(self):
    'Create an CRC32 unique ID'
    return zlib.crc32((str(int(time.time()*1000))+ str(self.tag) + str(random.randint(0,10000))).encode())

  def _first_leader_thread(self):
    start = int(time.time())
    while int(time.time()) - start < 2:
      time.sleep(1)
    if self._check_if_i_will_leade():
      if self.debug: print("RSM-> I will leade")
      self.consensus.propose(['LEADER', self.tag], leader_round=True)
    return

  def _fault_callback(self, node):
    'Callback for when a fault is detected on the leader'
    if self.consensus.get_leader() == node:    #double check
      if self.debug: print("RSM-> leader failed")
      self.consensus.leader_failed()
      if self._check_if_i_will_leade():
        if self.debug: print("RSM-> I will leade")
        self.consensus.propose(['LEADER', self.tag], leader_round=True)

  def _check_if_i_will_leade(self):
    running = self.Node.FaultDetector.get_running()
    ill_be_leader = True
    for server in running:
      rank = int(server[0].split(".")[3]) - 1
      #print(rank)
      if rank > self.ranking:
        ill_be_leader = False
    return ill_be_leader

  def _leader_election(self):
    'Run leader election round on consensus object'
    self.consensus.election_round()

  def _set_as_leader(self):
    'Request this node to be a leader'
    #self.consensus.propose(['LEADER', self.tag], leader_round=True)
    self.consensus.set_role('LEADER')
    self.Node.FaultDetector.set_leader(self.Node.Network.myip)

  def _set_as_follower(self):
    'Request this node to be a follower'
    self.consensus.set_role('FOLLOWER')

  def _packet_handler(self, payload, sender_ip, connection):
    'This function handles as a callback the received packet'
    'First layer always pickle, second layer can be pickle or json'
    self.Node.stats[0] += 1
    try:
      payload = pickle.loads(payload)
    except:
      print("empty payload?")
      print(payload)
    msg_id = payload[0]
    #self.job_queue.append([msg_id, connection, ''])
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
      command = payload[0]
    except:
      payload = json.loads(encoded_payload.decode())
      command = payload[0]

    self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + str(command) + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    response = ''
    
    if command == 'READ':
      #check if message was mine or coming from other node
      key = payload[1]
      start=time.monotonic_ns()
      #print('Client wants to READ ' + str(key))
      if self._am_i_leader():
        #print("I am leader")
        response = self._read(key)
        length = len(pickle.dumps(response))
        connection.sendall(struct.pack('!I', length))
        connection.sendall(pickle.dumps(response))
        connection.close()
        return
      else:
        #ask the leader
        bytes_to_send = pickle.dumps(payload)
        leader = self.who_is_leader()
        if leader == '':
          response = 'FAIL'
          length = len(pickle.dumps(response))
          connection.sendall(struct.pack('!I', length))
          connection.sendall(pickle.dumps(response))
          connection.close()
          return
        else:
          start=time.monotonic_ns()
          response = self.rsm_interface.send(self.who_is_leader(), bytes_to_send, self._create_id())
          end = time.monotonic_ns()
          print("read took:" +str((end-start)/1000000))
          self.Node.Tracer.add_trace(msg_id+';'+'SEND' + ';' + str(command) + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(self.who_is_leader()))
        try:
          #response = pickle.loads(response)
          length = len(pickle.dumps(response))
          connection.sendall(struct.pack('!I', length))
          connection.sendall(pickle.dumps(response))
          connection.close()
          return
        except:
          traceback.print_exc()
          #print("empty response?")
          #print(response)
        end = time.monotonic_ns()
        print("read took:" +str((end-start)/1000000))
        length = len(pickle.dumps(response))
        connection.sendall(struct.pack('!I', length))
        connection.sendall(pickle.dumps(response))
        connection.close()
        return

    elif command == 'WRITE':
      key = payload[1]
      value = payload[2]
      try:
        jobid = payload[3]
      except:
        jobid = None
      self.write(key, value, connection, jobid)
      #print('Client wants to WRITE ' + str(value) + ' to: ' + str(key))
    #print(response)
    elif command == 'bye':
      response = 'bye'
      length = len(pickle.dumps(response))
      connection.sendall(struct.pack('!I', length))
      connection.sendall(pickle.dumps(response))
      connection.close()
      return
    return

  def _prompt(self, command):
    'Application prompt'
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self.printinfo()
      elif command[1] == 'storage':
        self._print_storage()
      elif command[1] == 'queue':
        self._print_queue()
      elif command[1] == 'hist':
        self._print_hist()
      elif command[1] == 'disable':
        self.disable()
      elif command[1] == 'getleader':
        print(self.who_is_leader())
      elif command[1] == 'enable':
        self.enable()
      elif command[1] == 'leader':
        self.consensus.propose(['LEADER', self.tag], leader_round=True)
        #self._set_as_leader()
      elif command[1] == 'follower':
        self._set_as_follower()
      elif command[1] == 'state':
        self.request_consensus_last_state()
      elif command[1] == 'list':
        self._print_servers()
      elif command[1] == 'log':
        self.consensus._print_log()
      elif command[1] == 'add':
        self.request_consensus(command[2].upper())
      elif command[1] == 'consensus':
        if len(command) >2:
          command.pop(0)
        self.consensus._prompt(command)
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()

  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for RSM")
    print()
    print("help                - Print this help message")
    print("log                 - Print current consensus log")
    print("list                - Print current list of servers")
    print("queue               - Print current queue")
    print("hist                - Print current history")
    print("leader              - Set current node as a leader")
    print("getleader           - Ask current node who is the leader")
    print("follower            - Set current node as a follower")
    print("disable             - Set current node as disabled")
    print("enable              - Set current node as enabled")
    print("state               - Pool state from paxos")
    print("storage             - Print storage")
    print("add [newstate]      - Ask consensus module to add state")
    print()

  def _print_servers(self):
    print('Current servers:')
    print()
    for node in self.servers:
      print(node)

  def _print_queue(self):
    print('Current jobs:')
    print()
    for job in self.job_queue:
      print(job)

  def _print_hist(self):
    print('Current jobs:')
    print()
    for job in self.job_hist:
      print(job)

  def _print_storage(self):
    print('Current storage:')
    print()
    for key in self.storage:
      print(str(key) + '-> ' + str(self.storage[key]))

  def printinfo(self):
    print("Application stats (RSM)")
    print("State: \t\t" + self.state)
    print("Role: \t\t" + self.Node.role)
    print()
    self.consensus.printinfo()
