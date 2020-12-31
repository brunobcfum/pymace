#!/usr/bin/env python3 

""" 
Report scripts is part of a thesis work about distributed systems 
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

# TODO #
# Remove / from the end of indir

libnames = ['pandas']
import sys
for libname in libnames:
    try:
        lib = __import__(libname)
    except:
        print (sys.exc_info())
    else:
        globals()[libname] = lib

import os, math, struct, sys, json, traceback, time, argparse, statistics
import matplotlib.pyplot as plt
import numpy as np
pd = pandas
import numpy_indexed as npi

class Report ():

    def __init__ (self,folder=''):
        print("Preparing report on folder: " + folder)
        self.folder = folder
        try:
            #self.network_comm_loss()
            pass
        except:
            pass
            #traceback.print_exc()
            #sys.exit()

        try:
            self.paxos_quorum()
            pass
        except:
            #pass
            traceback.print_exc()
            #sys.exit()

    def paxos_quorum(self):
        paxos_traces = []
        temp_list = []
        time = []
        quorum_evolution = []
        node_quorum = {}
        for (dirpath, dirnames, filenames) in os.walk(self.folder+"/tracer/"):
            temp_list.extend(filenames)
        for file in temp_list:
            if file.split("_")[0] == "status":
                paxos_traces.append(file)
        for file in paxos_traces:
            node_name = file.split("_")[2]
            node_name = node_name.split(".")[0]
            node_quorum[node_name] = []
            #print(node_name)
            paxos_status_file = open(self.folder+"/tracer/"+file,"r")
            paxos_status = paxos_status_file.readlines()
            #print(paxos_status)
            for line in range(1,len(paxos_status)):
                time = paxos_status[line].split(";")[0]
                quorum = paxos_status[line].split(";")[6]
                node_quorum[node_name].append((int(time)/1000, int(quorum)))
                #print(paxos_status[line].split(";")[6])
                #pass
            quorum_evolution.append(node_quorum)
            #print(node_quorum)
            node_quorum = {}

        plt.style.use('ggplot')
        plt.title('Quorum evolution')
        plt.ylabel('Voters')
        plt.xlabel('Time(s)')
        
        #time = list(map (int, battery_data_lines[len(battery_data_lines)-1]))
        #print (time)
        #for i in range(0,len(battery_data_lines)-1):
        #    if i != len(battery_data_lines)-1:
        #        battery_data_lines[i].pop(0)
        #    results = list(map(float, battery_data_lines[i]))
            #print(battery_data_lines[len(battery_data_lines)-1])
        #
        for node in quorum_evolution:
            #print(node)
            for key in node:
                #print(*zip(*node[key]))
                plt.plot(*zip(*node[key]), label = key)


        plt.tight_layout()
        plt.legend()
        plt.savefig(self.folder+'/quorum_evolution.png')
        plt.close()
        #print(quorum_evolution)
        


    def network_comm_loss(self):
        #Creates a box plot for each node, showing their neighbohood communication loss
        #read trace files
        net_traces = []
        temp_boxes = {}
        for (dirpath, dirnames, filenames) in os.walk(self.folder+"/net_dumps/"):
            net_traces.extend(filenames)
        #print(net_traces)
        for trace in net_traces:
            node_name = trace.split('_')[2]
            temp_data = []
            #print(trace)
            net_report_file = open(self.folder+"/net_dumps/"+trace,"r")
            net_report_file = net_report_file.readlines()
            #print(net_report_file.read())
            #df = pd.DataFrame(net_report_file, columns=['Node IP', 'Out for'])
            #df.plot.box(grid='True')
            for line in range(len(net_report_file)):
                if line != 0:
                    data = net_report_file[line].split(";")
                    data[1] = int(data[1])
                    temp_data.append(data)
            myIndexes = []
            for line in range(len(temp_data)):
                if temp_data[line][0] not in myIndexes:
                    myIndexes.append(temp_data[line][0])
            for index in range(len(myIndexes)):
                temp_boxes[myIndexes[index]] = []
                for line in range(len(temp_data)):
                    if temp_data[line][0] == myIndexes[index]:
                        temp_boxes[myIndexes[index]].append(temp_data[line][1])
            #print(temp_boxes)
            df = pd.DataFrame.from_dict(temp_boxes, orient='index')
            df=df.transpose()
            #print(df)
            df.plot.box(grid='True')
            plt.title('Node:' + node_name)
            plt.xlabel('Neighbour')
            plt.ylabel('Time(ms)')
            #plt.show()
            plt.savefig(self.folder+'/netout_box_'+ node_name +'.png')
            #print(temp_boxes)
            #for box in temp_boxes:
            #    df = pd.DataFrame(box, columns=['Out for'])
            #    df.plot.box(grid='True')
            #    plt.show()
            plt.close()
            temp_boxes = {}
                    #teste = npi.group_by(data[:, 0]).split(data[:, 1])
        #print(teste)
        #treat data
        #create plot


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
        report = Report(folder)
        #print(path+'/'+folders[len(folders)-1])
    elif (arguments.all == True):
        for simulation in sorted_folders:
            folder = arguments.indir+'/'+simulation
            #print(folder)
            report = Report(folder)
    elif (arguments.date != False):
        for simulation in sorted_folders:
            if (simulation == arguments.date):
                folder = arguments.indir+'/'+simulation
                #print(path+'/'+simulation)
                report = Report(folder)
    sys.exit()
