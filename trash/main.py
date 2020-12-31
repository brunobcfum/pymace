#!/usr/bin/env python3

""" 
Main simulation runner is part of the Genesis project.
This contains the main runner that will run in each node. This is called by the genesis main emulation script,
but can be called manually when running on real hardware or when running manually for testing.
"""
__author__ = "Bruno Chianca Ferreira"
__license__ = "MIT"
__version__ = "0.6"
__maintainer__ = "Bruno Chianca Ferreira"
__email__ = "brunobcf@gmail.com"

import  threading, sys, traceback, time, random, json, os, shutil, socket, argparse
from classes import prompt, log, node, nodedump, tools
from apscheduler.schedulers.background import BackgroundScheduler

fwd_old = 0
inc=0
packet_counter = 0
anim = ['\\','|','/','-']

def main(tag):
    #this function controls all the tasks
    try:
        _start()
        _shutdown()
    except KeyboardInterrupt:
        logger.print_error("Interrupted by ctrl+c")
        os._exit(1)
    except:
        logger.print_error("Scheduling error!")
        traceback.print_exc()

def _start():
    random.seed("this_is_enac "+Node.tag); #Seed for random
    prompt_thread.start() #starts prompt
    
    # finally a scheduler that actually works
    scheduler.add_job(task1, 'interval', seconds=1, id='running')
    scheduler.add_job(task2, 'interval', seconds=Node.second/1000, id='sim_sec')
    scheduler.add_job(task3, 'interval', seconds=1, id='real_sec')
    #scheduler.add_job(task4, 'interval', seconds=2, id='datalogger')
    #scheduler.add_job(task5, 'interval', seconds=5, id='node_info')
    #scheduler.add_job(task6, 'interval', seconds=8, id='node_neighbours')
    #scheduler.add_job(milisecond, 'interval', seconds=1/10, id='real_ms')
    scheduler.start()
    Node.start() # replace this by application start
    #Node.Application.start() # replace this by application start
    while Node.stop == False:
        time.sleep(2)

def _shutdown():
    try:
        scheduler.remove_job('running')
        scheduler.remove_job('sim_sec')
        scheduler.remove_job('real_sec')
        #scheduler.remove_job('datalogger')
        #scheduler.remove_job('node_info')
        #scheduler.remove_job('node_neighbours')
        #scheduler.remove_job('real_ms')
        scheduler.shutdown()
    except: 
        pass
    prompt_thread.join(timeout=1)
    os._exit(1)

def task1(): #check_if_finished and stops the simulation
    if Node.stop==False: #Run if the simulation is supposed to stop
        #if Node.Battery.battery_percent <= 1 or Node.lock == False:
        if Node.lock == False:
            logger.print_alert("Simulation ended. Recording logs.")
            #Node.lock=False
            prompt.lock=False
            logger.datalog(Node)
            logger.log_messages(Node)
            logger.log_network(Node)
            try:
                shutil.move("./node_dumps", "reports/" + logger.simdir + "/")
                shutil.move("./neighbours", "reports/" + logger.simdir + "/")
            except:
                pass
            try:
                logger.print_alert("Shuting down node.")
                Node.shutdown()
                #Node.stop = True
                endfile = open("reports/" + logger.simdir + "/finished/"+args.tag+".csv","w") #
                endfile.write('done\n')
                endfile.close()
                logger.print_alert("Done:" + str(Node.stop))
            except:
                pass
            return

def task2(): #1 tick per sim second
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    Node.simulation_seconds += 1
    if Node.simulation_seconds > args.time_limit:
        Node.lock = False

def task3(): #This task draws a HMI to have some realtime info
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    Node.simulation_tick_seconds += 1 
    fwd_new = Node.stats[0]
    visible = len(Node.Membership.visible)
    #topology = len(Node.Membership.topology) + 1
    global inc, fwd_old, packet_counter
    if packet_counter >= 5:
        Node.Network.traffic = Node.Network.packets / 5 
        Node.Network.packets = 0
        packet_counter = 0
    else:
        packet_counter += 1
    if fwd_new > fwd_old:
        fwd_old= fwd_new
        inc+=1
        if inc == 4:
            inc = 0
    logger.printxy(1,79,anim[inc])
    #logger.printxy(1,79,Node.stats[0])
    #logger.printxy(2,70,Node.Membership.traffic)
    #logger.printxy(2,77,'pps')
    #logger.printxy(2,70,visible)
    #logger.printxy(2,73,'visible')
    #logger.printxy(4,70,topology)
    #logger.printxy(4,73,'total')
    logger.printxy(2, 80-(len(str(Node.simulation_seconds))),Node.simulation_seconds)

