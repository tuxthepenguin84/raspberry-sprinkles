# Modules
from datetime import datetime, timedelta
import json
import os
import requests
import schedule
import sys
import time

# Import raspberry-sprinkles Modules
import rsclient as rsc

# Functions
def check_weather(weather_params):
  if weather_params is not None:
    # Get weather from API
    weather_response_json = (requests.get(weather_api_forecast_url, params=weather_params, timeout=10)).json()
    # If rain threshold reached then request a rain delay
    total_rain = weather_response_json['daily']['rain_sum'][0] + weather_response_json['daily']['rain_sum'][1]
    if total_rain > rain_threshold:
      rain_delay_response_json = (rsc.get_rain_delay(api_url)).json()
      if rain_delay_response_json['enddate'] == None or datetime.now() >= datetime.strptime(rain_delay_response_json['enddate'], time_format_year):
        rsc.patch_rain_delay(api_url)

def main():
  #Import Schedule
  schedule_json = rsc.import_schedule(schedule_file, time_format)
  if schedule_json is None:
    print('Unable to import schedule data')
    sys.exit(1)
  delay_uptime_ping = datetime.now()
  dow = datetime.now().strftime("%a")
  hour_min = datetime.now().strftime("%H:%M")

  # Check if schedules fall within the day of week, hour, and minute
  schedule_ids = []
  for schedule in schedule_json['schedules']:
    if dow in schedule_json['schedules'][schedule]['dow'] and hour_min in schedule_json['schedules'][schedule]['starttime']:
      schedule_ids.append(schedule)

  # Check if any valid schedules are within the time constraints
  if len(schedule_ids) > 0:
    # Check weather
    check_weather(weather_params)
    # Run schedule
    run_schedule_response = rsc.run_schedule(api_url, schedule_ids)
    print(f'{datetime.now().strftime(time_format)} | Running ScheduleIDs: {schedule_ids} Response: {run_schedule_response}')

  if datetime.now() >= delay_uptime_ping:
    if uptime_enabled:
      dutils.ping_uptime(uptime_id)
      delay_uptime_ping = datetime.now() + timedelta(seconds=uptime_delay)

if __name__ == '__main__':
  # Variables
  time_format = "%a %m/%d %H:%M"
  time_format_year = "%a %m/%d/%y %H:%M"

  # Import params.json Data
  params_file = os.path.join(script_dir, 'params.json')
  params_json = dutils.load_json_file(params_file)
  if params_json is None:
    print(f'Unable to import {params_file} data')
    sys.exit(1)

  # Import API Data
  api_json = params_json['api']
  api_url = api_json['url']

  # Import Rain Threshold Data
  rain_json = params_json['rain']
  rain_threshold = rain_json['threshold']

  # Import Schedule Data
  schedule_file = os.path.join(script_dir, 'schedule.json')
  schedule_json = rsc.import_schedule(schedule_file, time_format)
  if schedule_json is None:
    print('Unable to import schedule data')
    sys.exit(1)
  print(json.dumps(schedule_json, indent=2))

  # Import Uptime Data
  if 'uptime' in params_json:
    uptime_enabled = True
    uptime_json = params_json['uptime']
    uptime_delay = uptime_json['delay']
    uptime_id = uptime_json['id']
  else:
    uptime_enabled = False
    uptime_delay = None
    uptime_id = None

  # Import Weather Data
  weather_json = params_json['weather']
  weather_api_forecast_url = weather_json['api_forecast_url']
  weather_params = weather_json['params']

  # Startup
  startup = {
    'APIURL': api_url,
    'SCHEDULE': schedule_file,
    'RAINTHRESHOLD': rain_threshold,
    'UPTIMEDELAY': uptime_delay,
    'UPTIMEID': uptime_id,
    'WEATHERURL': weather_api_forecast_url,
    'WEATHERPARAMS': weather_params
  }

  print(f'{datetime.now().strftime(time_format)} | STARTING RASPBERRY SPRINKLES SCHEDULER')
  for key, value in startup.items():
    print(f'{datetime.now().strftime(time_format)} | {key}: {value}')

  # Schedule and main function every minute at :00 seconds
  schedule.every().minute.at(":00").do(main)
  while True:
    schedule.run_pending()
    time.sleep(1)