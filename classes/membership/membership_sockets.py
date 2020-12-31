#!/usr/bin/env python3

""" 
Memebership service classes
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, struct, sys, json, traceback, zlib, fcntl, threading, time, pickle, distutils, random
from operator import itemgetter
from apscheduler.schedulers.background import BackgroundScheduler
from classes.network import network_sockets
from classes import log

from base64 import (
    b64encode,
    b64decode,
)

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.py3compat import *

class Local():

  def __init__(self, Node, ip):
    'Initializes the properties of the Node object'
    self.scheduler = BackgroundScheduler()
    #### NODE ###############################################################################
    self.Node = Node
    self.visible = [] #our visibble neighbours
    self.ever_visible = [] #our visibble neighbours
    self.visibility_lost = [] #our visibble neighbours
    self.messages_created = [] #messages created by each node
    self.messages = []
    self.average = 0
    self.topology = [] #our visibble neighbours
    #### NETWORK ##############################################################################
    self.ip = ip 
    #print(self.net_trans)
    if self.ip == 'IPV4':
      self.bcast_group = '10.0.0.255' #broadcast ip address
    elif self.ip == 'IPV6':
      self.bcast_group = 'ff02::1'
    self.port = 56123 # UDP port 
    self.max_packet = 65535 #max packet size to listen
    #### UTILITIES ############################################################################
    self.protocol_stats = [0,0,0,0] #created, forwarded, delivered, discarded
    self.errors = [0,0,0]
    self.myip = ''
    #### Layer specific ####################################################################
    self.ttl = 16 #not used now
    self.dynamic = True
    self.fanout_max = 3
    self.mode = "NDM" #close neighbouhood discover mode
    self.packets = 0
    self.traffic = 0
    self.helloInterval = 0.2
    self.visible_timeout =  self.helloInterval * 5 #timeout when visible neighbours should be removed from list in s TODO make it setting
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()
    if self.dynamic:
      self.t2 = threading.Thread(target=self._listener, args=())
      self.scheduler.add_job(self._sendHello, 'interval', seconds=self.helloInterval, id='membership')
      self.scheduler.add_job(self._analyse_visible, 'interval', seconds=0.1, id='membership_analysis')

  ############### Public methods ###########################

  def start(self):
    self.t2.start()
    self.scheduler.start()

  def shutdown(self):
    self.scheduler.shutdown()
    #TODO: To actually join the thread one need to unlock the socket by writing something to it.
    self.t2.join(timeout=2)

  def printinfo(self):
    'Prints general information about the node'
    print()
    print("STUB - Using the OS routing and network")
    print("Broadcast IP: " + self.bcast_group)
    print()

  def get_servers(self):
    return self.visible

  def printvisible(self):
    print("Visible neighbours at:" + str(self.Node.simulation_seconds) )
    print("===============================================================================")
    print("|IP\t\t|Node ID\t|Load\t\t|Last seen\t|")
    print("-------------------------------------------------------------------------------")
    for member in range(len(self.visible)):
      print ("|"+self.visible[member][0]+"\t|"+str(self.visible[member][1])+"\t\t|"+str(self.visible[member][2])+"\t\t|"+str(self.visible[member][3])+"\t\t|")
    print("===============================================================================")
  
  ############### Private methods ##########################

  def _setup(self):
    settings_file = open("./classes/network/settings.json","r").read()
    settings = json.loads(settings_file)
    self.interface_stem = settings['interface']
    if self.interface_stem == "tap":
      interface=self.interface_stem + self.Node.tag[-1]
    elif self.interface_stem == "bat":
      interface=self.interface_stem + '0'
    elif self.interface_stem == "eth":
      interface=self.interface_stem + '0'
    self.myip = self._get_ip(interface)
    self.port = settings['networkPort']
    self.bcast_group = settings['ipv4bcast']
    self.helloInterval = settings['helloInterval']
    self.visible_timeout = settings['visibleTimeout']
    self.dynamic = True if settings['dynamic'] == "True" else False

  def _listener(self):
    'This method opens a UDP socket to receive data. It runs in infinite loop as long as the node is up'
    addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
    self.udp_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM) #UDP
    self.udp_socket.bind(('', self.port))
    if (self.ip=='IPV6'):
      group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
      mreq = group_bin + struct.pack('@I', 0)
      self.udp_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
    while self.Node.lock: #this infinity loop handles the received packets
      payload, sender = self.udp_socket.recvfrom(self.max_packet)
      sender_ip = str(sender[0])
      #self.packets += 1
      self._packet_handler(payload, sender_ip)
    self.udp_socket.close()

  def _packet_handler(self, payload, sender_ip):
    'When a message of type gossip is received from neighbours this method unpacks and handles it'
    pickleload = payload
    payload = pickle.loads(pickleload)
    msg_id = payload[0]
    payload = pickle.loads(payload[1])
    pdu = payload[0]
    if pdu == 0: # Got a hello package
      #msg_id = zlib.crc32(str((self.Node.simulation_mseconds)).encode())
      self.Node.Tracer.add_trace(msg_id+';'+'RECV' + ';' + 'HELLO' + ';' + str(sys.getsizeof(pickleload)) + ';' + str(sender_ip))
      node = payload[1]
      processor = payload[2]
      if (node != self.Node.tag):
        if len(self.visible) > 0: #list no empty, check if already there
          not_there = 1
          for element in range(len(self.visible)):
            if sender_ip == self.visible[element][0]: #if there...
              self.visible[element][3] = self.Node.simulation_seconds # refresh timestamp
              self.visible[element][2] = processor # refresh timestamp
              not_there = 0
              break
          if not_there:
            self.visible.append([sender_ip, node, processor, self.Node.simulation_seconds, 0])
        else: #Empty neighbours list, add 
          self.visible.append([sender_ip, node, processor, self.Node.simulation_seconds, 0])
    else:
      print('not hello')

  def _broadcaster(self, bytes_to_send):
    'This method sends a hello message'
    addrinfo = socket.getaddrinfo(self.bcast_group, None)[1] 
    sender_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    if (self.ip=='IPV6'):
      ttl_bin  = struct.pack('@i', 1) #ttl=1
      sender_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
    elif (self.ip=='IPV4'):
      sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.messages_created.append([hex(1),self.Node.simulation_seconds])
    sender_socket.sendto(bytes_to_send, (addrinfo[4][0], self.port))
    sender_socket.close()
    self.Node.stats[0] += 1

  def _createHello(self):
    processor = self.Node.load
    helloPack = pickle.dumps([0, self.Node.tag, processor])
    buffer = bytearray()
    buffer.append(0)
    buffer.extend(map(ord, self.Node.tag))
    if len(buffer) < 11:
      left = 11 - len(buffer)
      for i in range(left):
        buffer.append(0)
    buffer.append(processor)
    return helloPack

  def _sendHello(self):
    msg_id = zlib.crc32(str((int(time.time()*1000))).encode())
    _buffer = self._createHello()
    _buffer = pickle.dumps([hex(msg_id), _buffer])
    self._broadcaster(_buffer)
    self.Node.Tracer.add_trace(hex(msg_id)+';'+'SEND' + ';' + 'HELLO' + ';' + str(sys.getsizeof(_buffer)) + ';' + self.bcast_group)
    self._update_visible()
  
  def _setbcast(self, bcast):
    self.bcast_group = bcast

  def _update_visible(self):
    for member in range(len(self.visible)):
      if (self.Node.simulation_seconds - self.visible[member][3] > self.visible_timeout):
        del self.visible[member]
        break

  def _analyse_visible(self):
    for member in range(len(self.visible)):
      found = 0
      for ever_member in range(len(self.ever_visible)):
        if self.visible[member][0] == self.ever_visible[ever_member][0]:
          found = 1
          if self.ever_visible[ever_member][3] != 0:
            #calculate absense
            abesense = int(time.time() * 1000) - self.ever_visible[ever_member][3]
            #store absense for report
            self.visibility_lost.append([self.ever_visible[ever_member][0], abesense])
            self.ever_visible[ever_member][3] = 0
      if found == 0:
        self.ever_visible.append([self.visible[member][0], self.visible[member][1], 0, 0])
    for ever_member in range(len(self.ever_visible)):
      found = 0
      for member in range(len(self.visible)):
        if self.visible[member][0] == self.ever_visible[ever_member][0]:
          found = 1
      if found == 0:
        if self.ever_visible[ever_member][3] == 0:
          self.ever_visible[ever_member][2] += 1
          self.ever_visible[ever_member][3] = int(time.time() * 1000)

  def _print_ever(self):
    for member in self.ever_visible:
      print(member)

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self.printinfo()
      elif command[1] == 'bcast':
        self._setbcast(command[2])
      elif command[1] == 'ever':
        self._print_ever()
      elif command[1] == 'lost':
        for member in self.visibility_lost:
          print(member)
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()  

  def _get_ip(self,iface = 'eth0'):
    'Gets IP address'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
    try:
      res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
      traceback.print_exc()
      return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

class Global():

  def __init__(self, Node, ip):
    'Initializes the properties of the Node object'
    self.scheduler = BackgroundScheduler()
    #### NODE ###############################################################################
    self.Node = Node
    self.visible = [] #our visibble neighbours
    self.ever_visible = [] #our visibble neighbours
    self.visibility_lost = [] #our visibble neighbours
    self.messages_created = [] #messages created by each node
    self.messages = []
    self.average = 0
    self.topology = [] #our visibble neighbours
    #### NETWORK ##############################################################################
    self.ip = ip 
    #### UTILITIES ############################################################################
    self.protocol_stats = [0,0,0,0] #created, forwarded, delivered, discarded
    self.errors = [0,0,0]
    #### Layer specific ####################################################################
    self.packets = 0
    self.traffic = 0
    ##################### END OF DEFAULT SETTINGS ###########################################################
    self._setup()

  ############### Public methods ###########################

  def start(self):
    self.scheduler.start()
    self._generate_members()

  def shutdown(self):
    self.scheduler.shutdown()

  def get_ever_visible(self):
    return self.ever_visible

  def get_servers(self):
    #self._generate_members()
    self.visible = sorted(self.visible, key=itemgetter(3))
    return self.visible

  def update_node(self, ip, latency):
    for node in self.visible:
      if node[0] == ip:
        node[3] = (node[3] + latency) / 2

  def printinfo(self):
    'Prints general information about the node'
    print()
    print("Membership class - Global fixed membership")
    print()

  def printvisible(self):
    print("Visible neighbours at:" + str(self.Node.simulation_seconds) )
    print("===============================================================================")
    print("|IP\t\t|Node ID\t|Load\t\t|Last seen\t|")
    print("-------------------------------------------------------------------------------")
    for member in range(len(self.visible)):
      print ("|"+self.visible[member][0]+"\t|"+str(self.visible[member][1])+"\t\t|"+str(self.visible[member][2])+"\t\t|"+str(self.visible[member][3])+"\t\t|")
    print("===============================================================================")
  
  ############### Private methods ##########################
  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for Membership")
    print()
    print("help                - Print this help message")
    print()

  def _get_ip(self,iface = 'eth0'):
    'Gets IP address'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
    try:
      res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
      traceback.print_exc()
      return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)


  def _generate_members(self):
    self.visible = []
    for i in range(0,self.membership_len):
      if self.network + str(i+1) != self.myip:
        self.visible.append([self.network + str(i+1), 'drone' + str(i), 0 ,0])
    #random.shuffle(self.visible)

  def _setup(self):
    settings_file = open("./classes/membership/settings.json","r").read()
    settings = json.loads(settings_file)
    self.interface_stem = settings['interface']
    if self.interface_stem == "tap":
      interface=self.interface_stem + self.Node.tag[-1]
    elif self.interface_stem == "bat":
      interface=self.interface_stem + '0'
    elif self.interface_stem == "eth":
      interface=self.interface_stem + '0'
    self.myip = self._get_ip(interface)
    self.membership_len = settings['membership_len']
    self.network = settings['network']

  def _print_ever(self):
    for member in self.ever_visible:
      print(member)

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self.printinfo()
      elif command[1] == 'ever':
        self._print_ever()
      elif command[1] == 'lost':
        for member in self.visibility_lost:
          print(member)
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self.printinfo()  

class DBRB():

  def __init__(self, Node, ip ):
    self.Node = Node
    self.ip = ip #ipv4 or ipv6
    self.tag = Node.tag
    ##### Compatibility
    self.visible = [] #this is here for compatibility and is equivalente to CV in DBRB
    self.messages = []
    ##### End compatibility
    self.view = []
    self.recv = []
    self.seq = []
    self.lcseq = ''
    self.format = ''
    self.views = []
    self.debug = False
    self.scheduler = BackgroundScheduler()
    ### Application variables
    self.g_sample = 3
    self.state = "OUT"
    ##################### Constructor actions  #########################
    self._setup()
    self.scheduler.add_job(self._discover, 'interval', seconds=self.discover_interval, id='membership')
    self.scheduler.add_job(self._print_state, 'interval', seconds=2, id='state')

  def start(self):
    self.scheduler.start()
    self.discover_broadcast = network_sockets.UdpInterface(self._discover_handler, debug=False, port=self.membership_port, interface='')
    self.membership_tcp_interface = network_sockets.TcpPersistent(self._membership_handler, debug=False, port=self.membership_port, interface='')
    self.discover_broadcast.start()
    self.membership_tcp_interface.start()
    #self._auto_job()
    #self._initiate()

  def shutdown(self):
    self.scheduler.shutdown()
    self.membership_tcp_interface.shutdown()
    self.discover_broadcast.shutdown()

  def join(self):
    pass

  def leave(self):
    pass

  def least_updated(self, seq):
    pass

  def most_updated(self, seq):
    pass

  def get_current_view(self):
    return self.visible

  def get_servers(self):
    #compatibility
    return self.get_current_view()

  ############ Private ##############################################################################

  def _setup(self):
    settings_file = open("./classes/network/settings.json","r").read()
    settings = json.loads(settings_file)
    self.interface = settings['interface']
    self.membership_len = settings['membership_len']
    self.network = settings['network']
    self.membership_port = 57999
    self.discover_interval = 1
    self.request_timeout = 5
    self.bcast_group = settings['ipv4bcast']

  def _print_state(self):
    log.printxy(3,70,self.state)

  def _create_id(self):
    'Create an CRC32 unique ID'
    return zlib.crc32((str(int(time.time()*1000))+ str(self.tag) + str(random.randint(0,10000))).encode())

  def _pack_cv(self):
    reconfig_packet = pickle.dumps(['CV_PDU', self.visible])
    msg_id = zlib.crc32(str(int(time.time()*1000)).encode())
    signature = self._sign(reconfig_packet)
    buffer = pickle.dumps([signature, reconfig_packet])
    return buffer

  def _pack_reconfig(self):
    reconfig_packet = pickle.dumps([2, self.Node.tag])
    msg_id = zlib.crc32(str(int(time.time()*1000)).encode())
    signature = self._sign(reconfig_packet)
    buffer = pickle.dumps([signature, reconfig_packet])
    return buffer

  def _pack_propose(self):
    pass

  def _pack_converged(self):
    pass

  def _pack_install(self):
    pass

  def _request_membership(self):
    if self.reqlock == True:
      return
    if self.state == 'OUT':
      req_packet = pickle.dumps([1, self.Node.tag])
      msg_id = zlib.crc32(str(int(time.time()*1000)).encode())
      signature = self._sign(req_packet)
      buffer = pickle.dumps([signature, req_packet])
      for member in self.view:
        self.membership_tcp_interface.send(member[0], buffer, msg_id)
      reqtd = threading.Thread(target=self._request_thread, args=(self.quorum,self.sequence,int(time.time()*1000),))
      reqtd.start()
    else:
      return

  def _send_reconfig(self):
    packet = self._pack_reconfig()
    msg_id = zlib.crc32(str(int(time.time()*1000)).encode())
    for process in self.membership:
      self.membership_tcp_interface.send(process, packet, msg_id)

  def _request_thread(self):
    self.reqlock = True
    while self.reqlock:
      if int(time.time()*1000) - start > self.request_timeout:
        self.reqlock = False
        if self.debug: print("Request timeout")
        self.request_buffer = []
        return
      else:
        for req in self.request_buffer:
          self.membership = list(set().union(self.membership, req))
      if len(self.request_buffer) >= len(self.view):
        if self.debug: print("Request finished")
        return
      time.sleep(0.02)

  def _initiate(self):
    for i in range(0,self.membership_len):
      self.visible.append(self.network + str(i+1))
    self.state = 'RUN'

  def _discover(self):
    #onion discover packet
    discover_packet = pickle.dumps(['DISCOVER_PDU', self.Node.tag])
    msg_id = self._create_id()
    signature = self._sign(discover_packet)
    buffer = pickle.dumps([signature, discover_packet])
    if self.state == 'OUT':
      self.discover_broadcast.send(self.bcast_group, buffer, msg_id)

  def _sign(self, message):
    #print("sign->" + str(message))
    digest = SHA256.new()
    try:
      digest.update(message.encode())
    except:
      digest.update(message)
    private_key = False
    with open ("./classes/network/dbrb_private_key.pem", "r") as myfile:
      private_key = RSA.importKey(myfile.read())
    # Load private key and sign message
    signer = PKCS1_v1_5.new(private_key)
    sig = signer.sign(digest)
    #print("sign->" + str(digest.hexdigest()))
    #print("veri->" + str(sig.hex()))
    self.messages.append([message, digest, sig.hex()]) #always add to the end
    return sig.hex()

  def _verify(self, message, sig):
    #print("veri->" + str(sig))
    'Verify a signature against a message'
    #signature must be in bytes. use bytes.fromhex(signagure in hex) before
    #digest = self.messages[index][1]
    digest = SHA256.new()
    try:
      digest.update(message.encode())
    except:
      #already bytes
      digest.update(message)
    #print("veri->" + str(digest.hexdigest()))
    private_key = False
    with open ("./classes/network/dbrb_private_key.pem", "r") as myfile:
        private_key = RSA.importKey(myfile.read())
    # Load public key and verify message
    verifier = PKCS1_v1_5.new(private_key.publickey())
    try:
      verified = verifier.verify(digest, sig)
    except ValueError:
      #traceback.print_exc()
      return False
    except:
      traceback.print_exc()
      return False
    try:
      assert verified, 'Signature verification failed'
    except AssertionError:
      #print('Signature verification failed')
      return False
    return True

  def _discover_handler(self, payload, sender_ip):
    'When a message of type gossip is received from neighbours this method unpacks and handles it'
    #first layer
    payload = pickle.loads(payload)
    msg_id = payload[0]
    #second layer
    payload = pickle.loads(payload[1])
    signature = bytes.fromhex(payload[0])
    message = payload[1]
    #print(str(self._verify(message, signature)))
    if not self._verify(message, signature):
      #pass
      return #invalid, just ignore
    #third layer
    payload = pickle.loads(message)
    pdu = payload[0]
    real_payload = payload[1]
    if (sender_ip != self.Node.Network.myip): #not me
      if pdu == 'DISCOVER_PDU': # Got a discover package
        if len(self.visible) > 0 and self.state == 'RUN': #I'm running and I have a view
          cv_pack = self._pack_cv()
          self.discover_broadcast.send(sender_ip, cv_pack, self._create_id())
        else: #Empty neighbours list, I am out
          return
      elif pdu == 'CV_PDU':
        self.visible = list(set().union(self.visible,payload[1]))
    else:
      return
      
  def _membership_handler(self, payload, sender_ip,connection):
    'When a message of type gossip is received from neighbours this method unpacks and handles it'
    #first layer
    payload = pickle.loads(payload)
    msg_id = payload[0]
    #second layer
    payload = pickle.loads(payload[1])
    signature = bytes.fromhex(payload[0])
    message = payload[1]
    #print(str(self._verify(message, signature)))
    if not self._verify(message, signature):
      #pass
      return #invalid, just ignore
    #third layer
    payload = pickle.loads(message)
    pdu = payload[0]
    real_payload = payload[1]
    if (sender_ip != self.Node.Network.myip): #not me
      if pdu == 1: # Got a request package
        #only act if I am in
        if self.state == 'RUN':
          pass
      elif pdu == 2: #Got a reconfig package
        if self.state == 'RUN':
          pass
      else:
        return

  def _prompt(self, command):
    if (len(command))>=2:
      if command[1] == 'help':
        self._printhelp()
      elif command[1] == 'info':
        self._printinfo()
      elif command[1] == 'init':
        self._initiate()
      elif command[1] == 'view':
        self._printview()
      elif command[1] == 'cv':
        self._printcv()
      elif command[1] == 'sign':
        try:
          print(self._sign(command[2]))
        except:
          traceback.print_exc()
          #self._printhelp()
      elif command[1] == 'verify':
        try:
          message = command[2]
          try:
            sig = bytes.fromhex(command[3])
            result = self._verify(message, sig)
            print(str(result))
          except:
            print("Invalid signature")
        except:
          traceback.print_exc()
          #self._printhelp()
      else:
        print("Invalid Option")
        self._printhelp()
    elif (len(command))==1:
      self._printhelp()


  def _printinfo(self):
    'Prints general information about the node'
    print()
    print("DBRB - Using the OS routing and network")
    print("Node state: " + str(self.state))
    print()

  def _printview(self):
    print("View at:" + str(self.Node.simulation_seconds) )
    print("===============================================================================")
    print("|IP\t\t|Node ID\t|Last seen(s)\t|")
    print("-------------------------------------------------------------------------------")
    for member in range(len(self.view)):
      print ("|"+self.view[member][0]+"\t|"+str(self.view[member][1])+"\t\t|"+str(self.view[member][2])+"\t\t|")
    print("===============================================================================")

  def _printhelp(self):
    'Prints general information about the application'
    print()
    print("Options for [DBRB] membership")
    print()
    print("help                - Print this help message")
    print()

  def _printcv(self):
    for member in self.visible:
      print(member)
