# Modules
import argparse
from datetime import datetime, timedelta
from flask import Flask
from flask_cors import CORS
from flask_restful import abort, Api, reqparse, Resource
try:
  import RPi.GPIO as GPIO
  runningOnPi = True
except (RuntimeError, ModuleNotFoundError):
  runningOnPi = False
import json
import logging
import os
from pathlib import Path
import sys
import threading
import time

# Custom Modules
try:
  sys.path.append('/home/pi/git/matrix')
  from matrixmessage import sendMatrixMessage
  messagingEnabled = True
except (RuntimeError, ModuleNotFoundError):
  messagingEnabled = False

# GPIO Functions
def customGPIOMapping(totalChannels, channel):
  threeChannel = {1: 26,
                  2: 20,
                  3: 21}
  eightChannel = {1: 5,   # Grey Green
                  2: 6,   # Grey Red
                  3: 13,  # Grey Blue
                  4: 16,  # Brown Red
                  5: 19,  # Brown Blue
                  6: 20,  # Blank
                  7: 21,  # Blank
                  8: 26}  # Blank

  if totalChannels == 8:
    return eightChannel[int(channel)]
  elif totalChannels == 3:
    return threeChannel[int(channel)]
  else:
    return None

# Check Functions
def checkExistingSprinklerID(sprinklerID, scheduleJSON):
  if sprinklerID not in scheduleJSON['sprinklers']:
    abort(404, message='Could not find sprinklerID')

def checkNotExistingSprinklerID(sprinklerID, scheduleJSON):
  if sprinklerID in scheduleJSON['sprinklers']:
    abort(409, message='sprinklerID already exists')

def checkExistingScheduleID(scheduleID, scheduleJSON):
  if scheduleID not in scheduleJSON['schedules']:
    abort(404, message='Could not find scheduleID')

def checkNotExistingSchedule(newScheduleData, scheduleID, scheduleJSON):
  if scheduleID in scheduleJSON['schedules']:
    abort(409, message='scheduleID already exists')
  for schedule in scheduleJSON['schedules']:
    if newScheduleData['sprinklerid'] == scheduleJSON['schedules'][schedule]['sprinklerid'] and newScheduleData['dow'] == scheduleJSON['schedules'][schedule]['dow'] and newScheduleData['starttime'] == scheduleJSON['schedules'][schedule]['starttime'] and newScheduleData['runtime'] == scheduleJSON['schedules'][schedule]['runtime']:
      abort(409, message='schedule already exists')

def checkRunningSprinklers(sprinklingInProgress):
  if sprinklingInProgress:
    abort(409, message='Sprinklers currently running, try again')

# Sprinkler Functions
def runSprinkler(gpioPIN, sprinklerRuntime, sprinklerName):
  global stopRunningRequest
  global sprinklingInProgress
  stopRunningRequest = False
  sprinklingInProgress = True
  pushMessage = f'START | {sprinklerName} | {sprinklerRuntime} minutes'
  raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
  if unitTestingMode == False:
    if messagingEnabled: sendMatrixMessage(pushMessage, roomid, timeout, True, token)
    if runningOnPi: GPIO.output(gpioPIN, True)
  now = datetime.now()
  while (now + timedelta(minutes=sprinklerRuntime)) > datetime.now() and stopRunningRequest == False and unitTestingMode == False:
    time.sleep(0.1)
  pushMessage = f'STOP  | {sprinklerName} | {sprinklerRuntime} minutes'
  raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
  if unitTestingMode == False:
    if messagingEnabled: sendMatrixMessage(pushMessage, roomid, timeout, True, token)
    if runningOnPi: GPIO.output(gpioPIN, False)

