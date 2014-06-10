#!/usr/bin/python
import threading, time, cPickle
names = ["Temperature [C*] MPL3115A2", "Pressure [Pa] MPL3115A2", "Humidity [%] HTU21D(F)",
  "Ambient light [lux] ALS-PT19-315C/L177/TR8", "Precipitation [in/sec] ADS80422",
  "Wind direction [deg] ADS80422", "Wind speed [mph] ADS80422", "Lat [deg] GP635T",
  "Lon [deg] GP635T", "Alt [m] GP635T", "Battery voltage [V]"]

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
  l = dp.light.add()
  l.minwavelength = 390
  l.maxwavelength = 700
  v = dp.voltage.add()
  for val in names:
    if val.lower().find('pressure') != -1:
      dp.air.pressure = float(res.get(val, -9999))
    elif val.lower().find('temperature') != -1:
      dp.air.temperature = float(res.get(val, -9999))
    elif val.lower().find('humidity') != -1:
      dp.air.humidity = float(res.get(val, -9999))
    elif val.lower().find('precipitation') != -1:
      dp.air.precipitation = float(res.get(val, -9999))
    elif val.lower().find('light') != -1:
      l.intensity = float(res.get(val, -9999))
    elif val.lower().find('wind dir') != -1:
      dp.wind.direction = int(res.get(val, -9999))
    elif val.lower().find('wind speed') != -1:
      dp.wind.speed = float(res.get(val, -9999))
    elif val.lower().find('battery') != -1:
      v.name = "Weather power voltage"
      v.value = res.get(val, -9999)


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
