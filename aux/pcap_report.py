#!/usr/bin/env python3

import dpkt
import os, math, struct, sys, json, traceback, time, argparse, statistics, datetime
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import struct
from operator import itemgetter


matplotlib.rcParams['mathtext.fontset'] = 'custom'
matplotlib.rcParams['mathtext.rm'] = 'Bitstream Vera Sans'
matplotlib.rcParams['mathtext.it'] = 'Bitstream Vera Sans:italic'
matplotlib.rcParams['mathtext.bf'] = 'Bitstream Vera Sans:bold'


class PcapReport ():

  def __init__ (self,folder=''):
    print("Preparing report on folder: " + folder)
    self.folder = folder
    try:
      self. net_traces = self.load_net_traces_tomem()
      pass
    except:
      #pass
      traceback.print_exc()
    try:
      self.convert_to_json()
      #print(self.get_json_dissects())
      pass
    except:
      #pass
      traceback.print_exc()
    try:
      #self.parse_json_files()
      pass
    except:
      #pass
      traceback.print_exc()
    try:
      self.parse_for_waterfall()
      pass
    except:
      #pass
      traceback.print_exc()

  def dict_raise_on_duplicates(self,ordered_pairs):
    """Reject duplicate keys."""
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           pass
           #raise ValueError("duplicate key: %r" % (k,))
        else:
           d[k] = v
    return d

  def mac_addr(self,address):
    """Convert a MAC address to a readable/printable string
       Args:
           address (str): a MAC address in hex form (e.g. '\x01\x02\x03\x04\x05\x06')
       Returns:
           str: Printable/readable MAC address
    """
    return ':'.join('%02x' % dpkt.compat_ord(b) for b in address)

  def inet_to_str(self, inet):
    """Convert inet object to a string

        Args:
            inet (inet struct): inet network address
        Returns:
            str: Printable/readable IP address
    """
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)

  def convert_to_json(self):
    print("Converting pcap files to json")
    temp_list = []
    pcap_traces = []
    for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
      temp_list.extend(filenames)

    for file in temp_list:
      if len(file.split(".")) == 2:
        if file.split(".")[1] == "pcap":
            pcap_traces.append(file)

    for trace in pcap_traces:
      os.system("tshark -r " + self.folder+"/tracer/"+trace + " -V -Tjson > " + self.folder+"/tracer/"+trace + ".json")
  
  def get_json_dissects(self):
    temp_list = []
    json_traces = []
    for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
      temp_list.extend(filenames)

    for file in temp_list:
      if len(file.split(".")) == 3:
        if file.split(".")[2] == "json":
          json_traces.append(self.folder+"/tracer/" +file)
    return json_traces

  def load_net_traces_tomem(self):
    print("Loading net traces to memory")
    temp_list = []
    net_traces = []
    traces_per_node = {}
    for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
      temp_list.extend(filenames)

    for file in temp_list:
      if file.split("_")[0] == "net":
        net_traces.append(self.folder+"/tracer/" +file)

    for trace in net_traces:
      print(trace)
      current_node = trace.split(".")[1].split("/")[5].split("_")[2]
      netfile = open(trace,'r').read()
      traces_per_node[current_node] = netfile

    return traces_per_node

  def get_type_my_msgid(self, msgid, node):
    command_idx = 0
    _type = "---"
    for key in self.net_traces:
      if key == node:
        trace = self.net_traces[key].split(";")
        try:
          command_idx = trace.index(msgid)
        except ValueError:
          pass
        if command_idx > 0:
          _type = trace[command_idx+2]
        return _type

  def parse_for_waterfall(self):
    print("Parsing dissects #2")
    nodes = {}
    rows = {}
    columns = []
    first = True
    delta = 1
    json_dissect = ''
    files = self.get_json_dissects()
    total_drones = len(files)
    for file in files:
      current_node = file.split(".")[1].split("/")[5]
      columns.append(current_node)
      jsonfile = open(file,'r').read()
      try:
        json_dissect = json.loads(jsonfile, object_pairs_hook=self.dict_raise_on_duplicates)
      except:
        pass
      counter = 0
      packet = json_dissect[0]
      old_time = int(float(packet['_source']['layers']['frame']['frame.time_relative']))
      for packet in json_dissect:
        #print(packet['_source']['layers']['data']['data.data'])
        try:
          #check if there is data
          time = packet['_source']['layers']['frame']['frame.time_relative']
          data = packet['_source']['layers']['data']['data.data']
          #print(data.replace(":", ""))
          #data = data.replace(":", "")
          #string_data = str(''.join([chr(int(''.join(c), 16)) for c in zip(data[0::2],data[1::2])]))
          #teste = bytearray.fromhex(data).decode('hex')
          #splitdata = data.split(":")
          #start=string_data.find("0x")
          #msg_id = string_data[start:start+10]
          if (math.floor(float(time)) >= (old_time) + delta) and not first:
            try:
              rows[old_time][columns.index(current_node)] = counter
              nodes[current_node].append([old_time, counter])
            except:
              rows[old_time] = [0] * total_drones
              rows[old_time][columns.index(current_node)] = counter
              nodes[current_node] = []
              nodes[current_node].append([old_time, counter])
            gap = math.floor(float(time)) - old_time + delta
            #fill gaps with zeros
            for i in range(1,gap-1,delta):
              try:
                nodes[current_node].append([old_time+i, 0])
                rows[old_time+i][columns.index(current_node)] = 0
              except:
                rows[old_time+i] = [0] * total_drones
                #rows[old_time+i][columns.index(current_node)] = 0
                nodes[current_node] = []
                nodes[current_node].append([old_time+i, 0])
            counter = 1
            old_time = math.floor(float(time))
          else:
            counter += 1
            first = False
          #print(string_data[start:start+10])
          #if current_node == "drone0": print(int(float(time)))
          #if current_node == "drone0": print(time)
          #if current_node == "drone0": print(math.floor(float(time)))
        except KeyError:
          pass
        except:
          #pass
          traceback.print_exc()
          #print("nodata")
      try:
        nodes[current_node].append([old_time, counter])
        rows[old_time][columns.index(current_node)] = counter
      except:
        rows[old_time] = [0] * total_drones
        rows[old_time][columns.index(current_node)] = counter
        nodes[current_node] = []
        nodes[current_node].append([old_time, counter])
    max = 0
    for key in nodes:
      if len(nodes[key]) > max: max = len(nodes[key])
    for key in nodes:
      oldlen=len(nodes[key])
      if len(nodes[key]) < max:
        gap = max - len(nodes[key])
        for i in range(gap):
          nodes[key].append([nodes[key][oldlen-1][0] + (i+1), 0])

    #transforming data
    #print(columns)
    #print(rows)
    df = pd.DataFrame.from_dict(rows,orient='index', columns=columns )
    df2 = pd.DataFrame.from_dict(nodes)
    fig, ax = plt.subplots(figsize=(12,25))         # Sample figsize in inches
    g = sns.heatmap(df, cmap="YlGnBu", ax=ax, square= False, cbar_kws={"orientation": "horizontal","label": "Number of packets"})#, annot=True, cbar=False)
    #plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = False, labeltop=True)
    plt.xticks(rotation=60)
    plt.yticks(rotation=0)
    #g.set_yticklabels(g.get_yticklabels(), rotation=30) 
    ax.set_title('Application packets per node in time', fontsize = 25, fontweight="bold")
    plt.ylabel('Simulation time(s)')
    plt.xlabel('Node')
    plt.savefig(self.folder+'/network_heatmap.png')
    #plt.show()
    #print(df)
    #print(nodes['drone0'])


  def parse_json_files(self):
    print("Parsing dissects #1")
    messages = {}
    json_dissect = ''
    files = self.get_json_dissects()
    for file in files:
      current_node = file.split(".")[1].split("/")[5]
      jsonfile = open(file,'r').read()
      try:
        json_dissect = json.loads(jsonfile, object_pairs_hook=self.dict_raise_on_duplicates)
      except:
        pass
      for packet in json_dissect:
        #print(packet['_source']['layers']['data']['data.data'])
        try:
          data = packet['_source']['layers']['data']['data.data']
          #print(data.replace(":", ""))
          data = data.replace(":", "")
          string_data = str(''.join([chr(int(''.join(c), 16)) for c in zip(data[0::2],data[1::2])]))
          #teste = bytearray.fromhex(data).decode('hex')
          #splitdata = data.split(":")
          start=string_data.find("0x")
          msg_id = string_data[start:start+10]
          prev_hop = packet['_source']['layers']['eth']['eth.src']
          next_hop = packet['_source']['layers']['eth']['eth.dst']
          ip_src = packet['_source']['layers']['ip']['ip.src']
          ip_dst = packet['_source']['layers']['ip']['ip.dst']
          frame = packet['_source']['layers']['frame']['frame.number']
          command = self.get_type_my_msgid(msg_id, current_node)
          try:
            messages[msg_id].append([packet['_source']['layers']['frame']['frame.time_epoch'], prev_hop, next_hop, ip_src, ip_dst, current_node, frame, command])
          except:
            messages[msg_id] = []
            messages[msg_id].append([packet['_source']['layers']['frame']['frame.time_epoch'], prev_hop, next_hop, ip_src, ip_dst, current_node, frame, command])
          #print(string_data[start:start+10])
        except KeyError:
          pass
        except:
          #pass
          traceback.print_exc()
          #print("nodata")
    self.add_message_type(messages)
  
  def add_message_type(self, messages):
    print("Adding message type")
    temp_list = []
    net_traces = []

    for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
      temp_list.extend(filenames)

    for file in temp_list:
      if len(file.split(".")) == 2:
        if file.split(".")[1] == "pcap":
          net_traces.append(file)
    for key in messages:
      pass
      #search for message in traces
    self.export_trace(messages)

  def export_trace(self, messages):
    print("Creating messages folder")
    try:
      os.mkdir(self.folder + "/tracer/messages")
    except FileExistsError:
      print("Folder already created")
    print("Exporting messages to individual files")
    prevtime = 0
    delta = 0
    for key in messages:
      file = open(self.folder + "/tracer/messages/" + key + ".csv",'w')
      value = messages[key]
      value = sorted(value, key=itemgetter(0))
      file.write("time; time_delta(ms); source_ip; dest_ip; prev_node_tag;current_node_tag; frame_number;prev_hop; current_hop; command \n")
      for time in value:
        #prev_node = 'drone' + str(int(time[1].split(":")[5])-1)
        prev_node = "-"
        if prev_node == str(time[5]):
          prev_node = "-"
        if prevtime > 0:
          delta = float(time[0]) - prevtime
        file.write(str(time[0]) + ";" + str(delta*1000) + ";"  + str(time[3])+ ";" + str(time[4])+ ";" + prev_node + ";" + str(time[5])+ ";" + str(time[6]) + ";" + str(time[1])+ ";" + str(time[2])+ ";" + str(time[7])+ "\n")
        prevtime = float(time[0])
      prevtime = 0
      delta = 0
      file.flush()
      file.close()

  def parse_file(self):
    temp_list = []
    pcap_traces = []
    node_report = {}
    node_report['node'] = []
    node_report['type'] = []
    node_report['packets'] = []

    for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
      temp_list.extend(filenames)

    for file in temp_list:
      if len(file.split(".")) == 2:
        if file.split(".")[1] == "pcap":
            pcap_traces.append(file)

    for trace in pcap_traces:
      counter=0
      ipcounter=0
      tcpcounter=0
      udpcounter=0
      pcapfile = open(self.folder+"/tracer/"+trace,'rb')
      print(pcapfile.name)
      pcap = dpkt.pcap.Reader(pcapfile)
      for ts, pkt in pcap:
        if counter == 0:
          timezero = ts
        counter+=1
        eth=dpkt.ethernet.Ethernet(pkt)
        if eth.type == 17157:
          batman  = eth.data
          print(eth.data)
          #BATMAN encapsulated
          #print('Timestamp: ', str(datetime.datetime.utcfromtimestamp(ts)))
          print("source->" + self.mac_addr(eth.src))
          print(eth.src)
          teste = struct.unpack(str(len(batman)) + 'c',batman)
          print(len(list(teste)))
          for byte in batman:
            print(self.inet_to_str(byte))
          return
          #print("source->" + self.mac_addr(eth.src))
          #print("dst   ->" + self.mac_addr(eth.dst))
        if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
          #print("aqui")
          continue
        
        ip=eth.data
        ipcounter+=1

        if ip.p==dpkt.ip.IP_PROTO_TCP: 
          tcpcounter+=1

        if ip.p==dpkt.ip.IP_PROTO_UDP:
          udpcounter+=1

        data = ip.data
        print("packet size = " + str(len(data)))
      node_report['node'].append(trace.split(".")[0])
      node_report['type'].append('ip')
      node_report['packets'].append(ipcounter)
      node_report['node'].append(trace.split(".")[0])
      node_report['type'].append('tcp')
      node_report['packets'].append(tcpcounter)
      node_report['node'].append(trace.split(".")[0])
      node_report['type'].append('udp')
      node_report['packets'].append(udpcounter)

    df = pd.DataFrame(data=node_report)
    g = sns.catplot(x='node', y='packets', hue='type', data=df, kind='bar')
    g._legend.remove()
    #plt.figure(figsize=(6,3))
    plt.grid(which='major', axis='both')
    plt.title('Packets per node')
    plt.ylabel('packets')
    plt.xlabel('Node')
    plt.xticks(rotation=60)

    #
    plt.tight_layout()
    plt.legend()
    plt.savefig(self.folder+'/packet_overview.png')
    #plt.show()
    plt.close()


