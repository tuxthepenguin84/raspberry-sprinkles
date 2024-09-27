from datetime import datetime
import json
import os
import requests
import sys

def get_all_sprinklers(base_url):
  return requests.get(base_url + 'sprinklergetall')

def get_sprinkler_id(base_url):
  sprinkler_latest_id = requests.get(base_url + 'sprinklergetid')
  return sprinkler_latest_id.json()

def get_sprinkler(base_url, sprinkler_id):
  return requests.get(base_url + 'sprinklerbuilder/' + str(sprinkler_id))

def add_sprinkler(base_url, sprinkler_name, gallonspermin):
  new_sprinkler_data = {
    'sprinklername': sprinkler_name,
    'gallonspermin': gallonspermin
  }
  return requests.put(base_url + 'sprinklerbuilder/' + str(get_sprinkler_id(base_url)), new_sprinkler_data)

def update_sprinkler(base_url, sprinkler_id, sprinkler_name, gallonspermin):
  updated_sprinkler_data = {
    'sprinklername': sprinkler_name,
    'gallonspermin': gallonspermin
  }
  return requests.patch(base_url + 'sprinklerbuilder/' + str(sprinkler_id), updated_sprinkler_data)

def delete_sprinkler(base_url, sprinkler_id):
  return requests.delete(base_url + 'sprinklerbuilder/' + str(sprinkler_id))

def get_all_schedules(base_url):
  return requests.get(base_url + 'schedulegetall')

def get_schedule_id(base_url):
  response = requests.get(base_url + 'schedulegetid')
  return response.json()

def get_schedule(base_url, schedule_id):
  return requests.get(base_url + 'schedulebuilder/' + str(schedule_id))

def add_schedule(base_url, sprinkler_id, dow, start_time, runtime):
  if type(dow) is list:
    for day in dow:
      add_schedule(base_url, sprinkler_id, day, start_time, runtime)
  else:
    add_schedule_data = {
      'sprinklerid': sprinkler_id,
      'dow': dow,
      'starttime': start_time,
      'runtime': runtime,
    }
    return requests.put(base_url + 'schedulebuilder/' + str(get_schedule_id(base_url)), add_schedule_data)

def update_schedule(base_url, schedule_id, dow, start_time, runtime):
  if type(dow) is list:
    for day in dow:
      update_schedule(base_url, schedule_id, day, start_time, runtime)
  else:
    updated_schedule_data = {
      'dow': dow,
      'starttime': start_time,
      'runtime': runtime,
    }
    return requests.patch(base_url + 'schedulebuilder/' + str(schedule_id), updated_schedule_data)

def delete_schedule(base_url, schedule_id):
  return requests.delete(base_url + 'schedulebuilder/' + str(schedule_id))

def get_rain_delay(base_url):
  return requests.get(base_url + 'raindelay')

def patch_rain_delay(base_url):
  return requests.patch(base_url + 'raindelay')

def delete_rain_delay(base_url):
  return requests.delete(base_url + 'raindelay')

def run_adhoc(base_url, sprinkler_id, runtime):
  run_sprinkler_data = {
    'runtime': runtime
  }
  return requests.put(base_url + 'runadhoc/' + str(sprinkler_id), run_sprinkler_data)

def run_schedule(base_url, schedule_ids):
  run_schedule_data = {
    'scheduleids': schedule_ids
  }
  return requests.put(base_url + 'runschedule', run_schedule_data)

def stop_running(base_url):
  return requests.delete(base_url + 'stoprunning')

def reset_all_data(base_url):
  return requests.delete(base_url + 'resetall')

def unit_testing(base_url, mode, file_name):
  unit_testing_data = {
    'filename': file_name
  }
  return requests.put(base_url + 'unittesting/' + str(mode), unit_testing_data)

# Schedule Functions
def import_schedule(schedule_file, time_format):
  schedule_json_data = dutils.load_json_file(schedule_file)
  if schedule_json_data is None:
    schedule_json_data = reset_schedule(time_format)
  return schedule_json_data

def reset_schedule(time_format):
  json_data = {
                "created": datetime.now().strftime(time_format),
                "edited": datetime.now().strftime(time_format),
                "raindelay":{
                  "startdate": None,
                  "enddate": None
                },
                "sprinklers":{},
                "schedules_edited": datetime.now().strftime(time_format),
                "schedules":{}
              }
  return json_data

def write_schedule(json_data, schedule_file, time_format):
  json_data['edited'] = datetime.now().strftime(time_format)
  f = open(schedule_file,"w")
  f.write(json.dumps(json_data, indent=2))
  f.close()
