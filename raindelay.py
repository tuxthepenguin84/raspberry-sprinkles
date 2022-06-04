from datetime import datetime
import logging

logging.basicConfig(format='%(message)s', filename='/var/log/piwater/piwater.log', encoding='utf-8', level=logging.INFO)

try:
    f = open("/home/pi/scripts/raindelay", "x")
    f.close()
    f = open("/home/pi/scripts/raindelay", "w")
    f.write("1")
    currentDelay = 1
    f.close()
except FileExistsError:
    try:
        f = open("/home/pi/scripts/raindelay", "r")
        currentDelay = int(f.read())
        f.close()
        if isinstance(currentDelay, int):
            currentDelay = currentDelay + 1
            f = open("/home/pi/scripts/raindelay", "w")
            f.write(str(currentDelay))
            f.close()
        else:
            f = open("/home/pi/scripts/raindelay", "w")
            f.write("1")
            f.close()
    except:
        f = open("/home/pi/scripts/raindelay", "w")
        f.write("1")
        currentDelay = 1
        f.close()

stringTime = "%a %m/%d %H:%M"
logging.info ('')
logging.info ('%s | RAIN DELAY REQUESTED for %s day(s)', datetime.now().strftime(stringTime), currentDelay)