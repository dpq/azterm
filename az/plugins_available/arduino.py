#!/usr/bin/python
import threading, time, cPickle, serial

class ArduinoPoller(threading.Thread):
  def __init__(self):
    super(ArduinoPoller, self).__init__()
    self.current_value = {}
    self._stop = threading.Event()
    self.ser = serial.Serial("/dev/arduino", timeout=5)

  def get_current_value(self):
    return self.current_value

  def stop(self):
    self.ser.close()
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

  def run(self):
    try:
      isInit = False
      while True:
        if self.stopped():
          print 'stopped'
          break
        line = []
        while True:
          c=self.ser.read(1)
          if c== '\r':
            end = True
          elif c == '\n' and end==True:
            break
          else:
            line.append(c)
            end = False

        l =''.join(line)
        if l.find("INIT") > -1:
          isInit = True
          l = l[l.find("INIT")+4:]
        if not isInit:
          continue
        line = []
        for d in l.split(";"):
          if d.find(":") == -1:
            continue
          d = d.split(":")
          self.current_value[d[0]] = float(d[1])
        time.sleep(2.0) # TODO tune.
        cPickle.dump(self.current_value, open("/tmp/azino","wb"))
    except StopIteration:
      pass


def dev_init():
  global ap
  ap = ArduinoPoller()
  ap.daemon = True
  ap.start()

def dev_exit():
  ap.stop()
  cPickle.dump({}, open("/tmp/azino","wb"))

def dev_data():
  while True:
    try:
      res = cPickle.load(open("/tmp/azino", "rb"))
      if res is not None:
          yield res
    except:
      yield {}

def dev_pack(dp, res):
  pass

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
