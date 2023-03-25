import threading, pickle, socket, os, traceback, struct

class VirtualGPS:
  """
  Class that reports current position to a UNIX socket so that other applications can access nodes position
  """
  def __init__(self, tag, node_number):
    self.tag = tag
    self.position = []
    self._setup()

  def _setup(self):
    pass

  def _update_position(self):
    pass

  def interface_callback(self, data):
    data = pickle.loads(data)
    #print(data)
    try:
      if data[0] == self.tag:
        if data[1].upper() == 'GET_POSITION':
          pos = self.get_position()
          #print(pos)
          return pos
    except:
      traceback.print_exc()
      pass

  def start(self):
    self.state = 'ENABLED'
    self.virtual_gps_thread = threading.Thread(target=self._interface_listener, args=())
    self.virtual_gps_thread.start()

  def _stop(self):
    self.state = "DISABLED"

  def shutdown(self):
    self._stop()
    self.virtual_gps_thread.join(timeout = 2)

  def _interface_listener(self):
    #this section is a synchronizer so that all nodes can start ROUGHLY at the same time
    gps_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
      os.remove("/tmp/" + self.tag +"_gps.sock")
    except OSError:
      #traceback.print_exc()
      pass
    try:
      gps_socket.bind("/tmp/" + self.tag +"_gps.sock")
      gps_socket.listen(1000) #backlog
    except OSError:
      traceback.print_exc()
    except:
      traceback.print_exc()
    while self.state != "DISABLED":
      conn, addr = gps_socket.accept()
      lengthbuf = conn.recv(4)
      length, = struct.unpack('!I', lengthbuf)
      data = b''
      while length:
        newbuf = conn.recv(length)
        if not newbuf: return None
        data += newbuf
        length -= len(newbuf)
      #data = conn.recv(65500)
      response = self.interface_callback(data)
      #print(response)
      payload = pickle.dumps(response)
      length = len(payload)
      conn.sendall(struct.pack('!I', length))
      conn.sendall(payload)
      conn.close()
    gps_socket.close()

  def emmit_to_gps_socket(self, data):
    gps = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    gps.settimeout(1)
    gps.connect("/tmp/" + self.tag +"_gps.sock")
    payload = pickle.dumps(data)
    length = len(payload)
    gps.sendall(struct.pack('!I', length))
    gps.sendall(payload)
    gps.close()

  def get_position(self):
    return self.position

  def set_position(self, pos):
    self.position = pos
    
