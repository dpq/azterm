#!/usr/bin/python
from gps import *
import os
import threading
import terminal_pb2

def touch(fname, times=None):
  fhandle = file(fname, 'a')
  try:
    os.utime(fname, times)
  finally:
    fhandle.close()

class GpsPoller(threading.Thread):
  def __init__(self):
    #threading.Thread.__init__(self)
    super(GpsPoller, self).__init__()
    self.session = gps(mode=WATCH_ENABLE)
    self.current_value = None
    self._stop = threading.Event()

  def get_current_value(self):
    return self.current_value

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

  def run(self):
    try:
      while True:
        if self.stopped():
          print 'stopped'
          break
        try:
          self.current_value = self.session.next()
          touch("/tmp/azgps") # This is needed to detect and fix GPS daemon lockups
        except:
          print "GPS error"
        time.sleep(0.2) # TODO tune.
    except StopIteration:
      pass

gpsp = None

def dev_init():
  global gpsp
  gpsp = GpsPoller()
  gpsp.daemon = True
  gpsp.start()

def dev_exit():
  gpsp.stop()

def dev_data():
  while True:
    res = gpsp.get_current_value()
    if res is not None:
        yield res

def dev_pack(dp, res):
  dp.pos.sys = terminal_pb2.DataPoint.PositionSensor.GPS
  dp.pos.lat, dp.pos.lon, dp.pos.alt = res.get(u"lat", -9999), res.get(u"lon", -9999), res.get(u"alt", -9999)
  dp.pos.speed, dp.pos.track, dp.pos.climb = res.get(u"speed", -9999), res.get(u"track", -9999), res.get(u"climb", -9999)
  dp.pos.epx, dp.pos.epy, dp.pos.epv = res.get(u"epx", -9999), res.get(u"epy", -9999), res.get(u"epv", -9999)
  return dp

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
