#!/usr/bin/env python3

"""
When studying distributed systems, it is usefull to play with concepts and create prototype applications.
This main runner aims in helping with the prototyping, so that an application can be created as a class 
in ./classes/apps. This code contains the main runner that will run in each node. This is called by the 
pymace main emulation script, but can be called manually when running on real hardware or when running 
manually for testing.

Other support classes are also in ./classes to bootstrap some basic funcionality, but are completelly 
optional since most is already covered by better python libraries.

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
        _start() #main execution loop
        _shutdown()
    except KeyboardInterrupt:
        logger.print_error("Interrupted by ctrl+c")
        os._exit(1)
    except:
        logger.print_error("Scheduling error!")
        traceback.print_exc()

def _start():
    random.seed("this_is_enac "+Node.fulltag); #Seed for random
    prompt_thread.start() #starts prompt
    
    # finally a scheduler that actually works
    scheduler.add_job(task1, 'interval', seconds=1, id='running')
    scheduler.add_job(task2, 'interval', seconds=Node.second/1000, id='sim_sec')
    scheduler.add_job(task3, 'interval', seconds=1, id='real_sec')
    scheduler.start()
    Node.start() # replace this by application start
    while Node.stop == False:
        time.sleep(2)

def _shutdown():
    try:
        scheduler.remove_job('running')
        scheduler.remove_job('sim_sec')
        scheduler.remove_job('real_sec')
        scheduler.shutdown()
    except: 
        pass
    prompt_thread.join(timeout=1)
    os._exit(1)

def task1(): #check_if_finished and stops the simulation
    """
    This function checks if simulation is supposed to be running, otherwise stop and cleanup
    """
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
                logger.print_alert("Shuting down node.")
                Node.shutdown()
                endfile = open("reports/" + logger.simdir + "/finished/"+args.tag+".csv","w") #
                endfile.write('done\n')
                endfile.close()
                logger.print_alert("Done:" + str(Node.stop))
            except:
                pass
            return

def task2(): #1 tick per sim second
    """
    This function counts every second and stops after defined limit
    """
    if Node.lock==False: #Do not run if the simulation is supposed to stop
        return
    Node.simulation_seconds += 1
    if Node.simulation_seconds > args.time_limit:
        Node.lock = False

def task3(): #This task draws a HMI to have some realtime info
    """
    This function displays elapsed time and a small indication that something is happeing in the network.
    """
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
    logger.printxy(2, 80-(len(str(Node.simulation_seconds))),Node.simulation_seconds)


def startup():
    """
    This function is a synchronizer so that all nodes can start ROUGHLY at the same time
    """
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove("/tmp/pymace.sock.node"+str(args.number))
    except OSError:
        #traceback.print_exc()
        pass
    try:
        s.bind("/tmp/pymace.sock.node"+str(args.number))
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

def pritn_header():
    print("pymace v." + __version__ + " - application test")

def parse_arguments():

    parser = argparse.ArgumentParser(description='Some arguments are obligatory and must follow the correct order as indicated')

    parser.add_argument("tag", help="A tag for the node")
    parser.add_argument("application", help="Which application you want to use")
    parser.add_argument("time_scale", help="Time scaler to make the application run faster(<1) or slower(>1)", type=float)
    parser.add_argument("time_limit", help="Simulation runtime limit in seconds", type=int)
    #parser.add_argument("mobility", help="The mobility model being use for reporting reasons")
    parser.add_argument("ip", help="IP protocol: ipv4 or ipv6", choices=['ipv4', 'ipv6'])
    parser.add_argument("-v", "--verbosity", action="store_true", help="Verbose output")
    parser.add_argument("-b", "--battery", type=int, help="Initial battery level", default=100)
    parser.add_argument("-e", "--energy", type=str, help="Energy model", default="stub")
    parser.add_argument("-r", "--role", type=str, help="Set a role if required by application", default="node")
    parser.add_argument("-p", "--protocol", type=str, help="Communication protocol", default="sockets")
    parser.add_argument("-m", "--membership", type=str, help="Membership control", default="local")
    parser.add_argument("-f", "--fault_detector", type=str, help="Fault Detector", default="simple")
    parser.add_argument("-o", "--mobility", type=str, help="Mobility Model", default="Random_Walk")
    parser.add_argument("-n", "--number", type=int, help="Node number", default=0)

    return parser.parse_args()

if __name__ == '__main__':  #for main run the main function. This is only run when this main python file is called, not when imported as a class
    try:
        pritn_header()
        args = parse_arguments()

        #defining the node
        Node = node.Node(args.tag,
                         args.number,
                         args.energy, 
                         args.mobility, 
                         args.application, 
                         args.role, 
                         args.time_scale, 
                         args.battery, 
                         args.ip.upper(), 
                         args.protocol, 
                         args.membership, 
                         args.fault_detector) #create node object
        
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
    except:
        traceback.print_exc()