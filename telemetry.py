#!/usr/bin/python
import az.proto.terminal_pb2 as proto
import az.plugins_enabled as plugs
import os, traceback, hashlib, socket, struct, ssl, pkgutil
from time import sleep, time
from datetime import datetime
from simplejson import loads

def send_network(server, string):
  if string is None or len(string)==0:
    return True
  try:
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock=ssl.wrap_socket(s, ca_certs="/home/pi/gv.crt", cert_reqs=ssl.CERT_REQUIRED)
  except socket.error, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False

  try:
    remote_ip=socket.gethostbyname(server)
  except socket.gaierror, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False

  try:
    ssl_sock.connect((remote_ip, p.port))    
    hash=hashlib.sha1(string)
    msglen=len(string)
    ssl_sock.sendall(struct.pack("i",msglen) + hash.digest() + string)
    ssl_sock.close()
    return True
  except socket.error, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False
  except Exception, msg:
    print datetime.utcnow(), msg
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
    f=open(p.storage, "a+b")
    f.write(string)
    f.close()
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()

def loadFromFile():
  try:
    with open(p.storage, "rb") as f:
      return f.read()
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()

def truncFile():
  try:
    open(p.storage, 'w').close()
    return True
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False


class Params(dict):
    def __init__(self, configfile, *args):
        dict.__init__(self, loads(open(configfile).read()), *args)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

    def __getattr__(self, name):
        return dict.__getitem__(self, name)

if __name__=="__main__":
  p = Params("/etc/azazel.json")
  prefix = plugs.__name__ + "."
  pf=[]
  for importer, modname, ispkg in pkgutil.iter_modules(plugs.__path__, prefix):
    module = __import__(modname, fromlist="dummy")
    pf.append((module, module.dev_data()))

  for m in pf:
    m[0].dev_init()

  currentServer, currentAttempt, currentMultiplier=0, 0, 1  
  pending_batch, pending_interval=0, 0

  isBatchMode=True  # as opposed to isIntervalMode
  truncateOK=True

  k=proto.DataPack()
  while True:
    dp=k.point.add()
    dp.unitid=p.unitID
    dp.timestamp=int(time())
    dp.type=proto.DataPoint.STATION

    for m in pf:
      m[0].dev_pack(dp,m[1].next())

    if isBatchMode:
      pending_batch+=1
    else:
      pending_interval+=1

    if pending_batch==p.batchSize:
      srv=p.servers[currentServer]
      ks=k.SerializeToString()

      uploadOK=send_network(srv, ks)
      if not uploadOK:
        saveToFile(ks)
      elif truncateOK:
        uploadOK=send_network(srv, loadFromFile())

      if uploadOK or not truncateOK:
        truncateOK=truncFile()

      if not uploadOK:
        currentAttempt+=1
        if currentAttempt==p.retryAttempts:
          currentServer+=1
          currentServer%=len(p.servers)
          currentAttempt, currentMultiplier=0, 1
        print 'Error connecting to %s. Sleeping for %d seconds' % (srv, currentMultiplier)
        sleep(currentMultiplier)
        currentMultiplier*=p.retryMultiplier
      else:
        currentAttempt, currentMultiplier=0, 1
      k=proto.DataPack()
      pending_batch=0
      isBatchMode=False
    
    if pending_interval==p.intervalSize:
      pending_interval=0
      isBatchMode=True

    sleep(1)
