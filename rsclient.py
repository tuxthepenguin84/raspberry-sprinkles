import requests

def getAllSprinklers(baseURL):
  return requests.get(baseURL + 'sprinklergetall')

def getSprinklerID(baseURL):
  sprinklerLatestID = requests.get(baseURL + 'sprinklergetid')
  return sprinklerLatestID.json()

def getSprinkler(baseURL, sprinklerID):
  return requests.get(baseURL + 'sprinklerbuilder/' + str(sprinklerID))

def addSprinkler(baseURL, sprinklerName, gallonspermin):
  newSprinklerData = {
    'sprinklername': sprinklerName,
    'gallonspermin': gallonspermin
  }
  return requests.put(baseURL + 'sprinklerbuilder/' + str(getSprinklerID(baseURL)), newSprinklerData)

def updateSprinkler(baseURL, sprinklerID, sprinklerName, gallonspermin):
  updatedSprinklerData = {
    'sprinklername': sprinklerName,
    'gallonspermin': gallonspermin
  }
  return requests.patch(baseURL + 'sprinklerbuilder/' + str(sprinklerID), updatedSprinklerData)

def deleteSprinkler(baseURL, sprinklerID):
  return requests.delete(baseURL + 'sprinklerbuilder/' + str(sprinklerID))

def getAllSchedules(baseURL):
  return requests.get(baseURL + 'schedulegetall')

def getScheduleID(baseURL):
  response = requests.get(baseURL + 'schedulegetid')
  return response.json()

def getSchedule(baseUrl, scheduleID):
  return requests.get(baseUrl + 'schedulebuilder/' + str(scheduleID))

def addSchedule(baseURL, sprinklerID, DoW, startTime, runTime):
  if type(DoW) is list:
    for day in DoW:
      addSchedule(baseURL, sprinklerID, day, startTime, runTime)
  else:
    addScheduleData = {
      'sprinklerid': sprinklerID,
      'dow': DoW,
      'starttime': startTime,
      'runtime': runTime,
    }
    return requests.put(baseURL + 'schedulebuilder/' + str(getScheduleID(baseURL)), addScheduleData)

def updateSchedule(baseURL, scheduleID, DoW, startTime, runTime):
  if type(DoW) is list:
    for day in DoW:
      updateSchedule(baseURL, scheduleID, day, startTime, runTime)
  else:
    updatedScheduleData = {
      'dow': DoW,
      'starttime': startTime,
      'runtime': runTime,
    }
    return requests.patch(baseURL + 'schedulebuilder/' + str(scheduleID), updatedScheduleData)

def deleteSchedule(baseURL, scheduleID):
  return requests.delete(baseURL + 'schedulebuilder/' + str(scheduleID))

def getRainDelay(baseURL):
  return requests.get(baseURL + 'raindelay')

def patchRainDelay(baseURL):
  return requests.patch(baseURL + 'raindelay')

def deleteRainDelay(baseURL):
  return requests.delete(baseURL + 'raindelay')

def runAdhoc(baseURL, sprinklerID, runTime):
  runSprinklerData = {
    'runtime': runTime
  }
  return requests.put(baseURL + 'runadhoc/' + str(sprinklerID), runSprinklerData)

def runSchedule(baseURL, scheduleIDs):
  runScheduleData = {
    'scheduleids': scheduleIDs
  }
  return requests.put(baseURL + 'runschedule', runScheduleData)

def stopRunning(baseURL):
  return requests.delete(baseURL + 'stoprunning')

def resetAllData(baseURL):
  return requests.delete(baseURL + 'resetall')

def unitTesting(baseURL, mode, fileName):
  unitTestingData = {
    'filename': fileName
  }
  return requests.put(baseURL + 'unittesting/' + str(mode), unitTestingData)