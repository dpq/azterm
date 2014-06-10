#!/usr/bin/python
import threading, time, cPickle
names = ["Combustible gas [ppm] MQ6"]

def dev_init():
  pass

def dev_exit():
  pass

def dev_data():
  while True:
    try:
      data = cPickle.load(open("/tmp/azino"))
      res = {}
      for n in names:
        res[n] = data.get(n, -9999)
      yield res
    except:
      yield {}

def dev_pack(dp, res):
  g=dp.gas.add()
  for val in names:
    if val.lower().find('mq6') != -1:
      g.name = "MQ6"
      g.ppm = int(res.get(val, -9999))

if __name__=="__main__":
  dev_init()
  gd = dev_data()
  try:
    while True:
     print gd.next()
     time.sleep(1)
  except KeyboardInterrupt:
    pass
  dev_exit()
