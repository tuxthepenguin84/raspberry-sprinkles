# Modules
from datetime import datetime, timedelta
from flask import Flask
from flask_cors import CORS
from flask_restful import abort, Api, reqparse, Resource
import json
import os
import RPi.GPIO as gpio
import sys
import threading
import time

# Import raspberry-sprinkles Modules
import rsclient as rsc

# Functions
def message_out(message):
  if unit_testing_mode == False and matrix_enabled:
    dmessage.send_matrix_message(message, matrix_room_id, matrix_token)
  message = f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | {message}'
  print(message)

# GPIO Functions
def gpio_mapping(total_channels, channel):
  three_channel = {
    1: 26,
    2: 20,
    3: 21
  }
  eight_channel = {
    1: 5,   # Grey Green
    2: 6,   # Grey Red
    3: 13,  # Grey Blue
    4: 16,  # Brown Red
    5: 19,  # Brown Blue
    6: 20,  # Blank - Used for Testing
    7: 21,  # Blank
    8: 26   # Blank
  }

  if total_channels == 8:
    return eight_channel[int(channel)]
  elif total_channels == 3:
    return three_channel[int(channel)]
  else:
    return None

# Check Functions
def check_existing_sprinkler_id(sprinkler_id, schedule_json):
  if sprinkler_id not in schedule_json['sprinklers']:
    abort(404, message='Could not find sprinkler_id')

def check_not_existing_sprinkler_id(sprinkler_id, schedule_json):
  if sprinkler_id in schedule_json['sprinklers']:
    abort(409, message='sprinkler_id already exists')

def check_existing_schedule_id(schedule_id, schedule_json):
  if schedule_id not in schedule_json['schedules']:
    abort(404, message='Could not find schedule_id')

def check_not_existing_schedule(new_schedule_data, schedule_id, schedule_json):
  if schedule_id in schedule_json['schedules']:
    abort(409, message='schedule_id already exists')
  for schedule in schedule_json['schedules']:
    if new_schedule_data['sprinklerid'] == schedule_json['schedules'][schedule]['sprinklerid'] and new_schedule_data['dow'] == schedule_json['schedules'][schedule]['dow'] and new_schedule_data['starttime'] == schedule_json['schedules'][schedule]['starttime'] and new_schedule_data['runtime'] == schedule_json['schedules'][schedule]['runtime']:
      abort(409, message='schedule already exists')

def check_running_sprinklers(sprinkle_in_progress):
  if sprinkle_in_progress:
    abort(409, message='Sprinklers currently running, try again')

# Sprinkler Functions
def run_sprinkler(gpio_pin, sprinkler_runtime, sprinkler_name):
  global stop_running_request
  global sprinkle_in_progress
  stop_running_request = False
  sprinkle_in_progress = True
  if unit_testing_mode == False:
    gpio.output(gpio_pin, True)
    message = f'START | {sprinkler_name} | {sprinkler_runtime} minutes'
    message_out(message)
    if db_enabled:
      db_values = (
        datetime.now().strftime(date_format_mon_day_year),
        datetime.now().strftime(time_format_hour_min_sec),
        sprinkler_name,
        'start',
        sprinkler_runtime
      )
      ddatabase.insert_into_db(db_connection_info, db_table, db_columns, db_values)

    endTime = datetime.now() + timedelta(minutes=sprinkler_runtime)
    while endTime > datetime.now() and stop_running_request == False:
      time.sleep(1)

    gpio.output(gpio_pin, False)
    message = f'STOP  | {sprinkler_name} | {sprinkler_runtime} minutes'
    message_out(message)
    if db_enabled:
      db_values = (
        datetime.now().strftime(date_format_mon_day_year),
        datetime.now().strftime(time_format_hour_min_sec),
        sprinkler_name,
        'stop',
        sprinkler_runtime
      )
      ddatabase.insert_into_db(db_connection_info, db_table, db_columns, db_values)

def sprinkler_stats():
  schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
  for sprinkler_id in schedule_json['sprinklers']:
    weekly_runtime = 0
    for schedule_id in schedule_json['schedules']:
      if schedule_json['schedules'][schedule_id]['sprinklerid'] == sprinkler_id:
        weekly_runtime += schedule_json['schedules'][schedule_id]['runtime']
    schedule_json['sprinklers'][sprinkler_id]['weeklyruntime'] = weekly_runtime
    schedule_json['sprinklers'][sprinkler_id]['weeklygals'] = weekly_runtime * schedule_json['sprinklers'][sprinkler_id]['gallonspermin']
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)

