# Modules
import argparse
from datetime import datetime
import json

# Import raspberry-sprinkles Modules
import rsclient as rsc

def main():
  # Seasons
  current_month = datetime.now().month
  month_to_season = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 1]
  seasons = {1:'winter', 2:'spring', 3:'summer', 4:'fall'}
  current_season = seasons[month_to_season[current_month - 1]]

  # Reset schedule
  rsc.reset_all_data(api_url)

  # Add sprinkler (URL, Name, Gallons Per Min)
  rsc.add_sprinkler(api_url, 'Front Bed  ', 3)
  rsc.add_sprinkler(api_url, 'Front Lawn ', 5)
  rsc.add_sprinkler(api_url, 'Side Fence ', 5)
  rsc.add_sprinkler(api_url, 'Back Fence ', 5)
  rsc.add_sprinkler(api_url, 'Back Garden', 1)
  rsc.add_sprinkler(api_url, 'Test       ', 1)

  # Add schedule
  #   (URL, SprinklerID [index of above starting at 1], DoW, Start Time, Run Time [Min])
  #
  # Examples
  #   Run sprinkler 1 "Front Bed" every day at 5:20 AM for 7 minutes
  #     rsc.add_schedule(api_url, 1, everyday, '05:20', 7)
  #   Run sprinkler 2 "Front Lawn" on Monday at 7:10 PM for 20 minutes
  #     rsc.add_schedule(api_url, 2, 'Mon', '19:10', 20)

  altdays = ['Sun', 'Mon', 'Wed', 'Fri']
  everyday = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
  weekend = ['Sun', 'Sat']

  disable_all_schedules = False

  if not disable_all_schedules:
    if current_season == 'winter':
      # WINTER
      rsc.add_schedule(api_url, 1, altdays, '05:00', 5)
      rsc.add_schedule(api_url, 2, altdays, '05:10', 5)
      rsc.add_schedule(api_url, 3, altdays, '05:20', 5)
      rsc.add_schedule(api_url, 4, altdays, '05:30', 5)
      rsc.add_schedule(api_url, 5, altdays, '05:40', 12)
    elif current_season == 'spring':
      # SPRING
      rsc.add_schedule(api_url, 1, altdays, '05:00', 5)
      rsc.add_schedule(api_url, 2, altdays, '05:10', 5)
      rsc.add_schedule(api_url, 2, altdays, '20:00', 5)
      rsc.add_schedule(api_url, 3, altdays, '05:20', 5)
      rsc.add_schedule(api_url, 4, altdays, '05:30', 5)
      rsc.add_schedule(api_url, 5, altdays, '05:40', 12)
    elif current_season == 'summer':
      # SUMMER
      rsc.add_schedule(api_url, 1, everyday, '05:00', 7)
      rsc.add_schedule(api_url, 2, everyday, '05:10', 7)
      rsc.add_schedule(api_url, 2, everyday, '20:00', 7)
      rsc.add_schedule(api_url, 3, everyday, '05:20', 7)
      rsc.add_schedule(api_url, 4, everyday, '05:30', 7)
      rsc.add_schedule(api_url, 5, everyday, '05:40', 20)
    elif current_season == 'fall':
      # FALL
      rsc.add_schedule(api_url, 1, altdays, '05:00', 5)
      rsc.add_schedule(api_url, 2, altdays, '05:10', 5)
      rsc.add_schedule(api_url, 3, altdays, '05:20', 5)
      rsc.add_schedule(api_url, 4, altdays, '05:30', 5)
      rsc.add_schedule(api_url, 5, altdays, '05:40', 12)
    # ALL SEASONS

    # TEST
    rsc.add_schedule(api_url, 6, 'Sat', '21:30', 1)


  # Show Schedule
  print(json.dumps(rsc.get_all_schedules(api_url).json(), indent=2))
  print(json.dumps(rsc.get_all_sprinklers(api_url).json(), indent=2))

if __name__ == '__main__':
  # Arg Parser
  arg_parser = argparse.ArgumentParser(description="Raspberry Sprinkles Schedule Builder")
  arg_parser.add_argument("--apiurl", help="Raspberry Sprinkles API URL", type=str, default='')
  parsedArgs = arg_parser.parse_args()
  print(parsedArgs)
  api_url = parsedArgs.apiurl

  # Call Main Function
  main()