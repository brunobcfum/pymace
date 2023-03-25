#!/usr/bin/env python3
from flask import Flask
from flask_socketio import SocketIO, emit

import flask, json, requests, os, socket, traceback, threading, time, logging, sys
from multiprocessing import Process

class Socket(flask.Flask):
    def __init__(self, corenodes, wlan, session, modelname, digest, semaphore, pymace, callback, networks):
        app = flask.Flask(__name__)
        self.Pymace = pymace
        self.socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, logger=False)
        log1 = logging.getLogger('werkzeug')
        log1.disabled = True
        log2 = logging.getLogger('socketio')
        log2.disabled = True
        log3 = logging.getLogger('engineio')
        log3.disabled = True
        self.digest = digest
        self.semaphore = semaphore
        self.lock = True
        self.list_nodes = []
        self.corenodes = corenodes
        self.initial_nodes = {}
        self.wlan = wlan
        self.session = session
        self.modelname = modelname
        self.pymace_callback = callback
        self.networks = networks

        for node in self.corenodes:
            self.initial_nodes[node.id] = node.getposition()
        @app.route("/")
        def info():
            data = json.dumps({'Hello':'world'})
            response = app.response_class(
                response=data,
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response

        @app.route("/sim/stop")
        def stop():
            print('Shutting down web server')
            try:
                self.Pymace.running = False
                self.socketio.stop()
            except:
                pass
            response = app.response_class(
                response='OK',
                status=200,
                mimetype='application/json'
            )
            return response
        
        @self.socketio.on('update_pos', namespace='/sim')
        def handle_message(updated_node):
            for node in self.corenodes:
                if int(node.id) - 1 == int(updated_node['node']['id']):
                    #print(node.id)
                    #print(updated_node['node']['id'])
                    node.setposition(int(updated_node['node']['x']),int(updated_node['node']['y']))
            #print('received message: ' + str(node))

        @self.socketio.on('reset_pos', namespace='/sim')
        def handle_message():
            for node in self.corenodes:
                node.setposition(self.initial_nodes[node.id][0],self.initial_nodes[node.id][1])

        @self.socketio.on('pingServer', namespace='/sim')
        def handle_my_custom_event(arg1, arg2):
            print('received json: ' + str(arg1) + " " + str(arg2))
            emit('ponggg')

        @self.socketio.on('connect', namespace='/sim')
        def test_connect():
            emit('my response', {'data': 'Connected'})
            #emit('nodes', {'nodes': self.list_nodes})

        @self.socketio.on('disconnect', namespace='/sim')
        def test_disconnect():
            print('Client disconnected')
        self.nthread = threading.Thread(target=self.nodes_thread, args=())
        self.dthread = threading.Thread(target=self.emmit_digest, args=())
        self.netthread = threading.Thread(target=self.network_thread, args=())
        self.nthread.start()
        self.dthread.start()
        self.netthread.start()
        self.socketio.run(app, debug=False)
        self.shutdown()

    def shutdown(self):
        #self.socketio.stop(namespace='/sim')
        self.lock=False
        self.nthread.join()
        self.dthread.join()
        self.netthread.join()


    def emmit_digest(self):
        while self.lock:
            if self.Pymace.iosocket_semaphore == True:
                print('IOSOCKET -> semaphore')
                self.socketio.emit('digest', {'data': self.Pymace.nodes_digest}, namespace='/sim')
                self.Pymace.iosocket_semaphore = False
            time.sleep(0.5)

    ###TODO: Separate nodes from wlan and for now on, different threads with different rate

    def network_thread(self):
        while self.lock:
            self.socketio.emit('networks', {'data': self.networks}, namespace='/sim')
            time.sleep(1)

    def nodes_thread(self):
        data = {}
        data['nodes'] = []
        data['wlan'] = {}
        while self.lock:
            data['nodes'].clear()
            for node in self.corenodes:
                nodedata = {}
                nodedata['position'] = node.getposition()
                nodedata['id'] = node.id
                nodedata['range'] = 250
                data['nodes'].append(nodedata)
            try:
                data['wlan']['model'] = self.modelname
                data['wlan']['range'] = self.session.mobility.get_model_config(self.wlan.id, self.modelname)['range']
                data['wlan']['bandwidth'] = self.session.mobility.get_model_config(self.wlan.id, self.modelname)['bandwidth']
                data['wlan']['jitter'] = self.session.mobility.get_model_config(self.wlan.id, self.modelname)['jitter']
                data['wlan']['delay'] = self.session.mobility.get_model_config(self.wlan.id, self.modelname)['delay']
                data['wlan']['error'] = self.session.mobility.get_model_config(self.wlan.id, self.modelname)['error']
            except:
                pass
            time.sleep(0.1)
            self.socketio.emit('nodes', {'data': data}, namespace='/sim')

    def add_node(self, node):
        self.corenodes.append(node)