# Classes
class SprinklerBuilder(Resource):
  def get(self, sprinkler_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_sprinkler_id(sprinkler_id, schedule_json)
    return schedule_json['sprinklers'][sprinkler_id], 200

  def put(self, sprinkler_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_not_existing_sprinkler_id(sprinkler_id, schedule_json)
    schedule_json['sprinklers'][sprinkler_id] = sprinkler_put_args.parse_args()
    if sprinkler_put_args.parse_args()['gallonspermin'] == None:
      schedule_json['sprinklers'][sprinkler_id]['gallonspermin'] = 0
    schedule_json['sprinklers'][sprinkler_id]['history'] = []
    schedule_json['sprinklers'][sprinkler_id]['inprogress'] = False
    schedule_json['sprinklers'][sprinkler_id]['lastrequest'] = None
    schedule_json['sprinklers'][sprinkler_id]['lastrun'] = None
    schedule_json['sprinklers'][sprinkler_id]['weeklyruntime'] = 0
    schedule_json['sprinklers'][sprinkler_id]['weeklygals'] = 0
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    return schedule_json['sprinklers'][sprinkler_id], 201

  def patch(self, sprinkler_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_sprinkler_id(sprinkler_id, schedule_json)
    sprinklers_changed = False
    ### CLEANUP
    if sprinkler_patch_args.parse_args()['sprinklername'] != None and sprinkler_patch_args.parse_args()['sprinklername'] != '' and schedule_json['sprinklers'][sprinkler_id]['sprinklername'] != sprinkler_patch_args.parse_args()['sprinklername']:
      schedule_json['sprinklers'][sprinkler_id]['sprinklername'] = sprinkler_patch_args.parse_args()['sprinklername']
      sprinklers_changed = True
    if sprinkler_patch_args.parse_args()['gallonspermin'] != None and sprinkler_patch_args.parse_args()['gallonspermin'] != '' and schedule_json['sprinklers'][sprinkler_id]['gallonspermin'] != sprinkler_patch_args.parse_args()['gallonspermin']:
      schedule_json['sprinklers'][sprinkler_id]['gallonspermin'] = sprinkler_patch_args.parse_args()['gallonspermin']
      sprinklers_changed = True
    if sprinklers_changed:
      rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
      return schedule_json['sprinklers'][sprinkler_id], 201
    else:
      return schedule_json['sprinklers'][sprinkler_id], 400
    ### CLEANUP

  def delete(self, sprinkler_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_sprinkler_id(sprinkler_id, schedule_json)
    del schedule_json['sprinklers'][sprinkler_id]
    for sprinkler in schedule_json['schedules'].copy():
      if schedule_json['schedules'][sprinkler]['sprinklerid'] == sprinkler_id:
        del schedule_json['schedules'][sprinkler]
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    return '', 204

class SprinklerGetAll(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    if len(schedule_json['sprinklers']) > 0:
      return (schedule_json['sprinklers'], 200)
    elif len(schedule_json['sprinklers']) == 0:
      return ('', 404)

class SprinklerGetID(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    return len(schedule_json['sprinklers']) + 1, 200

class ScheduleBuilder(Resource):
  def get(self, schedule_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_schedule_id(schedule_id, schedule_json)
    return schedule_json['schedules'][schedule_id], 200

  def put(self, schedule_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_sprinkler_id(schedule_put_args.parse_args()['sprinklerid'], schedule_json)
    check_not_existing_schedule(schedule_put_args.parse_args(), schedule_id, schedule_json)
    schedule_json['schedules'][schedule_id] = schedule_put_args.parse_args()
    schedule_json['schedules_edited'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    sprinkler_stats()
    return schedule_json['schedules'][schedule_id], 201

  def patch(self, schedule_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_schedule_id(schedule_id, schedule_json)
    schedulesChanged = False
    ### CLEANUP
    if schedule_patch_args.parse_args()['dow'] != None and schedule_patch_args.parse_args()['dow'] != '' and schedule_json['schedules'][schedule_id]['dow'] != schedule_patch_args.parse_args()['dow']:
      schedule_json['schedules'][schedule_id]['dow'] = schedule_patch_args.parse_args()['dow']
      schedulesChanged = True
    if schedule_patch_args.parse_args()['starttime'] != None and schedule_patch_args.parse_args()['starttime'] != '' and schedule_json['schedules'][schedule_id]['starttime'] != schedule_patch_args.parse_args()['starttime']:
      schedule_json['schedules'][schedule_id]['starttime'] = schedule_patch_args.parse_args()['starttime']
      schedulesChanged = True
    if schedule_patch_args.parse_args()['runtime'] != None and schedule_patch_args.parse_args()['runtime'] != '' and schedule_json['schedules'][schedule_id]['runtime'] != schedule_patch_args.parse_args()['runtime']:
      schedule_json['schedules'][schedule_id]['runtime'] = schedule_patch_args.parse_args()['runtime']
      schedulesChanged = True
    if schedulesChanged:
      schedule_json['schedules_edited'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
      rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
      sprinkler_stats()
      return schedule_json['schedules'][schedule_id], 201
    else:
      return schedule_json['schedules'][schedule_id], 400
    ### CLEANUP

  def delete(self, schedule_id):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    check_existing_schedule_id(schedule_id, schedule_json)
    del schedule_json['schedules'][schedule_id]
    schedule_json['schedules_edited'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    sprinkler_stats()
    return '', 204

class ScheduleGetAll(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    if len(schedule_json['schedules']) > 0:
      return (schedule_json['schedules'], 200)
    elif len(schedule_json['schedules']) == 0:
      return ('', 404)

class ScheduleGetID(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    return len(schedule_json['schedules']) + 1, 200

class RainDelay(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    return schedule_json['raindelay'], 200

  def patch(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    schedule_json['raindelay']['startdate'] = datetime.now().strftime(time_format_dow_mon_day_year_hour_min)
    if schedule_json['raindelay']['enddate'] == None or datetime.now() >= datetime.strptime(schedule_json['raindelay']['enddate'], time_format_dow_mon_day_year_hour_min): # None or In the Past
      schedule_json['raindelay']['enddate'] = (datetime.now() + timedelta(days=1)).strftime(time_format_dow_mon_day_year_hour_min) # Schedule rain delay through tomorrow
    elif datetime.now() < datetime.strptime(schedule_json['raindelay']['enddate'], time_format_dow_mon_day_year_hour_min):
      schedule_json['raindelay']['enddate'] = (datetime.strptime(schedule_json['raindelay']['enddate'], time_format_dow_mon_day_year_hour_min) + timedelta(days=1)).strftime(time_format_dow_mon_day_year_hour_min) # Existing valid rain delay, increment by 1 day
    else:
      schedule_json['raindelay'] = {
                      "enddate": None
                    }
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    return schedule_json['raindelay'], 201

  def delete(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    schedule_json['raindelay'] = {
                    "startdate": None,
                    "enddate": None
                  }
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    return '', 204

class RunAdhoc(Resource):
  def put(self, sprinkler_id):
    global sprinkle_in_progress
    check_running_sprinklers(sprinkle_in_progress)
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    sprinkler_builder = SprinklerBuilder()
    sprinklerInfo, status_code = sprinkler_builder.get(sprinkler_id)
    if status_code == 200:
      message = f'ADHOC WATERING REQUEST STARTED'
      message_out(message)
      adhoc_sprinkler_thread = sprinklerThread(sprinkler_id, sprinklerInfo['sprinklername'], run_adhoc_put_args.parse_args()['runtime'])
      adhoc_sprinkler_thread.start()
      schedule_json['sprinklers'][sprinkler_id]['history'].append(datetime.now().strftime(time_format_dow_mon_day_hour_min))
      schedule_json['sprinklers'][sprinkler_id]['inprogress'] = True
      schedule_json['sprinklers'][sprinkler_id]['lastrequest'] = "Adhoc"
      schedule_json['sprinklers'][sprinkler_id]['lastrun'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
      rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
      monitor_sprinkler_thread = monitorThread(adhoc_sprinkler_thread, "ADHOC", sprinkler_id)
      monitor_sprinkler_thread.start()
      return '', 200

class RunSchedule(Resource):
  def put(self):
    global sprinkle_in_progress
    check_running_sprinklers(sprinkle_in_progress)
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    scheduleBuilder = ScheduleBuilder()
    schedule_ids = run_schedule_put_args.parse_args()['scheduleids']
    for schedule_id in schedule_ids:
      scheduleInfo = scheduleBuilder.get(schedule_id)
      if scheduleInfo[1] != 200:
        return schedule_ids, 400
    sprinkler_builder = SprinklerBuilder()
    scheduled_sprinkler_threads = []
    if schedule_json['raindelay']['enddate'] != None and datetime.now() < datetime.strptime(schedule_json['raindelay']['enddate'], time_format_dow_mon_day_year_hour_min):
      message = f'RAIN DELAY UNTIL {schedule_json["raindelay"]["enddate"]}'
      message_out(message)
      return '', 202
    sprinkler_ids = []
    for schedule_id in schedule_ids:
      scheduleInfo = scheduleBuilder.get(schedule_id)
      sprinkler_id = scheduleInfo[0]['sprinklerid']
      sprinkler_ids.append(sprinkler_id)
      run_time = scheduleInfo[0]['runtime']
      sprinklerInfo = sprinkler_builder.get(sprinkler_id)
      sprinkler_name = sprinklerInfo[0]['sprinklername']
      if scheduleInfo[1] == 200:
        scheduled_sprinkler_threads.append(sprinklerThread(sprinkler_id, sprinkler_name, run_time))
        scheduled_sprinkler_threads[-1].name = sprinkler_id
        scheduled_sprinkler_threads[-1].start()
        schedule_json['sprinklers'][sprinkler_id]['history'].append(datetime.now().strftime(time_format_dow_mon_day_hour_min))
        schedule_json['sprinklers'][sprinkler_id]['inprogress'] = True
        schedule_json['sprinklers'][sprinkler_id]['lastrequest'] = "Scheduled"
        schedule_json['sprinklers'][sprinkler_id]['lastrun'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
        rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    monitor_sprinkler_thread = monitorThread(scheduled_sprinkler_threads, "SCHEDULED", sprinkler_ids)
    monitor_sprinkler_thread.start()
    return '', 200

class StopRunning(Resource):
  def delete(self):
    global stop_running_request
    stop_running_request = True
    message = f'INTERRUPTING'
    message_out(message)
    return '', 200

class Config(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    return schedule_json, 200

class ResetAll(Resource):
  def delete(self):
    schedule_json = rsc.reset_schedule(time_format_dow_mon_day_hour_min)
    rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    return '', 204

class Status(Resource):
  def get(self):
    global sprinkle_in_progress
    if sprinkle_in_progress:
      return 'running', 200
    elif sprinkle_in_progress == False:
      return 'stopped', 200

class Health(Resource):
  def get(self):
    return 'up', 200

class Metrics(Resource):
  def get(self):
    #schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    return 'Coming soon', 200

class NextRun(Resource):
  def get(self):
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    day_mapping = {
      "Mon": 0,
      "Tue": 1,
      "Wed": 2,
      "Thu": 3,
      "Fri": 4,
      "Sat": 5,
      "Sun": 6,
    }
    now = datetime.now()
    current_day = now.weekday()
    next_sprinkler_time = None
    return '', 200
    if schedule_json['schedules']:
      for schedule in schedule_json['schedules'].values():
        schedule_day = day_mapping[schedule['dow']]
        start_time = datetime.strptime(schedule['starttime'], time_format_hour_min).time()

        if schedule_day >= current_day:
          scheduled_datetime = datetime.combine(now.date() + timedelta(days=(schedule_day - current_day)), start_time)
        else:
          scheduled_datetime = datetime.combine(now.date() + timedelta(days=(7 - current_day + schedule_day)), start_time)

        if (next_sprinkler_time is None or scheduled_datetime < next_sprinkler_time) and start_time > now.time():
          next_sprinkler_time = scheduled_datetime
      return next_sprinkler_time.strftime(time_format_dow_mon_day_hour_min), 200


class UnitTesting(Resource):
  def put(self, mode):
    global unit_testing_mode
    global schedule_file
    if int(mode) == 1:
      print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | ##########################')
      print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | UNIT TESTING MODE STARTING')
      unit_testing_mode = True
      schedule_file = unit_testing_put_args.parse_args()['filename']
      #unitTestingFlaskFile = unit_testing_put_args.parse_args()['flaskfile']
      #unitTestingLogFile = unit_testing_put_args.parse_args()['logfile']
      return 'On', 200
    elif int(mode) == 0:
      unit_testing_mode = False
      schedule_file = original_schedule_file
      os.remove(unit_testing_put_args.parse_args()['filename'])
      print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | UNIT TESTING MODE COMPLETED')
      print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | ###########################')
      return 'Off', 200

class sprinklerThread (threading.Thread):
  def __init__(self, sprinkler_id, sprinkler_name, run_time):
    threading.Thread.__init__(self)
    self.GPIO = gpio_mapping(gpio_channels, sprinkler_id)
    self.sprinkler_runtime = run_time
    self.sprinkler_name = sprinkler_name
  def run(self):
    run_sprinkler(self.GPIO, self.sprinkler_runtime, self.sprinkler_name)

class monitorThread (threading.Thread):
  def __init__(self, threads_to_monitor, sprinkler_request_type, sprinkler_ids):
    threading.Thread.__init__(self)
    self.threads_to_monitor = threads_to_monitor
    self.sprinkler_request_type = sprinkler_request_type
    self.sprinkler_ids = sprinkler_ids
  def run(self):
    global sprinkle_in_progress
    schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
    if self.sprinkler_request_type == "ADHOC":
      while self.threads_to_monitor.is_alive():
        time.sleep(0.1)
      schedule_json['sprinklers'][self.sprinkler_ids]['inprogress'] = False
      schedule_json['sprinklers'][self.sprinkler_ids]['lastrun'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
      rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    elif self.sprinkler_request_type == "SCHEDULED":
      for running_threads in self.threads_to_monitor:
        running_threads.join()
        schedule_json['sprinklers'][running_threads.name]['inprogress'] = False
        schedule_json['sprinklers'][running_threads.name]['lastrun'] = datetime.now().strftime(time_format_dow_mon_day_hour_min)
        rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)
    sprinkle_in_progress = False

def main():
  # Flask
  app = Flask(__name__)
  CORS(app)
  api = Api(app)
  api.add_resource(SprinklerBuilder, "/sprinklerbuilder/<sprinkler_id>")
  api.add_resource(SprinklerGetAll, "/sprinklergetall")
  api.add_resource(SprinklerGetID, "/sprinklergetid")
  api.add_resource(ScheduleBuilder, "/schedulebuilder/<schedule_id>")
  api.add_resource(ScheduleGetAll, "/schedulegetall")
  api.add_resource(ScheduleGetID, "/schedulegetid")
  api.add_resource(RainDelay, "/raindelay")
  api.add_resource(RunAdhoc, "/runadhoc/<sprinkler_id>")
  api.add_resource(RunSchedule, "/runschedule")
  api.add_resource(StopRunning, "/stoprunning")
  api.add_resource(Config, "/config")
  api.add_resource(ResetAll, "/resetall")
  api.add_resource(Status, "/status")
  api.add_resource(Health, "/health")
  api.add_resource(Metrics, "/metrics")
  api.add_resource(NextRun, "/nextrun")
  api.add_resource(UnitTesting, "/unittesting/<mode>")
  app.run(host='0.0.0.0', port=5000)
  #app.run(debug=True)
  #ssl_context='adhoc'

if __name__ == "__main__":
  # Variables
  date_format_mon_day_year = "%m/%d/%Y"
  stop_running_request = False
  sprinkle_in_progress = False
  time_format_dow_mon_day_hour_min = "%a %m/%d %H:%M"
  time_format_dow_mon_day_year_hour_min = "%a %m/%d/%y %H:%M"
  time_format_hour_min_sec = "%H:%M:%S"
  time_format_hour_min = "%H:%M"
  unit_testing_mode = False

  # Import params.json Data
  params_file = os.path.join(script_dir, 'params.json')
  params_json = dutils.load_json_file(params_file)
  if params_json is None:
    print(f'Unable to import {params_file} data')
    sys.exit(1)

  # Import Database Connection Data
  if 'database' in params_json:
    db_enabled = True
    db_json = params_json['database']
    db_columns = db_json['columns']
    db_connection_info = db_json['connection']
    db_retries = db_json['retries']
    db_table = db_json['table']
  else:
    db_enabled = False
    db_columns = None
    db_connection_info = None
    db_retries = None
    db_table = None

  # Import GPIO Data
  gpio_json = params_json['gpio']
  gpio_channels = gpio_json['channels']

  # Import Matrix Data
  if 'matrix' in params_json:
    matrix_enabled = True
    matrix_json = params_json['matrix']
    matrix_room_id = matrix_json['roomid']
    matrix_token = matrix_json['token']
  else:
    matrix_enabled = False
    matrix_room_id = None
    matrix_token = None

  # Import Schedule Data
  original_schedule_file = schedule_file = os.path.join(script_dir, 'schedule.json')
  schedule_json = rsc.import_schedule(schedule_file, time_format_dow_mon_day_hour_min)
  if schedule_json is None:
    print('Unable to import schedule data')
    sys.exit(1)
  print(json.dumps(schedule_json, indent=2))
  if schedule_json['sprinklers']:
    for sprinkler in schedule_json['sprinklers']:
      if schedule_json['sprinklers'][sprinkler]['inprogress']:
        schedule_json['sprinklers'][sprinkler]['inprogress'] = False
        rsc.write_schedule(schedule_json, schedule_file, time_format_dow_mon_day_hour_min)

  # GPIO
  if gpio_mapping(gpio_channels, 1) is None:
    print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | ERROR - Invalid gpiorelay mapping - ERROR')
    sys.exit(1)
  else:
    # Set GPIO Mode
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)

    # Set GPIO as Output & False/Off
    for channel in range(gpio_channels):
      if channel == 0:
        continue
      print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | Channel: {channel} GPIO: {gpio_mapping(gpio_channels, channel)}')
      gpio.setup(gpio_mapping(gpio_channels, channel), gpio.OUT)
      gpio.output(gpio_mapping(gpio_channels, channel), False)

  # Startup
  startup = {
    'RELAY_CHANNELS': gpio_channels,
    'SCHEDULE': schedule_file,
    'DB_COLUMNS': db_columns,
    'DB_CONN_INFO': db_connection_info,
    'DB_RETRIES': db_retries,
    'DB_TABLE': db_table,
    'MATRIXROOMID': matrix_room_id,
    'MATRIXTOKEN': matrix_token
  }

  print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | STARTING RASPBERRY SPRINKLES API')
  for key, value in startup.items():
    print(f'{datetime.now().strftime(time_format_dow_mon_day_hour_min)} | {key}: {value}')

  # Request Parser
  sprinkler_put_args = reqparse.RequestParser()
  sprinkler_put_args.add_argument('sprinklername', type=str, help="Name of sprinkler", location='form', required=True)
  sprinkler_put_args.add_argument('gallonspermin', type=int, help="Gallons per minute", location='form')
  sprinkler_patch_args = reqparse.RequestParser()
  sprinkler_patch_args.add_argument('sprinklername', type=str, help="Name of sprinkler", location='form')
  sprinkler_patch_args.add_argument('gallonspermin', type=int, help="Gallons per minute", location='form')
  schedule_put_args = reqparse.RequestParser()
  schedule_put_args.add_argument('sprinklerid', type=str, help="Name of sprinkler", location='form', required=True)
  schedule_put_args.add_argument('dow', type=str, help="Day of Week to run sprinkler", location='form', required=True)
  schedule_put_args.add_argument('starttime', type=str, help="Time of day to start sprinkler", location='form', required=True)
  schedule_put_args.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form', required=True)
  schedule_patch_args = reqparse.RequestParser()
  schedule_patch_args.add_argument('dow', type=str, help="Day of Week to run sprinkler", location='form')
  schedule_patch_args.add_argument('starttime', type=str, help="Time of day to start sprinkler", location='form')
  schedule_patch_args.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form')
  run_adhoc_put_args = reqparse.RequestParser()
  run_adhoc_put_args.add_argument('runtime', type=int, help="Runtime of sprinkler", location='form', required=True)
  run_schedule_put_args = reqparse.RequestParser()
  run_schedule_put_args.add_argument('scheduleids', action='append', help="Sprinkler IDs", location='form', required=True)
  unit_testing_put_args = reqparse.RequestParser()
  unit_testing_put_args.add_argument('filename', type=str, help="Name of unit testing json file", location='form', required=True)

  # Call Main Function
  main()