def sprinklerStats():
  scheduleJSON = importSchedule(scheduleFile)
  for sprinklerID in scheduleJSON['sprinklers']:
    weeklyRuntime = 0
    for scheduleID in scheduleJSON['schedules']:
      if scheduleJSON['schedules'][scheduleID]['sprinklerid'] == sprinklerID:
        weeklyRuntime += scheduleJSON['schedules'][scheduleID]['runtime']
    scheduleJSON['sprinklers'][sprinklerID]['weeklyruntime'] = weeklyRuntime
    scheduleJSON['sprinklers'][sprinklerID]['weeklygals'] = weeklyRuntime * scheduleJSON['sprinklers'][sprinklerID]['gallonspermin']
    writeScheduleJSON(scheduleJSON, scheduleFile)

# Schedule Functions
def importSchedule(scheduleFile):
  if Path(scheduleFile).is_file():
    retries = 5
    scheduleJSON = None
    while scheduleJSON == None and retries > 0:
      try:
        scheduleJSON = json.load(open(Path(scheduleFile)))
      except json.decoder.JSONDecodeError:
        retries -= 1
        time.sleep(0.1)
    return scheduleJSON
  else:
    return resetSchedule()

def resetSchedule():
  scheduleJSON = {# move this to default.json
                    "created": datetime.now().strftime("%a %m/%d %H:%M"),
                    "edited": datetime.now().strftime("%a %m/%d %H:%M"),
                    "raindelay":{
                      "startdate": None,
                      "enddate": None
                    },
                    "sprinklers":{

                    },
                    "schedules_edited": datetime.now().strftime("%a %m/%d %H:%M"),
                    "schedules":{

                    }
                  }
  return scheduleJSON

def writeScheduleJSON(scheduleJSON, scheduleFile):
  scheduleJSON['edited'] = datetime.now().strftime("%a %m/%d %H:%M")
  f = open(scheduleFile,"w")
  f.write(json.dumps(scheduleJSON, indent=2))
  f.close()

