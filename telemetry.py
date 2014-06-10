#!/usr/bin/python
from az.proto import terminal_pb2
from urllib2 import urlopen, URLError
from simplejson import loads
import os, traceback, hashlib, socket, struct
from time import sleep
import time
from datetime import datetime

try:
    import ssl
except ImportError:
    print "SSL not found!"
    exit()

LS_LOCATION="/home/pi/localstorage.bin"

def send_network(server, string):
  if string is None or len(string)==0:
    return True
  try:
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock=ssl.wrap_socket(s, ca_certs="/home/pi/gv.crt", cert_reqs=ssl.CERT_REQUIRED)
  except socket.error, msg:
    print datetime.utcnow(), 'Cannot create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    print traceback.format_exc()
    return False

  try:
    remote_ip=socket.gethostbyname(server)
  except socket.gaierror, msg:
    print datetime.utcnow(), 'Cannot resolve server hostname. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    print traceback.format_exc()
    return False

  try:
    ssl_sock.connect((remote_ip, port))    
    hash=hashlib.sha1(string)
    msglen=len(string)
    ssl_sock.sendall(struct.pack("i",msglen) + hash.digest() + string)
    ssl_sock.close()
    return True
  except socket.error, msg:
    print datetime.utcnow(), 'Cannot transmit data, socket error. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    print traceback.format_exc()
    return False
  except:
    print datetime.utcnow(), 'Cannot transmit data, unknown error.Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    print traceback.format_exc()
    return False


def touch(fname, times=None):
  fhandle=file(fname, 'a')
  try:
    os.utime(fname, times)
  finally:
    fhandle.close()

def saveToFile(string):
  try:
    f=open(LS_LOCATION, "a+b")
    f.write(string)
    f.close()
  except:
    print datetime.utcnow(), "Cannot open local storage file for writing"
    print traceback.format_exc()

def loadFromFile():
  try:
    with open(LS_LOCATION, "rb") as f:
      return f.read()
  except:
    print datetime.utcnow(), "Cannot open local storage file for reading"
    print traceback.format_exc()

def truncFile():
  try:
    open(LS_LOCATION, 'w').close()
    return True
  except:
    print datetime.utcnow(), "Cannot open local storage file for truncating"
    print traceback.format_exc()
    return False

def getParams():
  str=open("/etc/azazel.json").read()
  conf=loads(str)
  return conf["servers"], int(conf["retryMultiplier"]), int(conf["retryAttempts"]), int(conf["port"]), conf["unitID"], int(conf["batch"]), int(conf["interval"])

import sys,imp

def plugin(device): #os.path.dirname(__file__)
    globals()["plugins-enabled.%s"%device]=imp.load_source(device,
      os.path.join("/usr/lib/python2.7/dist-packages", "plugins-enabled", "%s.py"%device))
    module=globals()["plugins-enabled.%s"%device]
    return module

if __name__=="__main__":
  servers, retryMultiplier, retryAttempts, port, token, batchSize, intervalSize=getParams()

  plugins=os.listdir('/home/pi/plugins-enabled')
  pf=[]
  for pi in plugins:
    if pi != "__init__.py" and pi.endswith(".py"):
      x=plugin(pi.replace(".py", ""))
      pf.append((x, x.dev_data()))

  for m in pf:
    m[0].dev_init()

  currentServer, currentAttempt, currentMultiplier=0, 0, 1  
  pending_batch, pending_interval=0, 0

  isBatchMode=True  # as opposed to isIntervalMode
  truncateOK=True

  k=terminal_pb2.DataPack()
  while True:
    dp=k.point.add()
    dp.unitid=token
    dp.timestamp=int(time.time())
    dp.type=terminal_pb2.DataPoint.STATION

    for m in pf:
      m[0].dev_pack(dp,m[1].next())

    if isBatchMode:
      pending_batch+=1
    else:
      pending_interval+=1

    if pending_batch==batchSize:
      srv=servers[currentServer]
      ks=k.SerializeToString()

      batchUploadOK=send_network(srv, ks)
      if not batchUploadOK:
        saveToFile(ks)
      elif truncateOK:
        backlogUploadOK=send_network(srv, loadFromFile())

      if backlogUploadOK or not truncateOK:
        truncateOK=truncFile()

      if not batchUploadOK:
        currentAttempt+=1
        if currentAttempt==retryAttempts:
          currentServer+=1
          currentServer%=len(servers)
          currentAttempt, currentMultiplier=0, 1
        print 'Error connecting to %s. Sleeping for %d seconds' % (srv, currentMultiplier)
        sleep(currentMultiplier)
        currentMultiplier*=retryMultiplier
      else:
        currentAttempt, currentMultiplier=0, 1
      k=terminal_pb2.DataPack()
      pending_batch=0
      isBatchMode=False
    
    if pending_interval==intervalSize:
      pending_interval=0
      isBatchMode=True

    sleep(1)