def task4(): #datalogger
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    logger.datalog(Node) #this task is run to log data to file

def task5(): #update node info for rest every 5 real seconds
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    nodedump.Dump(Node)

def task6(): #update node neighbours for rest every 8 real seconds
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    nodedump.Neighbours(Node)

def milisecond(): #update node neighbours for rest every 8 real seconds
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    Node.simulation_mseconds += 100

def startup():
    #this section is a synchronizer so that all nodes can start ROUGHLY at the same time
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove("/tmp/genesis.sock."+args.tag)
    except OSError:
        #traceback.print_exc()
        pass
    try:
        s.bind("/tmp/genesis.sock."+args.tag)
        s.listen(10)
    except OSError:
        traceback.print_exc()
        pass
    conn, addr = s.accept()
    data = conn.recv(1024)
    if (float(data) - time.time()) < 0:
        conn.send("NOK".encode())
    else:
        conn.send("OK".encode())
    #print(float(data)) 
    #receives the global time when they should start. Same for all and in this simulation the clock is universal since all nodes run in the same computer
    conn.close()
    return data

if __name__ == '__main__':  #for main run the main function. This is only run when this main python file is called, not when imported as a class
    try:
        print("Genesis v." + __version__ + " - testing agent")

        parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')

        parser.add_argument("tag", help="A tag for the node")
        parser.add_argument("application", help="Which application you want to use")
        parser.add_argument("time_scale", help="Time scaler to make the application run faster(<1) or slower(>1)", type=float)
        parser.add_argument("time_limit", help="Simulation runtime limit in seconds", type=int)
        parser.add_argument("mobility", help="The mobility model being use for reporting reasons")
        parser.add_argument("ip", help="IP protocol: ipv4 or ipv6", choices=['ipv4', 'ipv6'])
        parser.add_argument("-v", "--verbosity", action="store_true", help="Verbose output")
        parser.add_argument("-b", "--battery", type=int, help="Initial battery level", default=100)
        parser.add_argument("-e", "--energy", type=str, help="Energy model", default="stub")
        parser.add_argument("-r", "--role", type=str, help="Set a role if required by application", default="node")
        parser.add_argument("-p", "--protocol", type=str, help="Communication protocol", default="sockets")
        parser.add_argument("-m", "--membership", type=str, help="Membership control", default="local")
        parser.add_argument("-f", "--fault_detector", type=str, help="Fault Detector", default="simple")

        args = parser.parse_args()
        #print(args)

        energy_model_file = open("energy_models.json","r").read()
        energy_model = json.loads(energy_model_file)
        for board in energy_model:
            if board['board'] == args.energy:
                energy_model = board
                break 

        Node = node.Node(args.tag, energy_model, args.application, args.role, args.time_scale, args.battery, args.ip.upper(), args.protocol, args.membership, args.fault_detector) #create node object
        prompt = prompt.Prompt(Node)
        logger = log.Log(Node, args.tag, args.role, args.energy, args.mobility)
        logger.clean_nodedumps(Node)
        #wait from the runner script the time when this node should start
        start=startup()
        #print("Starting in: " + str(float(start) * 1000 -  time.time() * 1000) + "ms")
        print("Starting ...")
        #start = 1
        while float(start) > time.time():
            #keeps locked in loop until is time to start
            pass
        tools.printxy(2,1, "                ")
        #############################################################################
        prompt_thread = threading.Thread(target=prompt.prompt, args=(Node,))
        scheduler = BackgroundScheduler()
        main(args.tag); #call scheduler function
    except KeyboardInterrupt:
        logger.print_error("Interrupted by ctrl+c")
        logger.logfile.close()