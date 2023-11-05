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

  # Seasons
  current_month = datetime.now().month
  month_to_season = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 1]
  seasons = {1:'winter', 2:'spring', 3:'summer', 4:'fall'}
  current_season = seasons[month_to_season[current_month - 1]]

  # Reset schedule
  rsclient.resetAllData(parsedArgs.url)

  # Add sprinkler (URL, Name, Gallons Per Min)
  rsclient.addSprinkler(parsedArgs.url, 'Front Bed  ', 3)
  rsclient.addSprinkler(parsedArgs.url, 'Front Lawn ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Side Fence ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Back Fence ', 5)
  rsclient.addSprinkler(parsedArgs.url, 'Back Garden', 1)

  # Add schedule
  #   (URL, SprinklerID [index of above starting at 1], DoW, Start Time, Run Time [Min])
  #
  # Examples
  #   Run sprinkler 1 "Front Bed" every day at 5:20 AM for 7 minutes
  #     rsclient.addSchedule(parsedArgs.url, 1, everyday, '05:20', 7)
  #   Run sprinkler 2 "Front Lawn" on Monday at 7:10 PM for 20 minutes
  #     rsclient.addSchedule(parsedArgs.url, 2, 'Mon', '19:10', 20)

  altdays = ['Sun', 'Mon', 'Wed', 'Fri']
  everyday = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
  weekend = ['Sun', 'Sat']

  if current_season == 'winter':
    #WINTER
    rsclient.addSchedule(parsedArgs.url, 1, altdays, '05:00', 5)
    rsclient.addSchedule(parsedArgs.url, 2, altdays, '05:10', 5)
    rsclient.addSchedule(parsedArgs.url, 3, altdays, '05:20', 5)
    rsclient.addSchedule(parsedArgs.url, 4, altdays, '05:30', 5)
    rsclient.addSchedule(parsedArgs.url, 5, altdays, '05:40', 12)
  elif current_season == 'spring':
    # SPRING
    rsclient.addSchedule(parsedArgs.url, 1, altdays, '05:00', 5)
    rsclient.addSchedule(parsedArgs.url, 2, altdays, '05:10', 5)
    rsclient.addSchedule(parsedArgs.url, 3, altdays, '05:20', 5)
    rsclient.addSchedule(parsedArgs.url, 4, altdays, '05:30', 5)
    rsclient.addSchedule(parsedArgs.url, 5, altdays, '05:40', 12)
  elif current_season == 'summer':
    # SUMMER
    rsclient.addSchedule(parsedArgs.url, 1, everyday, '05:00', 7)
    rsclient.addSchedule(parsedArgs.url, 2, everyday, '05:10', 7)
    rsclient.addSchedule(parsedArgs.url, 2, everyday, '19:10', 7)
    rsclient.addSchedule(parsedArgs.url, 3, everyday, '05:20', 7)
    rsclient.addSchedule(parsedArgs.url, 4, everyday, '05:30', 7)
    rsclient.addSchedule(parsedArgs.url, 5, everyday, '05:40', 20)
  elif current_season == 'fall':
    # FALL
    rsclient.addSchedule(parsedArgs.url, 1, altdays, '05:00', 5)
    rsclient.addSchedule(parsedArgs.url, 2, altdays, '05:10', 5)
    rsclient.addSchedule(parsedArgs.url, 3, altdays, '05:20', 5)
    rsclient.addSchedule(parsedArgs.url, 4, altdays, '05:30', 5)
    rsclient.addSchedule(parsedArgs.url, 5, altdays, '05:40', 12)

  # ALL SEASONS


  # Show Schedule
  print(json.dumps(rsclient.getAllSchedules(parsedArgs.url).json(), indent=2))
  print(json.dumps(rsclient.getAllSprinklers(parsedArgs.url).json(), indent=2))

if __name__ == '__main__':
  main()