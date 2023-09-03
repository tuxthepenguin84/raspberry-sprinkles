# Modules
import argparse
from datetime import datetime
import schedule
import time

# Custom Modules
from rsclient import runSchedule
from rsapi import importSchedule

def main():
  scheduleJSON = importSchedule(parsedArgs.schedule)
  DoW = datetime.now().strftime("%a")
  HourMin = datetime.now().strftime("%H:%M")
  scheduleIDs = []
  for schedule in scheduleJSON['schedules']:
    if DoW in scheduleJSON['schedules'][schedule]['dow'] and HourMin in scheduleJSON['schedules'][schedule]['starttime']:
      scheduleIDs.append(schedule)
  if len(scheduleIDs) > 0:
    response = runSchedule(parsedArgs.url, scheduleIDs)
    print(response, response.json())

if __name__ == '__main__':
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Automated Scheduler")
  argParser.add_argument("-s", "--schedule", help="schedule file", default='/home/pi/git/raspberry-sprinkles/schedule.json')
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()
  schedule.every().minute.at(":00").do(main)
  while True:
    schedule.run_pending()
    time.sleep(1)