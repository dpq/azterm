#!/usr/bin/python
import threading, serial
import terminal_pb2
import time

names = [ "RPi Voltage", "EPR Voltage", "USB Voltage", "BAT Voltage", "UPiS Current", "Analog Sensor Temperature", "Powering Source" ]

class UpisPoller(threading.Thread):
  def __init__(self):
    super(UpisPoller, self).__init__()
    self.current_value = {}
    self._stop = threading.Event()
    self.ser = serial.Serial("/dev/ttyAMA0", 38400, timeout=10, parity=serial.PARITY_EVEN, rtscts=1)

  def get_current_value(self):
    return self.current_value

  def stop(self):
    self.ser.close()
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

  def run(self):
    try:
      while True:
        if self.stopped():
          print 'stopped'
          break
        self.ser.write("@status\r\n")
        self.ser.flush()
        res = self.ser.read(1024).split("\n\r")
        for l in res:
          if l.find(":") == -1:
            continue
          l = l.split(":")
          if l[0] in names:
            if l[0] == "Powering Source":
              self.current_value[l[0]] = l[1]
            else:
              self.current_value[l[0]] = float(l[1].split()[0])
        time.sleep(2.0) # TODO tune.
    except StopIteration,e:
      print e
      pass

def dev_init():
  global upisp
  upisp = UpisPoller()
  upisp.daemon = True
  upisp.start()

def dev_exit():
  upisp.stop()

def dev_data():
  while True:
    res = upisp.get_current_value()
    if res is not None:
        yield res

def dev_pack(dp, res):
  for val in names:
    if val.lower().find('voltage') != -1:
      v=dp.voltage.add()
      v.name = val
      v.value = res.get(val, -9999)
    elif val.lower().find('current') != -1:
      v=dp.current.add()
      v.name = "UPiS Current"
      v.value = res.get(val, -9999)
    elif val.lower().find('temperature') != -1:
      v=dp.temp.add()
      v.name = "UPiS Temperature"
      v.value = res.get(val, -9999)
    elif val.lower().find('source') != -1:
      v=dp.text.add()
      v.name = "UPiS Source"
      v.value = res.get(val, "")

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
