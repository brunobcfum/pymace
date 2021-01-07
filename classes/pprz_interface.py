#!/usr/bin/env python3
import json, os, sys, socket, traceback, threading, time, logging, pickle

import pprzlink.udp
import pprzlink.messages_xml_map as messages_xml_map
import pprzlink.message as message

from geopy import distance
from geopy.distance import geodesic

class Interface():
    def __init__(self, Node):
        self.Node = Node
        #self.tag_number = int(self.Node.tag[5:])
        self.home = [43.564188, 1.480981]
        self.scale = 2
        self.callbacks = []
        self.udp = pprzlink.udp.UdpMessagesInterface(
                self.packet_handler,            # Callback function
                uplink_port = 4212,      # Port we send messages to 
                downlink_port = 4242,  # Port used to receive messages
                #interface_id = 1,   # Numerical id of the interface (ac_id)
                verbose=False,
                msg_class='telemetry'
                )

        self.udp_sender = pprzlink.udp.UdpMessagesInterface(
                        self.packet_handler,          # Callback function
                        uplink_port = 56042,  # Port we send messages to 
                        downlink_port = 4212,  # Port used to receive messages
                        interface_id = 31, # Numerical id of the interface (ac_id)
                        msg_class='telemetry'
                        )

    def start(self):
        self.udp.start()
        self.udp_sender.start()

    def shutdown(self):
        self.udp_sender.shutdown()
        self.udp.shutdown()

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def packet_handler(self, sender,address,msg,length,receiver_id=None, component_id=None):
        if msg.name == "GPS_INT":
            #print(str(sender) + "->GPS lat:" + str(msg.get_field(3) / 10000000) + " long: " + str(msg.get_field(4) / 10000000))
            y = geodesic((self.home[0], self.home[1]), (msg.get_field(3)/ 10000000,self.home[1])).meters * self.scale
            x = geodesic((self.home[0], self.home[1]), (self.home[0], msg.get_field(4)/ 10000000)).meters * self.scale
            #x = 500 * (180 + (msg.get_field(3) / 10000000)) / 360
            #y = 500 * (90 - (msg.get_field(4) / 10000000)) / 180
            for cb in self.callbacks:
                cb([receiver_id, x, y])
            try:
                self.Node.Bus.emmit(['MOB', 'POSITION', [self.tag_number, x, y]])
            except:
                #Only works when called from a crafted node
                pass
            #print("X:" + str(x) + " Y:" + str(y))
        else:
            pass
            #print("Received message from %i %s [%d Bytes]: %s" % (sender, address, length, msg)) 

        try:
            self.udp_sender.send(
                msg,            # The message to send
                sender, # Our numerical id
                "127.0.0.1",   # The IP address of the destination
                0  # The id of the destination  
            )
        except:
            traceback.print_exc()
            #print("Failed to send message from %i %s [%d Bytes]: %s" % (sender, address, length, msg)) 