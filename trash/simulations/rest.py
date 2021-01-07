import flask, json, requests, os, socket, traceback
from multiprocessing import Process

motes_global = []
class Api(flask.Flask):

    def get_nodes(self):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect("/tmp/ouroboros/nodes.sock")
            s.send('get'.encode())
            data = s.recv(65000)
            #print(data.decode())
            nodes = json.loads(data.decode())
            s.close()
            return nodes
        except:
            #pass
            traceback.print_exc()

    def __init__(self, _motes):
        app = flask.Flask(__name__)
        list_nodes = []
        for mote in _motes:
            list_nodes.append(mote.name)
        #print(list_nodes)
        self.motes = _motes
        @app.route("/")
        def info():
            data = []
            nodes = self.get_nodes()
            #print(nodes)
            for node in nodes:
                data.append(node)
            data = json.dumps({'Nodes':data})
            response = app.response_class(
                response=data,
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response
        @app.route("/nodes") #deprecated
        def nodes():
            nodes = []
            nodes_info = []
            for node in self.motes:
                nodes.append(node.params['ip'][0].split('/')[0])
            for node in nodes:
                print(node)
                url = 'http://' + node + ':5000/'
                print(url)
                resp = requests.get(url)
                print(resp)
                nodes_info.append(resp)
            response = app.response_class(
                response=nodes_info,
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response
        @app.route("/nodedumps")
        def dumps():
            qnode = flask.request.args.get('node')
            path ="./node_dumps" 
            f = []
            node_info={}
            for (dirpath, dirnames, filenames) in os.walk(path):
                f.extend(filenames)
                break
            for node in f:
                if node.split('.')[0] == qnode:
                    dump_file = open(path+"/"+node,"r").read()
                    info=json.loads(dump_file)
                    node_info = json.dumps({qnode:info})
            if node_info != {}:
                response = app.response_class(
                    response=node_info,
                    status=200,
                    mimetype='application/json'
                )
                header = response.headers
                header['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                node_info = {"error":"not found"}
                response = app.response_class(
                    response=node_info,
                    status=404,
                    mimetype='application/json'
                )
                header = response.headers
                header['Access-Control-Allow-Origin'] = '*'
                return response
        @app.route("/neighbours")
        def neighbours():
            qnode = flask.request.args.get('node')
            path ="./neighbours" 
            files = []
            neighbours=[]
            for (dirpath, dirnames, filenames) in os.walk(path):
                files.extend(filenames)
                break
            for node in files:
                if node.split('.')[0] == qnode:
                    dump_file = open(path+"/"+node,"r").read()
                    nodes = dump_file.split(';')
                    for vizinho in range(len(nodes)-1):
                        info=json.loads(nodes[vizinho])
                        neighbours.append(info)
                    neighbours = json.dumps(neighbours)
            if neighbours != []:
                response = app.response_class(
                    response=neighbours,
                    status=200,
                    mimetype='application/json'
                )
                header = response.headers
                header['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                node_info = {"error":"not found"}
                response = app.response_class(
                    response=node_info,
                    status=404,
                    mimetype='application/json'
                )
                header = response.headers
                header['Access-Control-Allow-Origin'] = '*'
                return response
        @app.route("/shutdown") #deprecated
        def shutdown():
            self.server.terminate()
            self.server.join()
            response = app.response_class(
                response='OK',
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response
        #app.run(debug=False)
        self.server = Process(target=app.run)
        self.server.start()
    def shutdown(self):
        self.server.terminate()
        self.server.join()

