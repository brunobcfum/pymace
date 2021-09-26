#!/usr/bin/env python3

""" 
RSM Client
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import os, sys
import socket, random, json, traceback, zlib, fcntl, time, threading, pickle, argparse, statistics, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from classes.network import network_sockets
from tqdm import tqdm


class RSMClient:

  def __init__(self, endpoint, port, command, args, times, clients, size, tag):
    'Initializes the properties of the Node object'
    self.name = "RSMClient"
    self.size = size
    self.max_packet = 65535 #max packet size to listen
    self.endpoint = endpoint
    self.port = port
    self.command = command
    self.keyvalue = args
    self.read_results = [0,0]
    self.read_timings = []
    self.threads = []
    self.times = times
    self.clients = clients
    if self.command == 'READ':
      start = time.monotonic_ns()
      for i in range(clients):
        client_thread = threading.Thread(target=self.read_thread, args=())
        client_thread.start()
        self.threads.append(client_thread)
        time.sleep(0.5/1000)
      #self.read_thread()
    if self.command == 'WRITE':
      start = time.monotonic_ns()
      for i in range(clients):
        write_thread = threading.Thread(target=self.write_thread, args=())
        write_thread.start()
        self.threads.append(write_thread)
    for thread in self.threads:
      thread.join()
    end = time.monotonic_ns()
    self.total_time = (end - start) / 1000000
    self.print_results()
    if (self.times * self.clients > 1):
      self.export_results(tag)
    #### NODE ###############################################################################
# END OF DEFAULT SETTINGS ###########################################################

  def read_thread(self):
    read_timings = []
    for i in range(self.times):
      try:
        start = time.monotonic_ns()
        response = self._read(self.keyvalue[0])
        end = time.monotonic_ns()
        total = (end - start) / 1000000
        read_timings.append(total)
        if response != None:
          response = pickle.loads(response)
        else:
          self.read_results[1] +=1
          continue
        #print(str(response) + " -> " + str(total) + " ms")
        if response[0] == 'OK':
          self.read_results[0] +=1
        else:
          self.read_results[1] +=1
      except:
        traceback.print_exc()
        self.read_results[1] +=1
    self.read_timings = self.read_timings + read_timings

  def write_thread(self):
    #time.sleep(random.randint(0,10)/10)
    for i in tqdm(range(self.times)):
      try:
        #print(str(i)+'.', end='')
        start = time.monotonic_ns()
        response = self._write(self.keyvalue[0],self.keyvalue[1])
        end = time.monotonic_ns()
        total = (end - start) / 1000000
        self.read_timings.append(total)
        if response != None:
          response = pickle.loads(response)
        else:
          response = ['ERROR']
        #print(str(response) + " -> " + str(total) + " ms")
        if response[0] == 'OK':
          self.read_results[0] +=1
        else:
          self.read_results[1] +=1
      except:
        traceback.print_exc()
        self.read_results[1] +=1

  def who_is_leader(self):
    pass

  def print_results(self):
      print("Results")
      print("####################################################")
      print()
      print("Succesful: " + str(self.read_results[0]))
      print("Failed: " + str(self.read_results[1]))
      if (self.times * self.clients > 1):
        self.print_statistics()

  def print_statistics(self):
    try:
      print("Mean latency: " + str(statistics.mean(self.read_timings))     + " ms")
      print("Median latency: " + str(statistics.median(self.read_timings)) + " ms")
      print("Std dev latency: " + str(statistics.stdev(self.read_timings)) + " ms")
      print("Max latency: " + str(max(self.read_timings))                  + " ms")
      print("Min latency: " + str(min(self.read_timings))                  + " ms")
      print("Throughput: " + str((self.times * self.clients) / (self.total_time/1000)) + " ops/s")
    except statistics.StatisticsError:
      print("Too few runs to create statistic results")

  def export_results(self, manual_tag):
    filename = "./results/result_" + manual_tag + ".csv"
    if os.path.isfile(filename):
      export_file = open(filename,"a")
    else:
      export_file = open(filename,"w")
      export_file.write('datetime;repetitions;size;mean latency;median latency;std dev latency; max latency; min latency; throughput\n') #datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    export_file.write(str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))    )
    export_file.write(";" + str(self.times)                                         )
    export_file.write(";" + str(self.size)                                          )
    export_file.write(";" + str(statistics.mean(self.read_timings))                 )
    export_file.write(";" + str(statistics.median(self.read_timings))               )
    export_file.write(";" + str(statistics.stdev(self.read_timings))                )
    export_file.write(";" + str(max(self.read_timings))                             )
    export_file.write(";" + str(min(self.read_timings))                             )
    export_file.write(";" + str(self.times / (sum(self.read_timings) / 1000)) + "\n")
    export_file.flush()
    export_file.close()

  def _create_id(self):
    return zlib.crc32((str(time.time() * 1000)+ str('client') + str(random.randint(0,10000))).encode())

    ###############################################################################################
   
  def _write(self, key, value):
    bytes_to_send = pickle.dumps(['WRITE' , key, value])
    try:
      response = network_sockets.TcpPersistent.send(self, self.endpoint, bytes_to_send, self._create_id())
      return response
    except:
      pass


  def _read(self, key):
    bytes_to_send = pickle.dumps(['READ' , key])
    response = network_sockets.TcpPersistent.send(self, self.endpoint, bytes_to_send, self._create_id())
    return response

def _create_payload(char_tumble, size):
  return ''.join(random.choice(char_tumble) for i in range(size))

if __name__ == '__main__':  #for main run the main function. This is only run when this main python file is called, not when imported as a class
    try:
        print("Genesis v." + __version__ + " - RSM client")
        print()

        parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')

        parser.add_argument("command", help="Command: read of write", choices=['read', 'write'])
        parser.add_argument("key", help="New application name", nargs='?')
        parser.add_argument("value", help="New application name", nargs='?')
        parser.add_argument("-e", "--endpoint", type=str, help="End-point to connect", default="localhost")
        parser.add_argument("-p", "--port", type=int, help="Communication port", default=56444)
        parser.add_argument("-r", "--rep", type=int, help="Repetitions", default=1)
        parser.add_argument("-c", "--clients", type=int, help="Clients", default=1)
        parser.add_argument("-s", "--size", type=int, help="Value size", default=1)
        parser.add_argument("-t", "--tag", type=str, help="Manual tag", default="tag")

        args = parser.parse_args()
        char_tumble = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*?/"

        if args.command.upper() == 'READ':
          if args.key == None:
            print('Missing key to read.')
            sys.exit(0)
          else:
            key = args.key
            value = 0

        if args.command.upper() == 'WRITE':
          if args.key == None:
            print('Missing key to write.')
            sys.exit(0)
          else:
            key = args.key
          if args.value == None:
            print('Missing value to write. Generating based in passed size.')
            value = _create_payload(char_tumble, args.size)
            #print(value)
          else:
            value = args.value

        #print(args)
        client = RSMClient(args.endpoint, args.port, args.command.upper(), [key,value], args.rep, args.clients, args.size, args.tag)
        #############################################################################
    except KeyboardInterrupt:
      print("Interrupted by ctrl+c")
