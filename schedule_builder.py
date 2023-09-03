# Modules
import argparse
from datetime import datetime
import json

# Custom Modules
import rsclient

def main():
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Schedule Builder")
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()

  # Reset schedule
  rsclient.resetAllData(parsedArgs.url)

  # Add sprinkler (URL, Name, Gallons Per Min)
  rsclient.addSprinkler(parsedArgs.url, 'Front Bed  ', 3)
  rsclient.addSprinkler(parsedArgs.url, 'Front Lawn ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Side Fence ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Back Fence ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Back Garden', 1)

  # Seasons
  current_month = datetime.now().month
  month_to_season = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 1]
  seasons = {1:'winter', 2:'spring', 3:'summer', 4:'fall'}
  current_season = seasons[month_to_season[current_month - 1]]

  # Add schedule (URL, SprinklerID [index of above starting at 1], DoW, Start Time, Run Time [Min])
  if current_season == 'winter':
    #WINTER
    rsclient.addSchedule(parsedArgs.url, 1, 'Sun', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Mon', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Wed', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Fri', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Sun', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Mon', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Wed', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Fri', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Sun', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Mon', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Wed', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Fri', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Sun', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Mon', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Wed', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Fri', '05:30', '9')
  elif current_season == 'spring':
    # SPRING
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '19:00', '5')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '19:10', '5')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '19:20', '5')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '19:30', '5')
    rsclient.addSchedule(parsedArgs.url, 5, 'Everyday', '19:40', '20')
  elif current_season == 'summer':
    # SUMMER
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '19:00', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '19:10', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '19:20', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '19:30', '9')
    rsclient.addSchedule(parsedArgs.url, 5, 'Everyday', '19:40', '20')
  elif current_season == 'fall':
    # FALL
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '05:00', '9')
    rsclient.addSchedule(parsedArgs.url, 1, 'Everyday', '19:00', '5')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '05:10', '9')
    rsclient.addSchedule(parsedArgs.url, 2, 'Everyday', '19:10', '5')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '05:20', '9')
    rsclient.addSchedule(parsedArgs.url, 3, 'Everyday', '19:20', '5')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '05:30', '9')
    rsclient.addSchedule(parsedArgs.url, 4, 'Everyday', '19:30', '5')
    rsclient.addSchedule(parsedArgs.url, 5, 'Everyday', '19:40', '20')

  # ALL SEASONS
  rsclient.addSchedule(parsedArgs.url, 5, 'Everyday', '05:40', '20')

  # Show Schedule
  print(json.dumps(rsclient.getAllSchedules(parsedArgs.url).json(), indent=2))
  print(json.dumps(rsclient.getAllSprinklers(parsedArgs.url).json(), indent=2))

if __name__ == '__main__':
  main()