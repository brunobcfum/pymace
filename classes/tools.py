import zlib, random, sys

def create_id(time, tag):
  'Create an CRC32 unique ID'
  return zlib.crc32((str(time)+ str(tag) + str(random.randint(0,10000))).encode())

def print_error(text):
  'Print error message with special format'
  print()
  print("\033[1;31;40m"+text+"  \n")
  print("\033[0;37;40m")

def print_alert(text):
  'Print alert message with special format'
  print()
  print("\033[1;32;40m"+text+"  \n")
  print("\033[0;37;40m")

def print_info(text):
  'Print info message with special format'
  print()
  print("\033[1;34;40m"+text+"  \n")
  print("\033[0;37;40m")

def printxy(x, y, text):
  sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
  sys.stdout.flush()