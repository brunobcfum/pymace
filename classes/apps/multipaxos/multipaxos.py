#!/usr/bin/env python3

""" 
Paxos application class is part of a thesis work about distributed systems 
Two main threads are created, one with an UDP socket and one with a TCP socket
UDP socket - Command exchange - ADHOC commands sent in the ether
TCP socket - Data exchange
The membership is controlled by the network application.

This applicaiton uses pickle to serialize data, so it shouldn't be used outside 
academic world since pickle has security flaws.
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.3"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, sys, json, traceback, zlib, fcntl, time, threading, pickle, asyncio, os
from apscheduler.schedulers.background import BackgroundScheduler
from classes.network import network_sockets
from classes import prompt, tools
from struct import pack
from struct import unpack

class App():

  def __init__(self, Node, tag, time_scale, second, tag_number):
    'Initializes the properties of the Node object'
    #### Genesis Common 
    random.seed(tag)
    self.Node = Node
    self.tag = tag
    self.tag_number = tag_number
    self.debug = False
    self.multiplier = time_scale
    self.scheduler = BackgroundScheduler()
    ### Default options that are replaced by settings file
    self.bcast_group = '10.0.0.255' #broadcast ip address
    self.port = 56555 # TCP/UDP port used by paxos to talk to acceptors and learners
    self.client_port = 56444 # Client entry
    self.max_packet = 65500 #max packet size to listen
    self.proposal_timeout = 5000
    self.quorum_len = 10 #initial value, should be made by topology update?
    ### Application variables
    self.max_log = 100000 #what is more pratical? Create a log rotation or just use DEQUE?
    self.job_queue = []
    self.job_hist = []
    self.consensus_log = [None] * self.max_log
    self.leader = ''
    self.quorum = []
    self.max_round = 0
    self.sequence = 0
    self.state = "ENABLED" #current state
    self.seek_head = -1
    self.request = []
    ##################### Constructor actions  #########################
    self._setup()
    self.udp_interface = network_sockets.UdpInterface(self._packet_handler, debug=False, port=self.port, interface='')
    self.tcp_interface = network_sockets.TcpInterface(self._packet_handler, debug=False, port=self.port, interface='')
    self.scheduler.add_job(self._check_quorum, 'interval', seconds=1, id='quorum')
    self.scheduler.add_job(self._broadcast_leader, 'interval', seconds=1, id='leader')
    #self.scheduler.add_job(self._find_gaps, 'interval', seconds=1, id='gap')

  ############# Public methods ########################

  def start(self):
    self.Node.Tracer.add_status_trace("Time" + ";" + "State" + ';'+ 'Role' + ';' + 'Chosen Value' +';' + 'Local Sequence #' +';' + 'Last promise' +';' + 'Current Quorum' + ';' + 'Set Quorum')
    self.udp_interface.start()
    self.tcp_interface.start()
    self.scheduler.start()
    tools.printxy(2, 20 , "L: ---NONE--- ")
    self.election_round()
    self._auto_job()

  def rsm_start(self):
    self.Node.Tracer.add_status_trace("Time" + ";" + "State" + ';'+ 'Role' + ';' + 'Chosen Value' +';' + 'Local Sequence #' +';' + 'Last promise' +';' + 'Current Quorum' + ';' + 'Set Quorum')
    self.udp_interface.start()
    self.tcp_interface.start()
    self.scheduler.start()
    tools.printxy(2, 20 , "L: ---NONE--- ")

  def shutdown(self):
    self.tcp_interface.send(self.myip, "bye".encode(), 255)
    self.udp_interface.send(self.myip, "bye".encode(), 255)
    self.udp_interface.shutdown()
    self.tcp_interface.shutdown()
    self.scheduler.shutdown()

  def local(self):
    pass

  def last_state(self):
    last = 0
    for index in range(0, self.max_log):
      if self.consensus_log[index] == None:
        return self.consensus_log[last]
      else:
        last = index

  def toggleDebug(self):
    self.debug = not self.debug
    if (self.debug): 
      print("Multipaxos -> Debug mode set to on")
    elif (not self.debug): 
      print("Multipaxos -> Debug mode set to off")

  def disable(self):
    if self.state == 'ENABLED':
      self.set_state('DISABLED')
      self.scheduler.shutdown()
      #self.tcp_interface.send(self.myip, "bye".encode(), 255)
      #self.udp_interface.send(self.myip, "bye".encode(), 255)
      self.udp_interface.shutdown()
      self.tcp_interface.shutdown()
    else:
      print("Node not enabled. Skiping...")

  def enable(self):
    if self.state == 'DISABLED':
      self.set_role('FOLLOWER')
      self.set_state('ENABLED')
      self.udp_interface = network_sockets.UdpInterface(self._packet_handler, debug=False, port=self.port, interface='')
      self.tcp_interface = network_sockets.TcpInterface(self._packet_handler, debug=False, port=self.port, interface='')
      self.udp_interface.start()
      self.tcp_interface.start()
      self.scheduler = BackgroundScheduler()
      self.scheduler.add_job(self._check_quorum, 'interval', seconds=1, id='quorum')
      self.scheduler.add_job(self._broadcast_leader, 'interval', seconds=1, id='leader')
      self.scheduler.start()
    else:
      print("Node not disabled. Skiping...")

  def get_leader(self):
    return self.leader

  def election_round(self):
    self.set_role('LEADER')
    self.propose(['LEADER',self.tag], leader_round=True)
    self.set_role('FOLLOWER')

  def propose(self,proposal, leader_round=False):
    log = -1
    if self.get_role() == 'LEADER':
      log = self._propose(proposal, leader_round)
    elif self.get_role() != 'LEADER' and leader_round:
      log = self._propose(proposal, leader_round)
    else:
      print("not leader")
      print(self.get_role())
    return log 
    
  def get_role(self):
    return self.Node.role

  def set_role(self, role):
    self.Node.role = role
    self.Node.Tracer.add_app_trace('PAXOS->' + self.Node.fulltag + ' Set as ' + self.Node.role)

  def get_state(self):
    return self.state

  def set_state(self, state):
    self.state = state
    self.Node.Tracer.add_app_trace('PAXOS->' + self.Node.fulltag + ' Stage changed to ' + self.state)
  
  def get_seek_head(self):
    return self.seek_head

  def increment_seek_head(self, value):
    self.seek_head += value
  
  def set_seek_head(self, value):
    self.seek_head = value

  def sync(self, rounds):
    print("syncing")
    self.set_role('LEADER')
    for i in range(rounds):
      self.propose('')
    self.set_role('SERVER')

  def leader_failed(self):
    self.leader = ''
    tools.printxy(2, 20 , "L: ---NONE--- ")
  ############# Private methods #######################

  def _setup(self):
    self.myip = self.Node.Network.myip
    settings_file = open("./classes/apps/multipaxos/settings.json","r").read()
    settings = json.loads(settings_file)
    self.port = settings['controlPort']
    self.max_packet = settings['maxPacket']
    self.network = settings['network']
    self.bcast_group = settings['network'] + "255"
    self.proposal_timeout = settings['proposalTimeout']
    self.quorum_len = settings['quorumLen']
    self.Node.role = 'SERVER'

  def _auto_job(self):
    'Loads batch jobs from files. File must correspond to node name'
    try:
      jobs_file = open("./classes/apps/multipaxos/job_" + self.Node.fulltag + ".json","r").read()
      jobs_batch = json.loads(jobs_file)
      loop = asyncio.get_event_loop()
      for job in jobs_batch["jobs"]:
        loop.create_task(self._auto_job_add(job['start'],job['type'],job['value']))
      loop.run_forever()
      loop.close()
    except:
      #print("No jobs batch for me")
      pass

  async def _auto_job_add(self, delay, jobtype, value):
    'Adds batch jobs to the scheduler'
    await asyncio.sleep(delay * self.Node.multiplier)
    self._add_job(jobtype, value)

  def _add_job(self, jobtype='propose', value=None):
    'Adds manual jobs'
    if jobtype == 'propose':
      try:
        self._propose(value)
      except:
        traceback.print_exc()
    elif jobtype == 'leader':
      try:
        self.set_role('LEADER')
      except:
        traceback.print_exc()
    elif jobtype == 'disable':
      try:
        self.disable()
      except:
        traceback.print_exc()
    elif jobtype == 'enable':
      try:
        self.enable()
      except:
        traceback.print_exc()

  def _broadcast_leader(self):
    if self.Node.role == 'LEADER':
      if len(self.Node.FaultDetector.get_running()) < (len(self.Node.FaultDetector.get_suspect()) + len(self.Node.FaultDetector.get_faulty())):
        self.set_role('FOLLOWER')
        return
      #There are more faulty than running, so it is better not to have a leader
      #if leader, let others know
      self.leader = self.Node.Network.myip
      tools.printxy(2, 20 , "L: "+ str(self.leader) + "   ")
      leaderPack = [5,self.seek_head]
      leaeder = json.dumps(leaderPack).encode()
      self.Node.Bus.emmit(['RSM', 'BCAST_LEADER', self.tag])
      for node in self.quorum:
        msg_id = self._create_id()
        self.Node.Tracer.add_trace(hex(msg_id)+';'+'SEND' + ';' + 'LEADER' + ';' + str(sys.getsizeof(leaeder)) + ';' + str(node))
        self.worker = threading.Thread(target=self.udp_interface.send, args=(node, leaeder, msg_id))
        self.worker.start()

  def _find_empty(self):
    for entry in range(0,self.max_log):
      if self.consensus_log[entry] == None:
        return entry

  def _find_gaps(self):
    _request = []
    for i in range(len(self.consensus_log)-2):
      try:
        if self.consensus_log[i] == None:
          _request.append(i)
          if self.consensus_log[i+1] != None:
            self.request = _request
            return
      except IndexError:
        pass
      except:
        traceback.print_exc()

  def _create_id(self):
    return zlib.crc32((str(int(time.time()*1000))+ str(self.tag) + str(random.randint(0,10000))).encode())

  def _generate_proposal_number(self):
    self.max_round += 1
    return (self.max_round << 16) + self.tag_number

  def _extract_max_round(self, proposal_number):
    this_round = (proposal_number & 4294901760) >> 16
    server = proposal_number & 65535
    return (this_round , server)

  def _increment_proposal(self):
    self.sequence += 1

  def _status_tracer(self):
    self.Node.Tracer.add_status_trace(str(int(time.time()*1000))  + ';' + self.state + ';' + self.Node.role + ';' + str(self.consensus) + ';' + str(self.sequence) + ';' + str(self.last_promise_sent) +';' + str(len(self.quorum)) + ';' + str(self.quorum_len))
  
  def _move_to_history(self, id):
    pass

  def _encode(self, object):
    data = pickle.dumps(object)
    size = len(data)
    return data, size

  def _check_quorum(self):
    'Creating my quorum based in the Network class, which is an implementation of a membership protocol and needs to be enhanced'
    self.quorum = []
    for node in self.Node.Membership.get_servers():
      if node[0] != self.myip:
        self.quorum.append(node[0])

  def _packet_handler(self, payload, sender_ip, connection):
    'Callback function for receiving packets'
    if (sender_ip == self.myip):
      return
    try:
      payload = pickle.loads(payload)
    except:
      pass
      print(sender_ip)
      #print(payload)
    #magic_word = payload[0]
    #if magic_word != "genesis":
    #  return
    msg_id = payload[0]
    encoded_payload = payload[1]
    try:
      payload = pickle.loads(encoded_payload)
    except:
      payload = json.loads(encoded_payload.decode())
    pdu = payload[0]
    if pdu == 1: # Got a proposal package
      self._handle_prop(payload, sender_ip)
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'PROPOSAL' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    elif pdu == 2: #got an ACK package
      self._handle_prom(payload, sender_ip)
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    elif pdu == 3: #got an ACK package
      self._handle_accept(payload, sender_ip)
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    elif pdu == 4: #got an ACK package
      self._handle_accepted(payload, sender_ip)
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'ACCEPTED' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))
    elif pdu == 5: #got an LEADER package
      self._handle_leader(payload, sender_ip)
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'LEADER' + ';' + str(sys.getsizeof(encoded_payload)) + ';' + str(sender_ip))

  def _handle_prop(self, payload, sender_ip):
    seq = payload[1]
    time = payload[2]
    log = payload[3]
    #print(payload)
    if self.debug: print("Received a proposal with seq #" + str(seq))
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Received proposal ' + str(seq) + ' for slot ' + str(log) + ' from: '+ str(sender_ip))
    #find if log is empty
    if self.consensus_log[log] == None:
      if self.debug: print("Handling because slot is empty")
      self.job_hist.append(['PROPOSAL', sender_ip, seq, time,'', '', log])
      promise = self._createpromise(seq, None , log)
      self.consensus_log[log] = [seq, ""]
      msg_id = self._create_id()
      self.tcp_interface.send(sender_ip, promise, msg_id)
      self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending promise ' + str(seq) + ' for slot ' + str(log) +  ' with value ' + str(self.consensus_log[log][1]) + ' to: '+ str(sender_ip))
      self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(promise)) + ';' + str(sender_ip))
    else:
      if seq > self.consensus_log[log][0]:
        if self.debug: print("Handling because seq is higher than the one we primsed before for this slot")
        self.job_hist.append(['PROPOSAL', sender_ip, seq, time,'', ''])
        #creating promise with old value
        promise = self._createpromise(seq, [self.consensus_log[log][1], 0] , log)
        (self.max_round,_) = self._extract_max_round(seq)
        msg_id = self._create_id()
        self.tcp_interface.send(sender_ip, promise, msg_id)
        self.consensus_log[log][0] = seq
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending promise ' + str(seq) + ' for slot ' + str(log) +  ' with value ' + str(self.consensus_log[log][1]) + ' to: '+ str(sender_ip))
        self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(promise)) + ';' + str(sender_ip))
      else: #maybe instead of denial, we could just don't participate
        #slot was taken with a proposal value higher let sender so to avoid active waiting
        if self.debug: print("Not handling because seq is lower than the one we primsed before for this slot")
        promise = self._createpromise(seq, [self.consensus_log[log][0], -1],log)
        msg_id = self._create_id()
        self.tcp_interface.send(sender_ip, promise, msg_id)
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending denial ' + str(seq) + ' for slot ' + str(log) +  ' with value ' + str(-1) + ' to: '+ str(sender_ip))
        self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(promise)) + ';' + str(sender_ip))

  def _handle_prom(self, payload, sender_ip):
    lock = threading.Lock()
    seq = payload[1]
    consensus = payload[2]
    log = payload[3]
    if consensus == None:
      if self.debug: print("Received promise "+ str(seq) + "/" + str(log) + " from:" + str(sender_ip))
      self.Node.Tracer.add_app_trace('PAXOS->' + 'Received promise ' + str(seq) + ' for slot ' + str(log) +  ' with value ' + str(consensus) + ' from: '+ str(sender_ip))
      lock.acquire()
      for job in self.job_queue:
        if (job[1] == seq) and (job[6] == log):
          if job[4] == 'ONGOING' and len(job[5]) <= self.quorum_len / 2:
            job[5].append(sender_ip)
      lock.release()
    elif str(consensus[1]) == "-1":
      #todo: can we skip this step?
      #this was denied cause was more updated. Lets skip to its round
      if self.debug: print("This proposal "+ str(seq) + "/" + str(log) + " was denied. There was a more recent proposal")
      self.Node.Tracer.add_app_trace('PAXOS->' + 'Received denial ' + str(seq) + ' for slot ' + str(log) +  ' with value ' + str(consensus) + ' from: '+ str(sender_ip))
      #checking If I'm the one proposing. Would be better to create a unique ID
      #self.Node.role = 'LEADER'
      (self.max_round,_) = self._extract_max_round(seq)
      self.consensus_log[log] = None
      lock.acquire()
      for job in self.job_queue:
         if (job[1] == seq) and (job[6] == log):
          job[4] = 'REJECTED'
      lock.release()
    else:
      if self.debug: print("This proposal "+ str(seq) + "/" + str(log) + "was skiped due to previews consensus. Keeping same value")
      self.Node.Tracer.add_app_trace('PAXOS->' + 'Received promise ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
      #self.Node.role = 'LEADER'
      self.consensus_log[log][1] = consensus[0]
      lock.acquire()
      for job in self.job_queue:
        if (job[1] == seq) and (job[6] == log):
          job[4] = 'CONSENSUS'
          if job[4] == 'ONGOING' or job[4] == 'CONSENSUS':
            job[5].append(sender_ip)
      lock.release()

  def _handle_accept(self, payload, sender_ip):
    if self.debug: print(payload)
    lock = threading.Lock()
    log = payload[3]
    value = payload[2]
    seq = payload[1]
    if self.debug: print("Received ACCEPT  "+ str(seq) + "/" + str(log) + "/" + str(value) + " from:" + str(sender_ip))
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Received ACCEPT! proposal ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
    #gonna handle the accept event if i didnt promise
    if self.consensus_log[log] == None:
      self.consensus_log[log] = [0, ""]
    if (seq >= self.consensus_log[log][0]):
      lock.acquire()
      #for job in self.job_hist:
      #  if (seq == job[1]) and (job[6] == log):#job2?
      #    job[4] = payload[2]
      #    job[5] = 'ACCEPTED'
      lock.release()
      self.consensus_log[log][1] = value
      (self.max_round,_) = self._extract_max_round(seq) 
      #self.consensus = [payload[1], payload[2]]
      #self.sequence = payload[1]
      #TODO : Come up with something for sync
      #if log == self.get_seek_head() + 1:
        #we are in sync
      self.set_seek_head(log)
      try:
        self.Node.Bus.emmit(['RSM', 'COMMIT', value])
      except:
        if self.debug: print("Multipaxos-handleaccept->Could not write to BUS")
      #elif self.get_seek_head() >= log:
        #pass
      #elif log > self.get_seek_head() + 1:
        #looks like we are falling behind. Call sync
        #self.sync(log - self.get_seek_head())
        #sync is not working well
      #  pass
      self._createAccepted(payload[1], sender_ip, log)

  def _handle_accepted(self, payload, sender_ip):
    lock = threading.Lock()
    seq = payload[1]
    value = payload[2]
    log = payload[3]
    if self.debug: print("Received ACCEPTED  "+ str(seq) + "/" + str(log) + "/" + str(value) + " from:" + str(sender_ip))
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Got accepted for proposal '+ str(payload[1]) + ' with value: ' + str(payload[2]))
    lock.acquire()
    for job in self.job_queue:
      if (seq == job[1]) and (job[6] == log):
        self.consensus_log[log][1] = value
        #TODO : Come up with something for sync
        #if log == self.get_seek_head() + 1:
          #we are in sync
        #  self.increment_seek_head(1)
        try:
          self.Node.Bus.emmit(['RSM', 'COMMIT', value])
        except:
          if self.debug: print("Multipaxos-handleaccept->Could not write to BUS")
          #traceback.print_exc()
        self.set_seek_head(log)
        #self.consensus = payload[2]
        job[4] = 'FINALIZED'
        self.job_hist.append(job)
        self.job_queue.remove(job)
    lock.release()

  def _handle_leader(self, payload, sender_ip):
    #if self.debug: print("Got leader")
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Got leader keepalive from: ' + str(sender_ip))
    self.leader = sender_ip
    self.Node.FaultDetector.set_leader(sender_ip)
    tools.printxy(2, 20 , "L: "+ str(self.leader) + "   ")
    leader_seek_head = payload[1]
    request = []
    if leader_seek_head > self.seek_head:
      pass
      #I am behind
      #for i in range(self.seek_head+1, leader_seek_head):
      #  request.append(i)
    #request from leader missing positions

  def _propose(self, proposal, leader_round=False):
    tlock = threading.Lock()
    tlock.acquire()
    self.sequence = self._generate_proposal_number()
    self.current_log_position = 0
    tlock.release()
    #log = 0
    #if not leader_round:
    self.current_log_position = self._find_empty()
    log =  self.current_log_position
    self.job_queue.append(['PROPOSAL', self.sequence, int(time.time()*1000), proposal, 'ONGOING', [], log])
    seq = self.sequence
    self.consensus_log[log] = [seq, ""]
    propPack = [1 , self.sequence, int(time.time()*1000), log]
    prop = pickle.dumps(propPack)
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(seq) + ' for position ' + str(log) + ' with value: ' + str(proposal)+ ' is being sent to: '+ str(self.quorum))
    if self.debug: print("Proposing:" + str(self.sequence) + ' for pos ' + str(log) + ' with value: ' + str(proposal))
    for node in self.quorum:
      msg_id = self._create_id()
      self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROPOSAL' + ';' + str(sys.getsizeof(prop)) + ';' + str(node))
      self.worker = threading.Thread(target=self.tcp_interface.send, args=(node,prop, msg_id))
      self.worker.start()
    propTd = threading.Thread(target=self._propose_thread, args=(self.quorum, seq, int(time.time()*1000), log))
    propTd.start()
    return log

  def _propose_thread(self, quorum, seq, start, current_log_position):
    lock = True
    tlock = threading.Lock()
    while lock:
      if int(time.time()*1000) - start > self.proposal_timeout:
        lock = False
        if self.debug: print("Proposal rejected in stage 1")
        tlock.acquire()
        for job in self.job_queue:
          if job[1] == seq:
            job[4] = 'REJECTED'
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(seq) + ' was rejected in stage 1')
            #print(self.current_log_position)
            self.consensus_log[self.current_log_position][1] = 'NOP'
            response = [self.current_log_position, -1]
            self.job_hist.append(job)
            self.job_queue.remove(job)
        tlock.release()
      else:
        tlock.acquire()
        for job in self.job_queue:
          if (job[1] == seq) and (job[6] == current_log_position):
            voters = len(job[5])
            #if float(voters) >= (len(quorum) * 2) / 3: #variable quorum
            if float(voters) > float((self.quorum_len * 1.0) / 2): #fixed quorum
              if job[4] == 'ONGOING':
                job[4] = 'PROMISED'
              if self.debug: print("Enougth quorum for stage 2")
              self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(seq) + ' was accepted in stage 1 by:' + str(voters) + ' voters.' )
              lock = False
              self._createAccept(seq,current_log_position)
        tlock.release()
      time.sleep(0.01)

  def _createpromise(self, seq, value, log):
    promise = [2, seq, value, log]
    prom = pickle.dumps(promise)
    return prom

  def _createAccept(self, seq, log):
    if self.debug: print("createAccept -> " + str(seq) + "/" + str(log))
    for job in self.job_queue:
      if (job[1] == seq) and (job[6] == log):
        if job[4] == 'PROMISED':
          if self.debug: print("Sending ACCEPT PROMISED "+ str(seq) + "/" + str(log))
          accPack = [3, seq, job[3], log]
          accept = pickle.dumps(accPack)
          #Here we are sending to quorum or to the ones that sent promises?
          #for acceptor in job[5]:
          for acceptor in self.quorum:
            msg_id = self._create_id()
            self.tcp_interface.send(acceptor, accept, msg_id)
            self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(accept)) + ';' + str(acceptor))
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Sent ACCEPT to:'+ str(acceptor))
        elif job[4] == 'CONSENSUS':
          if self.debug: print("Sending ACCEPT CONSENSUS "+ str(seq) + "/" + str(log))
          accPack = [3, seq, self.consensus_log[log][1],log]
          accept = pickle.dumps(accPack)
          #Here we are sending to quorum or to the ones that sent promises?
          #for acceptor in job[5]:
          for acceptor in self.quorum:
            msg_id = self._create_id()
            self.tcp_interface.send(acceptor, accept, msg_id)
            self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(accept)) + ';' + str(acceptor))
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Sent ACCEPT to:'+ str(acceptor))
      else:
        if self.debug: print("Not sending ACCEPT  "+ str(seq) + "/" + str(log))

  def _createAccepted(self, seq, sender, log):
    acceptedPack = [4, seq, self.consensus_log[log][1], log]
    accepted = pickle.dumps(acceptedPack)
    msg_id = self._create_id()
    self.tcp_interface.send(sender, accepted, msg_id)
    self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPTED' + ';' + str(sys.getsizeof(accepted)) + ';' + str(sender))
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending ACCEPT! proposal ' + str(seq) + ' with value ' + str(self.consensus_log[log][1]) + ' packet to: '+ str(sender))

  def _get_ip(self,iface = 'eth0'):
    'This should be in routing layer'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
    try:
      res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
      traceback.print_exc()
      return None
    ip = unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

  def _sender_udp(self, destination, bytes_to_send, msg_id):
    bytes_to_send = pickle.dumps(["genesis",hex(msg_id), bytes_to_send])
    addrinfo = socket.getaddrinfo(destination, None)[1] 
    sender_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    sender_socket.sendto(bytes_to_send, (destination, self.port))
    sender_socket.close()

  def _sender_tcp(self, destination, bytes_to_send, msg_id):
    try:
      bytes_to_send = pickle.dumps(["genesis", hex(msg_id), bytes_to_send])
      addrinfo = socket.getaddrinfo(destination, None)[1] 
      sender_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM)
      sender_socket.settimeout(5)
      sender_socket.connect((destination, self.port))
      sender_socket.sendall(bytes_to_send)
      sender_socket.close()
    except:
      if self.debug: print("Could not send data to: " + str(destination))

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'propose':
        if self.Node.role != 'LEADER':
          prompt.print_error('Try this from a node set as leader')
        else:
          try:
            proposal = command[2]
            self._propose(proposal)
          except:
            traceback.print_exc()
            prompt.print_alert('Command error')
            self._printhelp()                    
      elif command[1] == 'leader':
        prompt.print_alert('Setting this node as a leader')
        self.set_role('LEADER')
      elif command[1] == 'server':
        prompt.print_alert('Setting this node as a server')
        self.set_role('SERVER')
      elif command[1] == 'disable':
        if (self.debug): prompt.print_alert('Disabling node')
        self.disable()
      elif command[1] == 'enable':
        if (self.debug): prompt.print_alert('Enabling node')
        self.enable()
      elif command[1] == 'hist':
        self._print_hist()
      elif command[1] == 'info':
        self.printinfo()
      elif command[1] == 'debug':
        self.debug = not self.debug
      elif command[1] == 'quorum':
        self._print_quorum()
      elif command[1] == 'log':
        self._print_log()
      elif command[1] == 'queue':
        self._print_queue()
      elif command[1] == 'request':
        self._print_request()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()

  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for Multi-Paxos")
    print()
    print("help                - Print this help message")
    print("quorum              - Show current quorum")
    print("queue               - Show current job queue")
    print("hist                - Show current job history")
    print("log                 - Print current consensus log")
    print("leader              - Set current node as a leader")
    print("server              - Set current node as a server")
    print("disable             - Set current node as disabled")
    print("enable              - Set current node as enabled")
    print("propose [value]     - Propose a new value to quorum")
    print()

  def printinfo(self):
    'Prints general information about the application'
    print()
    print("Application stats (MultiPaxos)")
    print("State: \t\t" + self.state)
    print("Role: \t\t" + self.Node.role)
    print("Paxos leader: \t" + self.leader)
    print()

  def _print_queue(self):
    print('Local job queue:')
    print()
    for job in self.job_queue:
      print(job)

  def _print_hist(self):
    print('Local history:')
    print()
    for job in self.job_hist:
      print(job)

  def _print_quorum(self):
    print('Current Quorum:')
    print()
    for node in self.quorum:
      print(node)

  def _print_log(self):
    print('Current seek head:' + str(self.get_seek_head()))
    print('Current log:')
    print()
    for entry in range(0,self.max_log):
    #for entry in self.consensus_log:
      if self.consensus_log[entry] != None:
        seq, ser = self._extract_max_round(self.consensus_log[entry][0]) 
        print(str(entry) + "-Seq:" + str(seq) + " Ser:" + str(ser) + "-->" + str(self.consensus_log[entry]))
  
  def _print_request(self):
    print('Current seek head:' + str(self.get_seek_head()))
    print('Current gap: ' + str(self.request))
    print()