# Classes
class SprinklerBuilder(Resource):
  def get(self, sprinklerID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingSprinklerID(sprinklerID, scheduleJSON)
    return scheduleJSON['sprinklers'][sprinklerID], 200

  def put(self, sprinklerID):
    scheduleJSON = importSchedule(scheduleFile)
    checkNotExistingSprinklerID(sprinklerID, scheduleJSON)
    scheduleJSON['sprinklers'][sprinklerID] = sprinklerPutArgs.parse_args()
    if sprinklerPutArgs.parse_args()['gallonspermin'] == None:
      scheduleJSON['sprinklers'][sprinklerID]['gallonspermin'] = 0
    scheduleJSON['sprinklers'][sprinklerID]['inprogress'] = False
    scheduleJSON['sprinklers'][sprinklerID]['lastrequest'] = None
    scheduleJSON['sprinklers'][sprinklerID]['lastrun'] = None
    scheduleJSON['sprinklers'][sprinklerID]['weeklyruntime'] = 0
    scheduleJSON['sprinklers'][sprinklerID]['weeklygals'] = 0
    writeScheduleJSON(scheduleJSON, scheduleFile)
    return scheduleJSON['sprinklers'][sprinklerID], 201

  def patch(self, sprinklerID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingSprinklerID(sprinklerID, scheduleJSON)
    sprinklersChanged = False
    ### CLEANUP
    if sprinklerPatchArgs.parse_args()['sprinklername'] != None and sprinklerPatchArgs.parse_args()['sprinklername'] != '' and scheduleJSON['sprinklers'][sprinklerID]['sprinklername'] != sprinklerPatchArgs.parse_args()['sprinklername']:
      scheduleJSON['sprinklers'][sprinklerID]['sprinklername'] = sprinklerPatchArgs.parse_args()['sprinklername']
      sprinklersChanged = True
    if sprinklerPatchArgs.parse_args()['gallonspermin'] != None and sprinklerPatchArgs.parse_args()['gallonspermin'] != '' and scheduleJSON['sprinklers'][sprinklerID]['gallonspermin'] != sprinklerPatchArgs.parse_args()['gallonspermin']:
      scheduleJSON['sprinklers'][sprinklerID]['gallonspermin'] = sprinklerPatchArgs.parse_args()['gallonspermin']
      sprinklersChanged = True
    if sprinklersChanged:
      writeScheduleJSON(scheduleJSON, scheduleFile)
      return scheduleJSON['sprinklers'][sprinklerID], 201
    else:
      return scheduleJSON['sprinklers'][sprinklerID], 400
    ### CLEANUP

  def delete(self, sprinklerID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingSprinklerID(sprinklerID, scheduleJSON)
    del scheduleJSON['sprinklers'][sprinklerID]
    for sprinkler in scheduleJSON['schedules'].copy():
      if scheduleJSON['schedules'][sprinkler]['sprinklerid'] == sprinklerID:
        del scheduleJSON['schedules'][sprinkler]
    writeScheduleJSON(scheduleJSON, scheduleFile)
    return '', 204

class SprinklerGetAll(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    if len(scheduleJSON['sprinklers']) > 0:
      return (scheduleJSON['sprinklers'], 200)
    elif len(scheduleJSON['sprinklers']) == 0:
      return ('', 404)

class SprinklerGetID(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    return len(scheduleJSON['sprinklers']) + 1, 200

class ScheduleBuilder(Resource):
  def get(self, scheduleID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingScheduleID(scheduleID, scheduleJSON)
    return scheduleJSON['schedules'][scheduleID], 200

  def put(self, scheduleID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingSprinklerID(schedulePutArgs.parse_args()['sprinklerid'], scheduleJSON)
    checkNotExistingSchedule(schedulePutArgs.parse_args(), scheduleID, scheduleJSON)
    scheduleJSON['schedules'][scheduleID] = schedulePutArgs.parse_args()
    scheduleJSON['schedules_edited'] = datetime.now().strftime("%a %m/%d %H:%M")
    writeScheduleJSON(scheduleJSON, scheduleFile)
    sprinklerStats()
    return scheduleJSON['schedules'][scheduleID], 201

  def patch(self, scheduleID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingScheduleID(scheduleID, scheduleJSON)
    schedulesChanged = False
    ### CLEANUP
    if schedulePatchArgs.parse_args()['dow'] != None and schedulePatchArgs.parse_args()['dow'] != '' and scheduleJSON['schedules'][scheduleID]['dow'] != schedulePatchArgs.parse_args()['dow']:
      scheduleJSON['schedules'][scheduleID]['dow'] = schedulePatchArgs.parse_args()['dow']
      schedulesChanged = True
    if schedulePatchArgs.parse_args()['starttime'] != None and schedulePatchArgs.parse_args()['starttime'] != '' and scheduleJSON['schedules'][scheduleID]['starttime'] != schedulePatchArgs.parse_args()['starttime']:
      scheduleJSON['schedules'][scheduleID]['starttime'] = schedulePatchArgs.parse_args()['starttime']
      schedulesChanged = True
    if schedulePatchArgs.parse_args()['runtime'] != None and schedulePatchArgs.parse_args()['runtime'] != '' and scheduleJSON['schedules'][scheduleID]['runtime'] != schedulePatchArgs.parse_args()['runtime']:
      scheduleJSON['schedules'][scheduleID]['runtime'] = schedulePatchArgs.parse_args()['runtime']
      schedulesChanged = True
    if schedulesChanged:
      scheduleJSON['schedules_edited'] = datetime.now().strftime("%a %m/%d %H:%M")
      writeScheduleJSON(scheduleJSON, scheduleFile)
      sprinklerStats()
      return scheduleJSON['schedules'][scheduleID], 201
    else:
      return scheduleJSON['schedules'][scheduleID], 400
    ### CLEANUP

  def delete(self, scheduleID):
    scheduleJSON = importSchedule(scheduleFile)
    checkExistingScheduleID(scheduleID, scheduleJSON)
    del scheduleJSON['schedules'][scheduleID]
    scheduleJSON['schedules_edited'] = datetime.now().strftime("%a %m/%d %H:%M")
    writeScheduleJSON(scheduleJSON, scheduleFile)
    sprinklerStats()
    return '', 204

class ScheduleGetAll(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    if len(scheduleJSON['schedules']) > 0:
      return (scheduleJSON['schedules'], 200)
    elif len(scheduleJSON['schedules']) == 0:
      return ('', 404)

class ScheduleGetID(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    return len(scheduleJSON['schedules']) + 1, 200

class RainDelay(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    return scheduleJSON['raindelay'], 200

  def patch(self):
    scheduleJSON = importSchedule(scheduleFile)
    scheduleJSON['raindelay']['startdate'] = datetime.now().strftime("%a %m/%d/%y %H:%M")
    if scheduleJSON['raindelay']['enddate'] == None or datetime.now() >= datetime.strptime(scheduleJSON['raindelay']['enddate'], "%a %m/%d/%y %H:%M"): # None or In the Past
      scheduleJSON['raindelay']['enddate'] = (datetime.now() + timedelta(days=1)).strftime("%a %m/%d/%y %H:%M") # Schedule rain delay through tomorrow
    elif datetime.now() < datetime.strptime(scheduleJSON['raindelay']['enddate'], "%a %m/%d/%y %H:%M"):
      scheduleJSON['raindelay']['enddate'] = (datetime.strptime(scheduleJSON['raindelay']['enddate'], "%a %m/%d/%y %H:%M") + timedelta(days=1)).strftime("%a %m/%d/%y %H:%M") # Existing valid rain delay, increment by 1 day
    else:
      scheduleJSON['raindelay'] = {
                      "enddate": None
                    }
    writeScheduleJSON(scheduleJSON, scheduleFile)
    return scheduleJSON['raindelay'], 201

  def delete(self):
    scheduleJSON = importSchedule(scheduleFile)
    scheduleJSON['raindelay'] = {
                    "startdate": None,
                    "enddate": None
                  }
    writeScheduleJSON(scheduleJSON, scheduleFile)
    return '', 204

class RunAdhoc(Resource):
  def put(self, sprinklerID):
    global sprinklingInProgress
    checkRunningSprinklers(sprinklingInProgress)
    scheduleJSON = importSchedule(scheduleFile)
    sprinklerBuilder = SprinklerBuilder()
    sprinklerInfo, statusCode = sprinklerBuilder.get(sprinklerID)
    if statusCode == 200:
      raspiLog.info ('')
      pushMessage = f'ADHOC WATERING REQUEST STARTED'
      raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
      if unitTestingMode == False:
        #if messagingEnabled: sendMatrixMessage(pushMessage, roomid, timeout, True, token)
        pass
      adhocSprinklerThread = sprinklerThread(sprinklerID, sprinklerInfo['sprinklername'], runAdhocPutArgs.parse_args()['runtime'])
      adhocSprinklerThread.start()
      scheduleJSON['sprinklers'][sprinklerID]['inprogress'] = True
      scheduleJSON['sprinklers'][sprinklerID]['lastrequest'] = "Adhoc"
      scheduleJSON['sprinklers'][sprinklerID]['lastrun'] = datetime.now().strftime("%a %m/%d %H:%M")
      writeScheduleJSON(scheduleJSON, scheduleFile)
      monitorSprinklerThread = monitorThread(adhocSprinklerThread, "ADHOC", sprinklerID)
      monitorSprinklerThread.start()
      return '', 200

class RunSchedule(Resource):
  def put(self):
    global sprinklingInProgress
    checkRunningSprinklers(sprinklingInProgress)
    scheduleJSON = importSchedule(scheduleFile)
    scheduleBuilder = ScheduleBuilder()
    scheduleIDs = runSchedulePutArgs.parse_args()['scheduleids']
    for scheduleID in scheduleIDs:
      scheduleInfo = scheduleBuilder.get(scheduleID)
      if scheduleInfo[1] != 200:
        return scheduleIDs, 400
    sprinklerBuilder = SprinklerBuilder()
    scheduledSprinklerThreads = []
    raspiLog.info ('')
    pushMessage = f'SCHEDULED WATERING REQUEST STARTED'
    raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
    if scheduleJSON['raindelay']['enddate'] != None and datetime.now() < datetime.strptime(scheduleJSON['raindelay']['enddate'], "%a %m/%d/%y %H:%M"):
      pushMessage = f'RAIN DELAY UNTIL {scheduleJSON["raindelay"]["enddate"]}'
      raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
      if unitTestingMode == False and messagingEnabled:
        sendMatrixMessage(pushMessage, roomid, timeout, True, token)
      pushMessage = f'SCHEDULED WATERING REQUEST DELAYED'
      raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
      return '', 202
    sprinklerIDs = []
    for scheduleID in scheduleIDs:
      scheduleInfo = scheduleBuilder.get(scheduleID)
      sprinklerID = scheduleInfo[0]['sprinklerid']
      sprinklerIDs.append(sprinklerID)
      runTime = scheduleInfo[0]['runtime']
      sprinklerInfo = sprinklerBuilder.get(sprinklerID)
      sprinklerName = sprinklerInfo[0]['sprinklername']
      if scheduleInfo[1] == 200:
        scheduledSprinklerThreads.append(sprinklerThread(sprinklerID, sprinklerName, runTime))
        scheduledSprinklerThreads[-1].name = sprinklerID
        scheduledSprinklerThreads[-1].start()
        scheduleJSON['sprinklers'][sprinklerID]['inprogress'] = True
        scheduleJSON['sprinklers'][sprinklerID]['lastrequest'] = "Scheduled"
        scheduleJSON['sprinklers'][sprinklerID]['lastrun'] = datetime.now().strftime("%a %m/%d %H:%M")
        writeScheduleJSON(scheduleJSON, scheduleFile)
    monitorSprinklerThread = monitorThread(scheduledSprinklerThreads, "SCHEDULED", sprinklerIDs)
    monitorSprinklerThread.start()
    return '', 200

class StopRunning(Resource):
  def delete(self):
    global stopRunningRequest
    stopRunningRequest = True
    pushMessage = f'INTERRUPTING'
    raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
    if unitTestingMode == False:
      if messagingEnabled: sendMatrixMessage(pushMessage, roomid, timeout, True, token)
    return '', 200

class Config(Resource):
  def get(self):
    scheduleJSON = importSchedule(scheduleFile)
    return scheduleJSON, 200

class ResetAll(Resource):
  def delete(self):
    scheduleJSON = resetSchedule()
    writeScheduleJSON(scheduleJSON, scheduleFile)
    return '', 204

class Status(Resource):
  def get(self):
    global sprinklingInProgress
    if sprinklingInProgress:
      return 'Running', 200
    elif sprinklingInProgress == False:
      return 'Off', 200

class Metrics(Resource):
  def get(self):
    #scheduleJSON = importSchedule(scheduleFile)
    return 'Coming soon', 200

class UnitTesting(Resource):
  def put(self, mode):
    global unitTestingMode
    global scheduleFile
    if int(mode) == 1:
      raspiLog.info ('')
      raspiLog.info ('%s | ##########################', datetime.now().strftime("%a %m/%d %H:%M"))
      raspiLog.info ('%s | UNIT TESTING MODE STARTING', datetime.now().strftime("%a %m/%d %H:%M"))
      unitTestingMode = True
      scheduleFile = unitTestingPutArgs.parse_args()['filename']
      #unitTestingFlaskFile = unitTestingPutArgs.parse_args()['flaskfile']
      #unitTestingLogFile = unitTestingPutArgs.parse_args()['logfile']
      return 'On', 200
    elif int(mode) == 0:
      unitTestingMode = False
      scheduleFile = originalScheduleFile
      os.remove(unitTestingPutArgs.parse_args()['filename'])
      raspiLog.info ('')
      raspiLog.info ('%s | UNIT TESTING MODE COMPLETED', datetime.now().strftime("%a %m/%d %H:%M"))
      raspiLog.info ('%s | ###########################', datetime.now().strftime("%a %m/%d %H:%M"))
      return 'Off', 200

class sprinklerThread (threading.Thread):
  def __init__(self, sprinklerID, sprinklerName, runTime):
    threading.Thread.__init__(self)
    self.GPIO = customGPIOMapping(parsedArgs.channels, sprinklerID)
    self.sprinklerRuntime = runTime
    self.sprinklerName = sprinklerName
  def run(self):
    runSprinkler(self.GPIO, self.sprinklerRuntime, self.sprinklerName)

class monitorThread (threading.Thread):
  def __init__(self, threadsToMonitor, sprinklerRequestType, sprinklerIDs):
    threading.Thread.__init__(self)
    self.threadsToMonitor = threadsToMonitor
    self.sprinklerRequestType = sprinklerRequestType
    self.sprinklerIDs = sprinklerIDs
  def run(self):
    global sprinklingInProgress
    scheduleJSON = importSchedule(scheduleFile)
    if self.sprinklerRequestType == "ADHOC":
      while self.threadsToMonitor.is_alive():
        time.sleep(0.1)
      scheduleJSON['sprinklers'][self.sprinklerIDs]['inprogress'] = False
      scheduleJSON['sprinklers'][self.sprinklerIDs]['lastrun'] = datetime.now().strftime("%a %m/%d %H:%M")
      writeScheduleJSON(scheduleJSON, scheduleFile)
    elif self.sprinklerRequestType == "SCHEDULED":
      for runningThreads in self.threadsToMonitor:
        runningThreads.join()
        scheduleJSON['sprinklers'][runningThreads.name]['inprogress'] = False
        scheduleJSON['sprinklers'][runningThreads.name]['lastrun'] = datetime.now().strftime("%a %m/%d %H:%M")
        writeScheduleJSON(scheduleJSON, scheduleFile)
    pushMessage = f'{self.sprinklerRequestType} WATERING REQUEST COMPLETED'
    raspiLog.info ('%s | %s', datetime.now().strftime("%a %m/%d/%y %H:%M"), pushMessage)
    sprinklingInProgress = False

if __name__ == "__main__":
  # Global Variables
  stopRunningRequest = False
  sprinklingInProgress = False
  unitTestingMode = False

  # Matrix Variables
  timeout = 10
  roomid = '!IwbJqjlrJYdTAmYMTh:matrix.delchamps.io'
  token = 'syt_bm90aWZpZXI_KQflmLjKwCDbKYjMzwRH_4BwUMB'

  # Arg Parser
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles API")
  argParser.add_argument("-c", "--channels", type=int, help="Number of channels on the relay", default=8)
  argParser.add_argument("-f", "--flog", help="Path to Flask log file", default='/var/log/rs/flask.log')
  argParser.add_argument("-l", "--rslog", help="Path to Raspberry Sprinkles log file", default='/var/log/rs/raspberry-sprinkles.log')
  argParser.add_argument("-s", "--schedule", help="Path to schedule file (json)", default='/home/pi/git/raspberry-sprinkles/schedule.json')
  parsedArgs = argParser.parse_args()
  originalScheduleFile = scheduleFile = parsedArgs.schedule

  # Request Parser
  sprinklerPutArgs = reqparse.RequestParser()
  sprinklerPutArgs.add_argument('sprinklername', type=str, help="Name of sprinkler", location='form', required=True)
  sprinklerPutArgs.add_argument('gallonspermin', type=int, help="Gallons per minute", location='form')
  sprinklerPatchArgs = reqparse.RequestParser()
  sprinklerPatchArgs.add_argument('sprinklername', type=str, help="Name of sprinkler", location='form')
  sprinklerPatchArgs.add_argument('gallonspermin', type=int, help="Gallons per minute", location='form')
  schedulePutArgs = reqparse.RequestParser()
  schedulePutArgs.add_argument('sprinklerid', type=str, help="Name of sprinkler", location='form', required=True)
  schedulePutArgs.add_argument('dow', type=str, help="Day of Week to run sprinkler", location='form', required=True)
  schedulePutArgs.add_argument('starttime', type=str, help="Time of day to start sprinkler", location='form', required=True)
  schedulePutArgs.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form', required=True)
  schedulePatchArgs = reqparse.RequestParser()
  schedulePatchArgs.add_argument('dow', type=str, help="Day of Week to run sprinkler", location='form')
  schedulePatchArgs.add_argument('starttime', type=str, help="Time of day to start sprinkler", location='form')
  schedulePatchArgs.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form')
  runAdhocPutArgs = reqparse.RequestParser()
  runAdhocPutArgs.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form', required=True)
  runSchedulePutArgs = reqparse.RequestParser()
  runSchedulePutArgs.add_argument('scheduleids', action='append', help="Sprinkler IDs", location='form', required=True)
  unitTestingPutArgs = reqparse.RequestParser()
  unitTestingPutArgs.add_argument('filename', type=str, help="Name of unit testing json file", location='form', required=True)

  # Logging
  werkzeugLogger = logging.getLogger("werkzeug")
  werkzeugLogger.setLevel(logging.DEBUG)
  wLH = logging.FileHandler(parsedArgs.flog)
  werkzeugLogger.addHandler(wLH)
  raspiLog = logging.getLogger("raspi")
  raspiLog.setLevel(logging.INFO)
  rLH = logging.FileHandler(parsedArgs.rslog)
  rLH.setFormatter(logging.Formatter('%(message)s'))
  raspiLog.addHandler(rLH)

  # GPIO
  if customGPIOMapping(parsedArgs.channels, 1) == None:
    raspiLog.info ('%s | ERROR - Invalid gpiorelay mapping - ERROR', datetime.now().strftime("%a %m/%d %H:%M"))
    sys.exit()
  elif runningOnPi:
    # Set GPIO Mode
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Set GPIO as Output & False/Off
    raspiLog.info ('')
    for channel in range(parsedArgs.channels):
      if channel == 0:
        continue
      raspiLog.info('%s | Channel: %s GPIO: %s', datetime.now().strftime("%a %m/%d %H:%M"), channel, customGPIOMapping(parsedArgs.channels, channel))
      GPIO.setup(customGPIOMapping(parsedArgs.channels, channel), GPIO.OUT)
      GPIO.output(customGPIOMapping(parsedArgs.channels, channel), False)

  # Begin
  raspiLog.info ('')
  raspiLog.info ('%s | STARTING RASPBERRY SPRINKLES API', datetime.now().strftime("%a %m/%d %H:%M"))
  scheduleJSON = importSchedule(scheduleFile)
  for sprinkler in scheduleJSON['sprinklers']:
    if scheduleJSON['sprinklers'][sprinkler]['inprogress']:
      scheduleJSON['sprinklers'][sprinkler]['inprogress'] = False
      writeScheduleJSON(scheduleJSON, scheduleFile)

  # Flask
  app = Flask(__name__)
  CORS(app)
  api = Api(app)
  api.add_resource(SprinklerBuilder, "/sprinklerbuilder/<sprinklerID>")
  api.add_resource(SprinklerGetAll, "/sprinklergetall")
  api.add_resource(SprinklerGetID, "/sprinklergetid")
  api.add_resource(ScheduleBuilder, "/schedulebuilder/<scheduleID>")
  api.add_resource(ScheduleGetAll, "/schedulegetall")
  api.add_resource(ScheduleGetID, "/schedulegetid")
  api.add_resource(RainDelay, "/raindelay")
  api.add_resource(RunAdhoc, "/runadhoc/<sprinklerID>")
  api.add_resource(RunSchedule, "/runschedule")
  api.add_resource(StopRunning, "/stoprunning")
  api.add_resource(Config, "/config")
  api.add_resource(ResetAll, "/resetall")
  api.add_resource(Status, "/status")
  api.add_resource(Metrics, "/metrics")
  api.add_resource(UnitTesting, "/unittesting/<mode>")
  app.run(host='0.0.0.0', port=5000)
  #app.run(debug=True)
  #ssl_context='adhoc'