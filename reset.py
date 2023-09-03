# Modules
import argparse

# Custom Modules
from rsclient import resetAllData

def main():
  argParser = argparse.ArgumentParser(description="Raspberry Sprinkles Reset")
  argParser.add_argument("-u", "--url", help="base url", default='http://127.0.0.1:5000/')
  parsedArgs = argParser.parse_args()
  response = resetAllData(parsedArgs.url)
  print(response)

if __name__ == '__main__':
  main()