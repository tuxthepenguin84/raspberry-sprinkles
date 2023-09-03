# Modules
import argparse

# Custom Modules
from rsclient import runAdhoc

def main():
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Run AdHoc Sprinkler")
  argParser.add_argument("-r", "--runtime", help="run time in minutes", type=int, nargs=1, required=True)
  argParser.add_argument("-s", "--sprinklerid", help="sprinklerid", type=int, nargs=1, required=True)
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()
  response = runAdhoc(parsedArgs.url, parsedArgs.sprinklerid[0], parsedArgs.runtime[0])
  print(response, response.json())

if __name__ == '__main__':
  main()