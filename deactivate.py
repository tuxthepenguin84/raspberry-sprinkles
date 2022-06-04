from datetime import datetime
import logging
import os
import RPi.GPIO as GPIO
import time

logging.basicConfig(format='%(message)s', filename='/var/log/piwater/piwater.log', encoding='utf-8', level=logging.INFO)

# Variables

# GPIO
sprinklerGPIO    = {'front-bed': 5,       # Front Bed
                    'front-lawn': 6,      # Front Lawn
                    'side-fence': 13,     # Side Fence
                    'back-fence': 16,     # Back Fence
                    'back-garden': 19}    # Back Garden

# strftime
stringTime = "%a %m/%d %H:%M"

# Begin
logging.info ('%s | INTERRUPTING', datetime.now().strftime(stringTime))

# Always delay for a few seconds to reduce flapping
time.sleep(1)

# Set GPIO Mode
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Set GPIO as Output & False/Off
for gpioPIN in sprinklerGPIO.values():
    GPIO.setup(gpioPIN, GPIO.OUT)
    GPIO.output(gpioPIN, False)

# GPIO Cleanup
GPIO.cleanup()

# Kill python processes
os.system("/usr/bin/killall python")