# Modules
import argparse
from datetime import datetime
import json
from pathlib import Path
import requests
import schedule
import time

# Custom Modules
from rsclient import runSchedule, getRainDelay, patchRainDelay
from rsapi import importSchedule

# Weather Functions
def importWeatherParams(weatherFile):
  if Path(weatherFile).is_file():
    weatherJSON = None
    while weatherJSON == None:
      try:
        weatherJSON = json.load(open(Path(weatherFile)))
      except json.decoder.JSONDecodeError:
        time.sleep(0.1)
    return weatherJSON
  else:
    return None

def checkWeather(weatherParams):
  rainThreshold = 0.5 # Inches
  weatherAPIURL = 'https://api.open-meteo.com/v1/forecast'
  weatherAPITimeout = 30 # Seconds
  YMD = datetime.now().strftime("%Y-%m-%d")
  if weatherParams is not None:
    # Get weather from API
    weatherResponse = requests.get(weatherAPIURL, params=weatherParams, timeout=weatherAPITimeout)
    weatherResponseJSON = weatherResponse.json()
    # If rain threshold reached then request a rain delay
    dateIndex = weatherResponseJSON['daily']['time'].index(YMD)
    if weatherResponseJSON['daily']['rain_sum'][dateIndex] > rainThreshold:
      rainDelayReponse = getRainDelay(parsedArgs.url)
      if rainDelayReponse['raindelay']['enddate'] == None or datetime.now() >= datetime.strptime(rainDelayReponse['raindelay']['enddate'], "%a %m/%d/%y %H:%M"):
        patchRainDelay(parsedArgs.url)

def main():
  #Import Schedule
  scheduleJSON = importSchedule(parsedArgs.schedule)
  DoW = datetime.now().strftime("%a")
  HourMin = datetime.now().strftime("%H:%M")

  # Check if schedules fall within the day of week, hour, and minute
  scheduleIDs = []
  for schedule in scheduleJSON['schedules']:
    if DoW in scheduleJSON['schedules'][schedule]['dow'] and HourMin in scheduleJSON['schedules'][schedule]['starttime']:
      scheduleIDs.append(schedule)

  # Check if any valid schedules are within the time constraints
  if len(scheduleIDs) > 0:
    # Check weather
    weatherParams = importWeatherParams(parsedArgs.weather)
    checkWeather(weatherParams)
    # Run schedule
    runScheduleReponse = runSchedule(parsedArgs.url, scheduleIDs)
    print(runScheduleReponse, runScheduleReponse.json())

if __name__ == '__main__':
  # Arg Parser
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Automated Scheduler")
  argParser.add_argument("-s", "--schedule", help="schedule file", default='/home/pi/git/raspberry-sprinkles/schedule.json')
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  argParser.add_argument("-w", "--weather", help="Path to weather file (json)", default='/home/pi/git/raspberry-sprinkles/weather_params.json')
  parsedArgs = argParser.parse_args()

  # Schedule and main function every minute at :00 seconds
  schedule.every().minute.at(":00").do(main)
  while True:
    schedule.run_pending()
    time.sleep(1)