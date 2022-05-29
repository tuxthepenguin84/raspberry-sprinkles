import argparse
from datetime import datetime
import logging
import RPi.GPIO as GPIO
import time

# CLI Arguments
parser = argparse.ArgumentParser(description="PiWater Manual Run")
parser.add_argument("-z", "--zone", help="Zone to water | front-bed, front-lawn, side-fence, back-fence, back-garden", required=True)
parser.add_argument("-t", "--time", help="Length of time to water in minutes", type=int, required=True)
args = parser.parse_args()

# Logging Config
logging.basicConfig(format='%(message)s', filename='/var/log/piwater/piwater.log', encoding='utf-8', level=logging.INFO)

# Sprinkler Name
sprinklerNameDict = {'front-bed': 'Front Bed  ',    # Grey Green
                    'front-lawn': 'Front Lawn ',    # Grey Red
                    'side-fence': 'Side Fence ',    # Grey Blue
                    'back-fence': 'Back Fence ',    # Brown Red
                    'back-garden': 'Back Garden'}   # Brown Blue

# GPIO
sprinklerGPIO    = {'front-bed': 5,       # Front Bed
                    'front-lawn': 6,      # Front Lawn
                    'side-fence': 13,     # Side Fence
                    'back-fence': 16,     # Back Fence
                    'back-garden': 19}    # Back Garden

# strftime


# Begin
stringTime = "%a %m/%d %H:%M"
logging.info ('')
logging.info ('%s | WATERING MANUAL RUN STARTED', datetime.now().strftime(stringTime))

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

# Sprinkler Function
def startSprinkler (gpioPIN, runtime, location):
    logging.info ('%s | START | %s | %s minutes', datetime.now().strftime(stringTime), location, runtime)
    GPIO.output(gpioPIN, True)
    time.sleep(runtime*60)
    logging.info ('%s | STOP  | %s | %s minutes', datetime.now().strftime(stringTime), location, runtime)
    GPIO.output(gpioPIN, False)

try:
    startSprinkler(sprinklerGPIO[args.zone], args.time, sprinklerNameDict[args.zone])

except KeyboardInterrupt:
    GPIO.cleanup()

finally:
    GPIO.cleanup()

logging.info ('%s | WATERING MANUAL RUN COMPLETED', datetime.now().strftime(stringTime))