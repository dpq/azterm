#!/usr/bin/python
import threading, time, cPickle
names = ["Temperature [C*] BMP085", "Pressure [Pa] BMP085"]

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
  for val in names:
    if val.lower().find('pressure') != -1:
      dp.air.pressure = res.get(val, -9999)
    elif val.lower().find('temperature') != -1:
      dp.air.temperature = res.get(val, -9999)

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
