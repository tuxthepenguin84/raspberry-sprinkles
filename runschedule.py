# Modules
import argparse

# Custom Modules
from rsclient import runSchedule

def main():
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Run Adhoc Existing Schedule(s)")
  argParser.add_argument("-s", "--schedules", help="schedules to run", type=int, nargs='+', required=True)
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()
  response = runSchedule(parsedArgs.url, parsedArgs.schedules)
  print(response, response.json())

if __name__ == '__main__':
  main()