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
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, sys, json, traceback, zlib, fcntl, time, threading, pickle, asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt
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
    self.max_packet = 1500 #max packet size to listen
    self.proposal_timeout = 5000
    self.quorum_len = 10 #initial value, should be made by topology update?
    ### Application variables
    self.job_queue = []
    self.job_hist = []
    self.consensus_log = []
    self.quorum = []
    self.consensus = None
    self.sequence = (self.tag_number << 16) + 0
    self.last_promise_sent = 0
    self.state = "ENABLED" #current state
    ##################### Constructor actions  #########################
    self._setup()
    self.udp_listener_thread = threading.Thread(target=self._udp_listener, args=())
    self.tcp_listener_thread = threading.Thread(target=self._tcp_listener, args=())
    self.client_listener_thread = threading.Thread(target=self._client_listener, args=())
    #self.t4 = threading.Thread(target=self._check_quorum, args=())
    self.scheduler.add_job(self._check_quorum, 'interval', seconds=1, id='quorum')
    self.scheduler.add_job(self._status_tracer, 'interval', seconds=1, id='status_log')

  ############# Public methods ########################

  def start(self):
    self.Node.Tracer.add_status_trace("Time" + ";" + "State" + ';'+ 'Role' + ';' + 'Chosen Value' +';' + 'Local Sequence #' +';' + 'Last promise' +';' + 'Current Quorum' + ';' + 'Set Quorum')
    self.udp_listener_thread.start()
    self.tcp_listener_thread.start()
    self.client_listener_thread.start()
    self.scheduler.start()
    self._auto_job()

  def rsm_start(self):
    self.Node.Tracer.add_status_trace("Time" + ";" + "State" + ';'+ 'Role' + ';' + 'Chosen Value' +';' + 'Local Sequence #' +';' + 'Last promise' +';' + 'Current Quorum' + ';' + 'Set Quorum')
    self.udp_listener_thread.start()
    self.tcp_listener_thread.start()
    self.client_listener_thread.start()
    self.scheduler.start()

  def shutdown(self):
    self.udp_listener_thread.join(timeout = 2)
    self.tcp_listener_thread.join(timeout = 2)
    self.client_listener_thread.join(timeout = 2)
    self.scheduler.shutdown()

  def local(self):
    pass

  def printinfo(self):
    'Prints general information about the application'
    print()
    print("Application stats (Paxos)")
    print("State: \t\t" + self.state)
    print("Role: \t\t" + self.Node.role)
    print("Sequence #: \t" + str(self.sequence))
    print("Last handled #: " + str(self.last_promise_sent))
    print("Consensus: " + str(self.consensus))
    print()

  def election_round(self):
    self.set_role('LEADER')
    self.propose(self.tag)

  def propose(self,proposal):
    if self.get_role() == 'LEADER':
      self._propose(proposal)
    
  def get_role(self):
    return self.Node.role

  def get_state(self):
    return self.state

  def set_role(self, role):
    self.Node.role = role
    self.Node.Tracer.add_app_trace('PAXOS->' + self.Node.fulltag + ' Set as ' + self.Node.role)

  def set_state(self, state):
    if (state.upper() == 'DISABLED'):
      self.udp_listener_thread.join(timeout = 2)
      self.tcp_listener_thread.join(timeout = 2)
    elif (state.upper() == 'ENABLED'):
      self.udp_listener_thread = threading.Thread(target=self._udp_listener, args=())
      self.tcp_listener_thread = threading.Thread(target=self._tcp_listener, args=())
      self.udp_listener_thread.start()
      self.tcp_listener_thread.start()
    self.state = state
    self.Node.Tracer.add_app_trace('PAXOS->' + self.Node.fulltag + ' Stage changed to ' + self.state)


  ############# Private methods #######################

  def _increment_proposal(self):
    self.sequence += 1 

  def _status_tracer(self):
    self.Node.Tracer.add_status_trace(str(int(time.time()*1000))  + ';' + self.state + ';' + self.Node.role + ';' + str(self.consensus) + ';' + str(self.sequence) + ';' + str(self.last_promise_sent) +';' + str(len(self.quorum)) + ';' + str(self.quorum_len))

  def _setup(self):
    settings_file = open("./classes/apps/paxos/settings.json","r").read()
    settings = json.loads(settings_file)
    self.port = settings['controlPort']
    self.client_port = settings['clientPort']
    self.max_packet = settings['maxUDPPacket']
    self.network = settings['network']
    self.bcast_group = settings['network'] + "255"
    self.proposal_timeout = settings['proposalTimeout']
    self.quorum_len = settings['quorumLen']
    self.Node.role = 'SERVER'

  def _auto_job(self):
    'Loads batch jobs from files. File must correspond to node name'
    try:
      jobs_file = open("./classes/apps/paxos/job_" + self.Node.fulltag + ".json","r").read()
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
        self.set_state('DISABLED')
      except:
        traceback.print_exc()
    elif jobtype == 'enable':
      try:
        self.set_state('ENABLED')
      except:
        traceback.print_exc()

  def _check_quorum(self):
    'Creating my quorum based in the Network class, which is an implementation of a membership protocol and needs to be enhanced'
    if self.Node.Membership.dynamic:
      self.quorum = []
      for node in self.Node.Membership.visible:
        if node[0] != self.myip:
          self.quorum.append(node[0])
    else:
      self.quorum = []
      for i in range(0,self.quorum_len):
        self.quorum.append(self.network + str(i+1))
  def _move_to_history(self, id):
    pass

  def _udp_listener(self):
    'This method opens a UDP socket to receive commands. It runs in infinite loop as long as the node is up'
    addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
    listen_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM) #UDP
    port = self.port + self.Node.tag_number
    interface='tap' + str(self.Node.tag_number)
    listen_socket.bind(('', self.port))
    self.myip = self._get_ip(interface)
    while self.Node.lock: #this infinity loop handles the received packets
      payload, sender = listen_socket.recvfrom(self.max_packet)
      sender_ip = str(sender[0])
      self.Node.Membership.packets+=1
      self._packet_handler(payload, sender_ip)
    listen_socket.close()

  def _tcp_listener(self):
    'This method opens a TCP socket to receive data. It runs in infinite loop as long as the node is up'
    addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
    listen_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM) 
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = self.port + self.Node.tag_number
    interface='tap' + str(self.Node.tag_number)
    self.myip = self._get_ip(interface)
    listen_socket.bind(('', self.port))
    listen_socket.listen(10)
    while self.Node.lock: #this infinity loop handles the received packets
      connection, sender = listen_socket.accept()
      sender_ip = str(sender[0])
      try:
        payload = connection.recv(self.max_packet) 
      finally:
        connection.close()
      self._packet_handler(payload, sender_ip)
    listen_socket.close()

  def _client_listener(self):
    'This method opens a TCP socket to receive data. It runs in infinite loop as long as the node is up'
    addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
    listen_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM) 
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = self.port + self.Node.tag_number
    interface='tap' + str(self.Node.tag_number)
    self.myip = self._get_ip(interface)
    listen_socket.bind(('', self.client_port))
    listen_socket.listen(10)
    while self.Node.lock: #this infinity loop handles the received packets
      connection, sender = listen_socket.accept()
      sender_ip = str(sender[0])
      try:
        payload = connection.recv(self.max_packet) 
      finally:
        connection.close()
      #do something with client request
    listen_socket.close()

  def _packet_handler(self, payload, sender_ip):
    'When a message of type gossip is received from neighbours this method unpacks and handles it'
    'This should be in routing layer'
    payload = pickle.loads(payload)
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

  def _handle_prop(self, payload, sender_ip):
    seq = payload[1]
    time = payload[2]
    #print(payload)
    if (sender_ip != self.myip):
      if self.debug: print("Received a proposal with seq #" + str(seq))
      self.Node.Tracer.add_app_trace('PAXOS->' + 'Received proposal ' + str(payload[1]) + ' from: '+ str(sender_ip))
      if seq > self.last_promise_sent:
        if self.debug: print("Handling because seq is higher than the one we primse")
        self.job_hist.append(['PROPOSAL', sender_ip, seq, time,'', ''])
        if self.consensus == None:
          promise = self._createpromise(seq, None)
        else:
          promise = self._createpromise(seq, self.consensus)
        self.last_promise_sent = int(seq)
        msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
        self._sender_tcp(sender_ip, promise, msg_id)
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending promise ' + str(seq) + ' with value ' + str(self.consensus) + ' to: '+ str(sender_ip))
        self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(promise)) + ';' + str(sender_ip))
      else: #maybe instead of denial, we could just don't participate
        promise = self._createpromise(seq, [self.last_promise_sent, -1])
        msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
        self._sender_tcp(sender_ip, promise, msg_id)
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending denial ' + str(seq) + ' with value ' + str(-1) + ' to: '+ str(sender_ip))
        self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROMISE' + ';' + str(sys.getsizeof(promise)) + ';' + str(sender_ip))
  def _createpromise(self, m, w):
    promise = [2, m, w]
    prom = json.dumps(promise).encode()
    return prom

  def _handle_prom(self, payload, sender_ip):
    seq = payload[1]
    consensus = payload[2]
    if (sender_ip != self.myip):
      if consensus == None:
        if self.debug: print("Received promise from:" + str(sender_ip))
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Received promise ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
        for job in self.job_queue:
          if job[1] == seq:
            job[5].append(sender_ip)
      elif str(consensus[1]) == "-1":
        if self.debug: print("This proposal was denied. There was a more recent proposal")
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Received denial ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
        #checking If I'm the one proposing. Would be better to create a unique ID
        #self.Node.role = 'LEADER'
        for job in self.job_queue:
          if job[1] == seq:
            job[4] = 'REJECTED'
      else:
        if self.debug: print("This proposal was skiped due to previews consensus. Keeping same value")
        self.Node.Tracer.add_app_trace('PAXOS->' + 'Received promise ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
        #self.Node.role = 'LEADER'
        self.consensus = consensus
        for job in self.job_queue:
          if job[1] == seq:
            job[4] = 'CONSENSUS'
            job[5].append(sender_ip)

  def _handle_accept(self, payload, sender_ip):
    if self.debug: print("Received ACCEPT from:" + str(sender_ip))
    if self.debug: print(payload)
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Received ACCEPT! proposal ' + str(payload[1]) + ' with value ' + str(payload[2]) + ' from: '+ str(sender_ip))
    if (payload[1] >= self.last_promise_sent):
      for job in self.job_hist:
        if payload[1] == job[2]:
          job[4] = payload[2]
          job[5] = 'ACCEPTED'
      self.consensus = [payload[1], payload[2]]
      #self.sequence = payload[1]
      self._createAccepted(payload[1], sender_ip)

  def _createAccepted(self, seq, sender):
    acceptedPack = [4, seq, self.consensus]
    accepted = json.dumps(acceptedPack).encode()
    msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
    self._sender_tcp(sender, accepted, msg_id)
    self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPTED' + ';' + str(sys.getsizeof(accepted)) + ';' + str(sender))
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Sending ACCEPT! proposal ' + str(seq) + ' with value ' + str(self.consensus) + ' packet to: '+ str(sender))
    

  def _handle_accepted(self, payload, sender_ip):
    if self.debug: print("Got accepted")
    seq = payload[1]
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Got accepted for proposal '+ str(payload[1]) + ' with value: ' + str(payload[2]))
    for job in self.job_queue:
      if job[1] == seq:
        self.consensus = payload[2]
        job[4] = 'FINALIZED'

  def _propose(self, proposal):
    if self.debug: print("Proposing:" + proposal)
    self._increment_proposal()
    self.job_queue.append(['PROPOSAL', self.sequence, int(time.time()*1000), proposal, 'ONGOING', []])
    propPack = [1 , self.sequence, int(time.time()*1000)]
    prop = json.dumps(propPack).encode()
    self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(self.sequence ) + ' with value: ' + str(proposal)+ ' is being sent to: '+ str(self.quorum))
    for node in self.quorum:
      msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
      self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'PROPOSAL' + ';' + str(sys.getsizeof(prop)) + ';' + str(node))
      self.worker = threading.Thread(target=self._sender_tcp, args=(node,prop, msg_id))
      self.worker.start()
    propTd = threading.Thread(target=self._propose_thread, args=(self.quorum,self.sequence,int(time.time()*1000),))
    propTd.start()

  def _propose_thread(self, quorum, seq, start):
    lock = True
    while lock:
      if int(time.time()*1000) - start > self.proposal_timeout:
        lock = False
        if self.debug: print("Proposal rejected in stage 1")
        for job in self.job_queue:
          if job[1] == seq:
            job[4] = 'REJECTED'
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(seq) + ' was rejected in stage 1')
      else:
        for job in self.job_queue:
          if job[1] == seq:
            voters = len(job[5])
            #if float(voters) >= (len(quorum) * 2) / 3: #variable quorum
            if float(voters) > (self.quorum_len * 1) / 2: #fixed quorum
              if job[4] == 'ONGOING':
                job[4] = 'ACCEPTED'
              if self.debug: print("Enougth quorum for stage 2")
              self.Node.Tracer.add_app_trace('PAXOS->' + 'Proposal '+ str(seq) + ' was accepted in stage 1 by:' + str(voters) + ' voters.' )
              lock = False
              self._createAccept(seq)
      time.sleep(0.01)

  def _createAccept(self, seq):
    for job in self.job_queue:
      if job[1] == seq:
        if job[4] == 'ACCEPTED':
          accPack = [3, seq, job[3]]
          accept = json.dumps(accPack).encode()
          #Here we are sending to quorum or to the ones that sent promises?
          #for acceptor in job[5]:
          for acceptor in self.quorum:
            msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
            self._sender_tcp(acceptor, accept, msg_id)
            self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(accept)) + ';' + str(acceptor))
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Sent ACCEPT to:'+ str(acceptor))
        elif job[4] == 'CONSENSUS':
          accPack = [3, seq, self.consensus[1]]
          if self.debug: print(accPack)
          accept = json.dumps(accPack).encode()
          #Here we are sending to quorum or to the ones that sent promises?
          #for acceptor in job[5]:
          for acceptor in self.quorum:
            msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
            self._sender_tcp(acceptor, accept, msg_id)
            self.Node.Tracer.add_trace(hex(msg_id)+';'+'SENT' + ';' + 'ACCEPT' + ';' + str(sys.getsizeof(accept)) + ';' + str(acceptor))
            self.Node.Tracer.add_app_trace('PAXOS->' + 'Sent ACCEPT to:'+ str(acceptor))

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

  def _shareDataTCP(self, data, size, job, destination):
    job = pack('>10s', job[0].encode())
    length = pack('>Q', size)
    addrinfo = socket.getaddrinfo(destination, None)[1] 
    sender_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM)
    sender_socket.settimeout(10)
    sender_socket.connect((destination, self.data_port))
    sender_socket.sendall(length)
    sender_socket.sendall(job)
    sender_socket.sendall(data)
    sender_socket.close()

  def _encode(self, object):
    data = pickle.dumps(object)
    size = len(data)
    return data, size

  def _sender_upd(self, destination, bytes_to_send, msg_id):
    'This method sends an epidemid message with the data read by the sensor'
    bytes_to_send = pickle.dumps([hex(msg_id), bytes_to_send])
    addrinfo = socket.getaddrinfo(destination, None)[1] 
    sender_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    sender_socket.sendto(bytes_to_send, (destination, self.port))
    sender_socket.close()

  def _sender_tcp(self, destination, bytes_to_send, msg_id):
    'This method sends an epidemid message with the data read by the sensor'
    try:
      bytes_to_send = pickle.dumps([hex(msg_id), bytes_to_send])
      addrinfo = socket.getaddrinfo(destination, None)[1] 
      sender_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM)
      sender_socket.settimeout(10)
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
        self.set_state('DISABLED')
      elif command[1] == 'enable':
        if (self.debug): prompt.print_alert('Enabling node')
        self.set_state('ENABLED')
      elif command[1] == 'hist':
        self._print_hist()
      elif command[1] == 'info':
        self.printinfo()
      elif command[1] == 'debug':
        self.debug = not self.debug
      elif command[1] == 'quorum':
        self._print_quorum()
      elif command[1] == 'queue':
        self._print_queue()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()

  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for Paxos")
    print()
    print("help                - Print this help message")
    print("quorum              - Show current quorum")
    print("queue               - Show current job queue")
    print("hist               - Show current job history")
    print("leader              - Set current node as a leader")
    print("server              - Set current node as a server")
    print("propose [value]     - Propose a new value to quorum")
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
