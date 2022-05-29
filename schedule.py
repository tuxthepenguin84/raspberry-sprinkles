import argparse
from datetime import datetime
import logging
import RPi.GPIO as GPIO
import threading
import time

# Schedule (Day of Week)
# Mon-Tue-Wed-Thu-Fri-Sat-Sun
sprinklerDoWDict = {'front-bed': ['Mon', 'Wed', 'Fri', 'Sun'],
                    'front-lawn': ['Mon', 'Wed', 'Fri', 'Sun'],
                    'side-fence': ['Mon', 'Wed', 'Fri', 'Sun'],
                    'back-fence': ['Mon', 'Wed', 'Fri', 'Sun'],
                    'back-garden': ['Mon', 'Wed', 'Fri', 'Sun']}

# Watering Time (min)
sprinklerMinDict = {'front-bed': 6,
                    'front-lawn': 10,
                    'side-fence': 8,
                    'back-fence': 8,
                    'back-garden': 30}

################################################################

# CLI Arguments
parser = argparse.ArgumentParser(description="PiWater Schedule Run")
parser.add_argument("-f", "--force", help="Force run schedule", default=False, action='store_true')
args = parser.parse_args()

# Logging Config
logging.basicConfig(format='%(message)s', filename='/var/log/piwater/piwater.log', encoding='utf-8', level=logging.INFO)

# Sprinkler Name
sprinklerNameDict = {'front-bed': 'Front Bed  ',    # Grey Green
                    'front-lawn': 'Front Lawn ',    # Grey Red
                    'side-fence': 'Side Fence ',    # Grey Blue
                    'back-fence': 'Back Fence ',    # Brown Red
                    'back-garden': 'Back Garden'}   # Brown Blue

# GPIO BMC Pin
sprinklerGPIO    = {'front-bed': 5,       # Front Bed
                    'front-lawn': 6,      # Front Lawn
                    'side-fence': 13,     # Side Fence
                    'back-fence': 16,     # Back Fence
                    'back-garden': 19}    # Back Garden

# Begin
stringTime = "%a %m/%d %H:%M"
DoW = datetime.now().strftime("%a")

if DoW not in [x for v in sprinklerDoWDict.values() for x in v] and args.force == False:
    exit()

# Begin
logging.info ('')
logging.info ('%s | WATERING SCHEDULE STARTED', datetime.now().strftime(stringTime))

# Always delay for a few seconds to reduce flapping
time.sleep(2)

# Set GPIO Mode
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Set GPIO as Output & False/Off
for gpio in sprinklerGPIO.values():
    GPIO.setup(gpio, GPIO.OUT)
    GPIO.output(gpio, False)

# Always delay for a few seconds to reduce flapping
time.sleep(2)

# Sprinkler Class
class sprinklerThread (threading.Thread):
   def __init__(self, GPIO, runTime, location):
      threading.Thread.__init__(self)
      self.GPIO = GPIO
      self.runTime = runTime
      self.location = location
   def run(self):
      startSprinkler(self.GPIO, self.runTime, self.location)

# Sprinkler Function
def startSprinkler (gpioPIN, runtime, location):
    logging.info ('%s | START | %s | %s minutes', datetime.now().strftime(stringTime), location, runtime)
    GPIO.output(gpioPIN, True)
    time.sleep(runtime*60)
    logging.info ('%s | STOP  | %s | %s minutes', datetime.now().strftime(stringTime), location, runtime)
    GPIO.output(gpioPIN, False)

try:
    # Create new threads
    runningSprinklerThreads = []
    for sprinklerID in sprinklerNameDict.keys():
        if DoW in sprinklerDoWDict[sprinklerID] or args.force == True:
            runningSprinklerThreads.append(sprinklerThread(sprinklerGPIO[sprinklerID], sprinklerMinDict[sprinklerID], sprinklerNameDict[sprinklerID]))
            runningSprinklerThreads[-1].start()
    
    # Wait for all threads to complete
    for runningThreads in runningSprinklerThreads:
        runningThreads.join()

except KeyboardInterrupt:
    GPIO.cleanup()

finally:
    GPIO.cleanup()

logging.info ('%s | WATERING SCHEDULE COMPLETED', datetime.now().strftime(stringTime))