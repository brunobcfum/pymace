#!/usr/bin/env python3

""" 
Traffic application class is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import socket, random, struct, json, traceback, zlib, fcntl, time, threading, pickle, asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from classes import prompt
from ping3 import ping, verbose_ping
from struct import pack
from struct import unpack

class App:

    def __init__(self, Node, tag, time_scale, second):
        'Initializes the properties of the Node object'
        random.seed(tag)
        self.Node = Node
        self.Node.role = "listener"
        self.tag = tag
        self.debug = False
        self.multiplier = time_scale
        self.scheduler = BackgroundScheduler()
        self.bcast_group = '10.0.0.255' #broadcast ip address
        self.port = 56555 # UDP/TCP port
        self.data_port = 56444 # UDP port
        self.max_packet = 1500 #max packet size to listen
        #### APP ################################################################################################
        self.job_queue = {}
        self.job_hist = []
        self.interval = 1
        self.destination = ''
        self.max_count = 5
        self.counter = 0
        self.payload_size = self.max_packet
        self.udp_stat = [0,0]
        self.tcp_stat = [0,0]
        self.pack_pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
        #### DRONE ##############################################################################################
        self.sequence = 0
        self.last_proposal_received = 0
        self.state = "IDLE" #current state
        ##################### END OF DEFAULT SETTINGS ###########################################################
        self._setup()
        self.udp_thread = threading.Thread(target=self._udp_listener, args=())
        self.tcp_thread = threading.Thread(target=self._tcp_listener, args=())
        self.udp_thread.start()
        self.tcp_thread.start()

    ############### Public methods ###########################

    def start(self):
        'Called by main. Starts the application'
        self.scheduler.start()
        # add batch jobs
        self._auto_job()

    def shutdown(self):
        'Called by main. Stops the application'
        self.scheduler.shutdown()
        self.udp_thread.join(timeout = 2)
        self.tcp_thread.join(timeout = 2)

    def printinfo(self):
        'Prints general information about the application'
        print()
        print("Application stats (Traffic)")
        print("State: \t\t" + self.state)
        print("Destination: \t" + self.destination)
        print("Payload size: \t" + str(self.payload_size))
        print("Sent UDP packets: \t" + str(self.udp_stat[0]))
        print("Received UDP packets: \t" + str(self.udp_stat[1]))
        print()

    def _printhelp(self):
        'Prints help information about the application'
        print()
        print("Options for Traffic")
        print()
        print("help                - Print this help message")
        print("info                - Print information regarding application")
        print("ping [destination]  - Send a ping no a IP with timeout of 5")
        print("cancelJob [jobid]   - Cancel a job")
        print("send [dest] [count] [size] [interval] [udp or tcp]\n- Starts sending packets to destination")
        print()

    ############### Public methods ###########################

    def _setup(self):
        'Called by constructor. Finish the initial setup'
        settings_file = open("./classes/apps/traffic/settings.json","r").read()
        settings = json.loads(settings_file)
        self.port = settings['dataPort']
        #self.max_packet = settings['maxUDPPacket']
        self.bcast_group = settings['ipv4bcast']
        self.proposal_timeout = settings['proposalTimeout']
        self.logfile = open(self.tag + "_target_report.csv","w")
        self.Node.role = 'SERVER'

    async def _auto_job_add(self, delay, dest, count, size, interval, jobtype):
        'Adds batch jobs to the scheduler'
        await asyncio.sleep(delay * self.Node.multiplier)
        self._add_job(dest, count, size, interval, jobtype)

    def _auto_job(self):
        'Loads batch jobs from files. File must correspond to node name'
        try:
            jobs_file = open("./classes/apps/traffic/job_" + self.Node.tag + ".json","r").read()
            jobs_batch = json.loads(jobs_file)
            loop = asyncio.get_event_loop()
            for job in jobs_batch["jobs"]:
                loop.create_task(self._auto_job_add(job['start'],job['dest'],job['count'],job['size'],job['interval'],job['type']))
            loop.run_forever()
            loop.close()
        except:
            print("No jobs batch for me")
            pass

    def _udp_listener(self):
        'This method opens a UDP socket to receive data. It runs in infinite loop as long as the node is up'
        addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
        listen_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM) #UDP
        port = self.port + int(self.Node.tag[-1])
        interface='tap' + self.Node.tag[-1]
        listen_socket.bind(('', self.port))
        self.myip = self._get_ip(interface)
        bat_IP = self._get_ip('bat0')
        while self.Node.lock: #this infinity loop handles the received packets
            payload, sender = listen_socket.recvfrom(2048)
            sender_ip = str(sender[0])
            if (sender_ip != self.myip) and (sender_ip != bat_IP):
                self.Node.Membership.packets+=1
                #print('got something...ignoring')
                #self.packets += 1
                self._packet_handler(payload, sender_ip)
        listen_socket.close()

    def _tcp_listener(self):
        'This method opens a TCP socket to receive data. It runs in infinite loop as long as the node is up'
        addrinfo = socket.getaddrinfo(self.bcast_group, None)[1]
        listen_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM) #TCP
        port = self.port + int(self.Node.tag[-1])
        interface='tap' + self.Node.tag[-1]
        self.myip = self._get_ip(interface)
        listen_socket.bind(('', self.port))
        listen_socket.listen(1)
        #this infinity loop handles the received packets
        while self.Node.lock:
            connection, addr = listen_socket.accept()
            try:
                bs = connection.recv(8)
                self.Node.Membership.packets+=1
                (length,) = unpack('>Q', bs)
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
        listen_socket.close()

    def _packet_handler(self, payload, sender_ip):
        'Handles received packet'
        try:
            payload = pickle.loads(payload)
        except:
            payload = json.loads(payload.decode())
        pdu = payload[0]

    def _get_ip(self,iface = 'eth0'):
        'Just gets IP. Should be moved to network class'
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

    def _encode(self, object):
        'Pickle encode object'
        data = pickle.dumps(object)
        size = len(data)
        return data, size

    def _udp_sender(self, jobid, dest, max_count, size):
        'Creates UDP packet'
        self.state = "SENDING"
        self.job_queue[jobid][6] = 'RUNNING'
        msg_id = zlib.crc32(str((self.Node.simulation_seconds)).encode())
        payload = ''
        upd_pack = [1, self.job_queue[jobid][8], int(time.time()), msg_id, payload]
        current_size = len(str(upd_pack))
        if size > self.max_packet:
            size = 1500
        if (size > current_size + 42):
            for i in range(0,size - current_size - 42):
                #add padding to reach size of packet
                payload = payload + random.choice(self.pack_pool)
        upd_pack[4] = payload
        upd_pack = json.dumps(upd_pack).encode()
        self._sender(dest, upd_pack)
        self.job_queue[jobid][8] += 1
        self.udp_stat[0] += 1
        #self.Node.Membership.packets += 1
        self.Node.stats[0] += 1
        if self.job_queue[jobid][8] >= max_count:
            self.state = "IDLE"
            self.job_queue[jobid][6] = 'FINISHED'
            self.scheduler.remove_job(jobid)

    def _tcp_sender(self, jobid, dest, max_count, size):
        'Creates TCP packet'
        self.state = "SENDING"
        self.job_queue[jobid][6] = 'RUNNING'
        msg_id = zlib.crc32(str((self.Node.simulation_seconds)).encode())
        payload = ''
        tcp_pack = [1, self.job_queue[jobid][8], int(time.time()), msg_id, payload]
        current_size = len(str(tcp_pack))
        if (size > current_size + 42):
            for i in range(0,size - current_size - 42):
                #add padding to reach size of packet
                payload = payload + random.choice(self.pack_pool)
        tcp_pack[4] = payload
        tcp_pack = pickle.dumps(tcp_pack)
        self._t_sender(dest, tcp_pack)
        self.job_queue[jobid][8] += 1
        self.tcp_stat[0] += 1
        #self.Node.Membership.packets += 1
        self.Node.stats[0] += 1
        if self.job_queue[jobid][8] >= max_count:
            self.state = "IDLE"
            self.job_queue[jobid][6] = 'FINISHED'
            self.scheduler.remove_job(jobid)

    def _sender(self, destination, bytes_to_send):
        'This method sends the UDP packet'
        addrinfo = socket.getaddrinfo(destination, None)[1] 
        sender_socket = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
        sender_socket.sendto(bytes_to_send, (destination, self.port))
        sender_socket.close()

    def _t_sender(self, destination, bytes_to_send):
        'This method sends the TCP packet'
        length = pack('>Q', len(bytes_to_send))
        addrinfo = socket.getaddrinfo(destination, None)[1] 
        sender_socket = socket.socket(addrinfo[0], socket.SOCK_STREAM)
        sender_socket.settimeout(10)
        try:
            sender_socket.connect((destination, self.port))
            sender_socket.sendall(length)
            sender_socket.sendall(bytes_to_send)
            sender_socket.close()
        except ConnectionRefusedError:
            print('Couldn\'t connect to destination')

    def _ping(self, destination):
        'Pings a node'
        verbose_ping(destination)

    def _set_destination(self, destination):
        'Deprecated'
        self.destination = destination

    def _set_payload(self, size):
        'Deprecated'
        if (int(size) < self.max_packet) and (int(size) > 76):
            self.payload_size = int(size)
        elif int(size) < 76:
            self.payload_size = 76
        else:
            prompt.print_error("Payload exceed max size of: " + str(self.max_packet))

    def _check_payload(self, size):
        'Deprecated'
        if (int(size) < self.max_packet) and (int(size) > 76):
            return int(size)
        elif int(size) < 76:
            return 76
        else:
            prompt.print_error("Payload exceed max size of: " + str(self.max_packet))
            return self.max_packet
    def _check_interval(self, interval):
        'Deprecated'
        if float(interval) > 0.01:
            return float(interval)
        else:
            prompt.print_error("Interval too small")
            return 0.01

    def _set_interval(self, interval):
        'Deprecated'
        if float(interval) > 0.01:
            self.interval = float(interval)
        else:
            prompt.print_error("Interval too small")

    def _add_job(self, dest, max_count, size, interval, jobtype='udp'):
        'Adds manual jobs'
        job_id = hex(zlib.crc32(str((time.time())).encode()))
        self.max_count = max_count
        if jobtype == 'udp':
            try:
                self.job_queue[job_id] = [self.Node.simulation_seconds, job_id, dest, max_count, size, interval,"IDLE", "U", 0]
                self.scheduler.add_job(self._udp_sender, 'interval', seconds = interval, id=job_id, args=[job_id, dest, max_count, size])
            except:
                traceback.print_exc()
        elif jobtype == 'tcp':
            try:
                self.job_queue[job_id] = [self.Node.simulation_seconds, job_id, dest, max_count, size, interval,"IDLE", "T", 0]
                self.scheduler.add_job(self._tcp_sender, 'interval', seconds = interval, id=job_id, args=[job_id, dest, max_count, size])
            except:
                traceback.print_exc()

    def _cancel_job(self, jobid):
        'Cancel a job'
        try:
            self.scheduler.remove_job(jobid)
            self.job_queue[jobid][6] = 'CANCELLED'
        except:
            traceback.print_exc()
            prompt.print_info("Job had already finished.")

    def _prompt(self, command):
        'Application command prompt options. Called from main prompt'
        if (len(command))>=2:
            if command[1] == 'help':
                self._printhelp()
            elif command[1] == 'ping':
                self._ping(command[2])
            elif command[1] == 'queue':
                self._print_queue()             
            elif command[1] == 'listener':
                prompt.print_info('Setting this node as a client')
                self.Node.role = 'LISTENER'
            elif command[1] == 'sender':
                prompt.print_info('Setting this node as a sender')
                self.Node.role = 'SENDER'
            elif command[1] == 'hist':
                self.print_hist()
            elif command[1] == 'debug':
                self.debug = not self.debug
            elif command[1] == 'info':
                self.printinfo()
            elif command[1] == 'dest':
               self._set_destination(command[2])
            elif command[1] == 'payload':
               self._set_payload(command[2])
            elif command[1] == 'interval':
               self._set_interval(command[2])
            elif command[1] == 'cancelJob':
               self._cancel_job(command[2])
            elif command[1] == 'send':
                if (len(command)) == 7:
                    #TODO add more satination
                    size = int(command[4])
                    interval = self._check_interval(command[5])
                    self._add_job(command[2], int(command[3]), size, interval, command[6])
                else:
                    prompt.print_error("Malformed command")
                    self._printhelp()
            else:
                print("Invalid Option")
                self._printhelp()
        elif (len(command))==1:
            self._printhelp()

    def _print_queue(self):
        'Prints current queue'
        print("Current jobs at:" + str(self.Node.simulation_seconds) )
        print("===============================================================================")
        print("|T|St:\t|Job ID\t\t|Dest\t\t|Count\t|Size\t|Int\t|Status\t\t|")
        print("-------------------------------------------------------------------------------")
        for jobid, job in self.job_queue.items():
            print ("|" + job[7] +"|"+str(job[0])+"\t|"+str(job[1])+"\t|"+str(job[2])+"\t|"+str(job[3])+"\t|"+str(job[4])+"\t|"+str(job[5])+"\t|"+job[6]+"\t|")
        print("===============================================================================")
