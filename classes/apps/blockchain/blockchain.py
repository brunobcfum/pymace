#!/usr/bin/env python3

""" 
Shareview application class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, os, math, random, struct, sys, json, traceback, zlib, fcntl, time, psutil, threading, cv2, base64, pickle, asyncio, hashlib
from apscheduler.schedulers.background import BackgroundScheduler
from collections import deque
from classes import prompt
from struct import pack, unpack
from ping3 import ping, verbose_ping

class App:

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.Node.role = "node"
        self.tag = tag
        self.debug = False
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        self.bcast_group = '10.0.1.255' #broadcast ip address
        self.main_port = 56555 # UDP port
        self.data_port = 56444 # UDP port
        self.task_port = 56444 # UDP port
        self.max_packet = 1500 #max packet size to listen
        #### APP ################################################################################################
        self.blockchain = []
        self.transactions_cache = []
        #### DRONE ##############################################################################################
        self.state = "IDLE" #current state
        ##################### END OF DEFAULT SETTINGS ###########################################################
       #self._setup()
        self.udp_thread = threading.Thread(target=self._udp_listener, args=())
        self.tcp_thread = threading.Thread(target=self._tcp_listener, args=())
        self.udp_thread.start()
        self.tcp_thread.start()

    ############### Public methods ###########################

    def start(self):
        self.scheduler.start()
        self._connect_peers()
        if (not self._check_blockchain()):
            self._genesis_block()
        #self._auto_job()

    def shutdown(self):
        self.scheduler.shutdown()
        self.udp_thread.join(timeout = 2)
        self.tcp_thread.join(timeout = 2)

    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (BlockChain)")
        print("State: \t\t" + self.state)
        print("Stub: \t" + self.state)
        print("Stub: \t" + str(self.state))
        print("Stub: \t" + str(self.state))
        print("Stub: \t" + str(self.state))
        print()

    def _printhelp(self):
        'Prints general information about the application'
        print()
        print("Options for Traffic")
        print()
        print("help                - Print this help message")
        print("info                - Print information regarding application")
        print("record [data]       - Record new data")
        print("block               - Add record transactions cache in a new block")
        print("mine                - Mine for new block")
        print("chain               - Print blockchain")
        print("buffer              - Print record transactions cache")
        print()

    def tracer(self):
        pass

    ############### Public methods ###########################

    def _connect_peers(self):
        prompt.print_info("Connecting to peers...")

    def _genesis_block(self):
        print("Creating genesis block")
        self._new_block(previous_hash=1, proof=100)

    def _new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        prompt.print_info("Adding new block with proof: " + str(proof))
        #TODO How to make this atomic
        block = {
            'index': len(self.blockchain) + 1,
            'timestamp': int(time.time()),
            'transactions': self.transactions_cache,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.blockchain[-1]),
        }

        # Reset the current list of transactions
        self.transactions_cache = []

        self.blockchain.append(block)
        return block

    def _proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        prompt.print_info("Found proof")
        return proof

    def _record(self, type, value):
        new_record = {
            'Type': type,
            'Value': value
        }
        self.transactions_cache.append(new_record)
        return self._last_block['index'] + 1

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        #NOTE: all nodes iterate in the same way. someone might finish before
        guess = f'{last_proof}{proof}'.encode() #creates a string that joins lastproof and current proof number
        guess_hash = hashlib.sha256(guess).hexdigest()
        #print(guess_hash)
        return guess_hash[:4] == "cafe"

    @staticmethod
    def _hash_block(block):
        # Hashes a Block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def _last_block(self):
        # Returns the last Block in the chain
        return self.blockchain[-1]

    def _check_blockchain(self):
        'Start with the basics. If my blockchain is empty or there is no blockchain or I am not in sync.'
        #loop = asyncio.get_event_loop()
        #loop.create_task(self._check_sync())
        #loop.run_forever()
        #loop.close()
        if len(self.blockchain)==0:
            return False
        return True

    async def _check_sync(self):
        'Go in my list of neighbours and ask the ID of the last block'

    def _setup(self):
        settings_file = open("./classes/apps/traffic/settings.json","r").read()
        settings = json.loads(settings_file)
        self.port = settings['controlPort']
        self.data_port = settings['dataPort']
        self.bcast_group = settings['ipv4bcast']
        self.proposal_timeout = settings['proposalTimeout']
        ret=cv2.setNumThreads(1)
        ret=cv2.setUseOptimized(False)
        self.logfile = open(self.tag + "_target_report.csv","w")
        self.Node.role = 'SERVER'

    def _udp_listener(self):
        'This method opens a UDP socket to receive data. It runs in infinite loop as long as the node is up'
        addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
        listen_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM) #UDP
        port = self.main_port + int(self.Node.tag[-1])
        interface='tap' + self.Node.tag[-1]
        listen_socket.bind(('', self.main_port))
        self.myip = self._get_ip(interface)
        while self.Node.lock: #this infinity loop handles the received packets
            payload, sender = listen_socket.recvfrom(self.max_packet)
            sender_ip = str(sender[0])
            self.Node.Membership.packets+=1
            #print('got something...ignoring')
            #self.packets += 1
            self._packet_handler(payload, sender_ip)
        listen_socket.close()

    def _tcp_listener(self):
        'This method opens a TCP socket to receive data. It runs in infinite loop as long as the node is up'
        addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
        listen_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM) #TCP
        port = self.main_port + int(self.Node.tag[-1])
        interface='tap' + self.Node.tag[-1]
        self.myip = self._get_ip(interface)
        listen_socket.bind((self.myip, self.main_port))
        listen_socket.listen(1)
        while self.Node.lock: #this infinity loop handles the received packets
            connection, addr = listen_socket.accept()
            try:
                bs = connection.recv(8)
                self.Node.Membership.packets+=1
                (length,) = unpack('>Q', bs)
                bs = connection.recv(10)
                self.Node.Membership.packets+=1
                data = b''
                while len(data) < length:
                    to_read = length - len(data)
                    data += connection.recv(4096 if to_read > 4096 else to_read)
                    self.Node.Membership.packets+=1
                assert len(b'\00') == 1
                connection.sendall(b'\00')
            finally:
                connection.close()

            #dosomethingwith data
            new_crc = hex(zlib.crc32(data))
            new_file = pickle.loads(data)
            for job in self.job_queue:
                if job[0] == jobid:
                    job[3].append(new_file)
            self.complete_files.append([jobid, new_file])
        listen_socket.close()

    def _packet_handler(self, payload, sender_ip):
        'When a message of type gossip is received from neighbours this method unpacks and handles it'
        'This should be in routing layer'
        try:
            payload = pickle.loads(payload)
        except:
            payload = json.loads(payload.decode())
        pdu = payload[0]

    def _get_ip(self,iface = 'eth0'):
        'This should be in routing layer'
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

    def _shareDataTCP(self, data, size, job, destination):
        job = pack('>10s', job[0].encode())
        length = pack('>Q', size)
        addrinfo = socket.getaddrinfo(destination, None)[1] 
        sender_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM)
        sender_socket.settimeout(10)
        sender_socket.connect((destination, self.data_port))
        sender_socket.sendall(length)
        sender_socket.sendall(job)
        #sender_socket.setblocking(False)
        sender_socket.sendall(data)
        #sender_socket.shutdown(SHUT_WR)
        sender_socket.close()

    def _encode(self, object):
        data = pickle.dumps(object)
        size = len(data)
        return data, size

    def _udp_sender(self, jobid, dest, max_count, size):
        'Redo'
        self.state = "SENDING"
        self.job_queue[jobid][6] = 'RUNNING'
        payload = ''
        for i in range(0,size - 34 - 42):
            payload = payload + random.choice(self.pack_pool)
        msg_id = zlib.crc32(str((self.Node.simulation_seconds)).encode())
        #TODO variable counter size
        upd_pack = [1, self.job_queue[jobid][8], int(time.time()), msg_id, payload]
        upd_pack = json.dumps(upd_pack).encode()
        self._sender(dest, upd_pack)
        self.job_queue[jobid][8] += 1
        self.udp_stat[0] += 1
        self.Node.Membership.packets += 1
        self.Node.stats[0] += 1
        if self.job_queue[jobid][8] >= max_count:
            self.state = "IDLE"
            self.job_queue[jobid][6] = 'FINISHED'
            self.scheduler.remove_job(jobid)

    def _sender(self, destination, bytes_to_send):
        'This method sends the bytes'
        addrinfo = socket.getaddrinfo(destination, None)[1] 
        sender_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
        sender_socket.sendto(bytes_to_send, (destination, self.main_port))
        sender_socket.close()

    def _ping(self, destination):
        verbose_ping(destination)

    def _check_payload(self, size):
        if (int(size) < self.max_packet) and (int(size) > 76):
            return int(size)
        elif int(size) < 76:
            return 76
        else:
            prompt.print_error("Interval too small exceed max size of: " + str(self.max_packet))
            return self.max_packet
    def _check_interval(self, interval):
        if float(interval) > 0.01:
            return float(interval)
        else:
            prompt.print_error("Interval too small")
            return 0.01

    #def _add_transaction(self, dest, max_count, size, interval, jobtype='udp'):
    #    job_id = hex(zlib.crc32(str((time.time())).encode()))
    #    self.max_count = max_count
    #    if jobtype == 'udp':
    #        try:
    #            self.job_queue[job_id] = [self.Node.simulation_seconds, job_id, dest, max_count, size, interval,"IDLE", "U", 0]
    #            self.scheduler.add_job(self._udp_sender, 'interval', seconds = interval, id=job_id, args=[job_id, dest, max_count, size])
    #        except:
    #            traceback.print_exc()
    #    elif jobtype == 'tcp':
    #        pass

    def _prompt(self, command):
        if (len(command))>=2:
            if command[1] == 'help':
                self._printhelp()
            elif command[1] == 'ping':
                self._ping(command[2])         
            elif command[1] == 'block':
                last_block = self._last_block
                print(last_block)
                last_proof = last_block['proof']
                print(last_proof)
                previous_hash = self._hash_block(last_block)
                print(previous_hash)
                self._new_block(self._proof_of_work(last_proof), previous_hash)
            elif command[1] == 'debug':
                self.debug = not self.debug
            elif command[1] == 'info':
                self.printinfo()
            elif command[1] == 'chain':
                self._print_chain()
            elif command[1] == 'cache':
                self._print_cache()
            elif command[1] == 'record':
                if (len(command)) == 4:
                    #TODO implement
                    #size = self._check_payload(command[4])
                    #interval = self._check_interval(command[5])
                    #self._add_job(command[2], int(command[3]), size, interval, command[6])
                    self._record(command[2], command[3])
                else:
                    prompt.print_error("Malformed command")
                    self._printhelp()
            else:
                print("Invalid Option")
                self._printhelp()
        elif (len(command))==1:
            self._printhelp()

    def _print_queue(self):
        print("Current jobs at:" + str(self.Node.simulation_seconds) )
        print("===============================================================================")
        print("|T|St:\t|Job ID\t\t|Dest\t\t|Count\t|Size\t|Int\t|Status\t\t|")
        print("-------------------------------------------------------------------------------")
        for jobid, job in self.job_queue.items():
            print ("|" + job[7] +"|"+str(job[0])+"\t|"+str(job[1])+"\t|"+str(job[2])+"\t|"+str(job[3])+"\t|"+str(job[4])+"\t|"+str(job[5])+"\t|"+job[6]+"\t|")
        print("===============================================================================")

    def _print_chain(self):
        print("Current chain at:" + str(self.Node.simulation_seconds) )
        print(self.blockchain)

    def _print_cache(self):
        print("Current buffer at:" + str(self.Node.simulation_seconds) )
        print(self.transactions_cache)