if __name__ == '__main__':  #for main run the main function. This is only run when this main python file is called, not when imported as a class
  print("Reporter - Report generator for Genesis")
  print()
  folders = []
  sorted_folders = []
  parser = argparse.ArgumentParser(description='Options as below')
  parser.add_argument('indir', type=str, help='Input dir where reports are located')
  parser.add_argument('-t','--type', type=str, help='type of report', default="loss", choices=['loss'])
  parser.add_argument('-a','--all', help='process all report folders', dest='all', action='store_true')
  parser.add_argument('-l','--last', help='process last report folder', dest='last', action='store_true')
  parser.add_argument('-d','--date', help='date/time to be processed', dest='date', type=str, default=False)
  arguments = parser.parse_args()

  for (dirpath, dirnames, filenames) in os.walk(arguments.indir):
    folders.extend(dirnames)
    break

  for folder in folders:
    sorted_folders.append(folder)
  sorted_folders = sorted(sorted_folders)

  if (arguments.last == True):
    folder = arguments.indir+'/'+sorted_folders[len(sorted_folders)-1]
    report = PcapReport(folder)
    #print(path+'/'+folders[len(folders)-1])
  elif (arguments.all == True):
    for simulation in sorted_folders:
      folder = arguments.indir+'/'+simulation
      #print(folder)
      report = PcapReport(folder)
  elif (arguments.date != False):
    for simulation in sorted_folders:
      if (simulation == arguments.date):
        folder = arguments.indir+'/'+simulation
        #print(path+'/'+simulation)
        report = PcapReport(folder)
  sys.exit()