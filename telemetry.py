#!/usr/bin/python
import az.proto.terminal_pb2 as proto
import az.plugins_enabled as plugs
import os, traceback, hashlib, socket, struct, pkgutil
from time import sleep, time
from datetime import datetime
from simplejson import loads
import gnupg

gpg = gnupg.GPG(gnupghome='/home/pi')

def sendNetwork(server, string):
  if string is None or len(string)==0:
    return True
  try:
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    s.connect((remote_ip, p.port))    
    s.sendall(struct.pack("q",len(string)) + string)
    s.close()
  except socket.error, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()
    return False

  return True

def saveLocalStore(string):
  try:
    f=open(p.storage, "a+b")
    f.write(string)
    f.close()
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()

def savePermaStore(string):
  try:
    f=open(p.permastorage, "a+b")
    f.write(string)
    f.close()
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()

def loadLocalStore():
  try:
    with open(p.storage, "rb") as f:
      return f.read()
  except Exception, msg:
    print datetime.utcnow(), msg
    print traceback.format_exc()

def truncLocalStore():
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
  currentCountDown = 0

  isBatchMode=True  # as opposed to isIntervalMode
  while True:

    if isBatchMode:
      dp=proto.DataPoint()
      dp.unitid=p.unitID
      dp.timestamp=int(time())
      dp.type=proto.DataPoint.STATION
      for m in pf:
        m[0].dev_pack(dp,m[1].next())
      pending_batch+=1
    else:
      pending_interval+=1


    if currentCountDown > 0:
      currentCountDown -= 1
      if pending_interval==p.intervalSize:
        pending_interval=0
        isBatchMode=True
      if pending_batch==p.batchSize:
        pending_batch=0
        isBatchMode=False
      sleep(1)
      continue

    if pending_batch==p.batchSize:
      srv=p.servers[currentServer]
      ks=dp.SerializeToString()
      ks=gpg.encrypt(ks, ['dp@dp.io'], always_trust=True, armor=False)

      savePermaStore(ks)
      uploadBatchOK=sendNetwork(srv, ks)

      if not uploadBatchOK:
        saveLocalStore(ks)
      else:
        ks = loadLocalStore()
        if ks and len(ks) > 0:
          uploadBacklogOK=sendNetwork(srv, ks)
          if uploadBacklogOK:
            truncLocalStore()

      if not uploadBatchOK:
        currentAttempt+=1
        if currentAttempt==p.retryAttempts:
          currentServer+=1
          currentServer%=len(p.servers)
          currentAttempt, currentMultiplier=0, 1
        print 'Error connecting to %s. Sleeping for %d seconds' % (srv, currentMultiplier)
        currentCountDown = currentMultiplier
        currentMultiplier*=p.retryMultiplier
      else:
        currentAttempt, currentMultiplier=0, 1
      pending_batch=0
      isBatchMode=False
    
    if pending_interval==p.intervalSize:
      pending_interval=0
      isBatchMode=True

    sleep(1)
