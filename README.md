# Raspberry-Sprinkles
Use a Raspberry Pi to control your sprinkler system.

![display](images/display.jpg "display")

# Getting Started
## Hardware

*   Raspberry Pi (3 or 4)
    *   Raspberry Pi OS Lite (64 bit) - No desktop environment
*   Power Relay Hat
    *   [8 Channel](https://www.amazon.com/gp/product/B08PSFK2L2/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1)
    *   [3 Channel](https://www.amazon.com/gp/product/B07CZL2SKN/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1)
*   3.5" Display Hat (Optional)
    *   [Waveshare 3.5inch RPi LCD (C) 320X480 Resolution Touch Screen TFT Display](https://www.amazon.com/gp/product/B07L1215W5/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
    *   [Waveshare Display Drivers](https://github.com/waveshare/LCD-show)
*   Assorted Jumper Wires for GPIO Pins
    *   [Breadboard Jumper Wires](https://www.amazon.com/EDGELEC-Breadboard-Optional-Assorted-Multicolored/dp/B07GD2BWPY/ref=sr_1_1_sspa?crid=3CBEKEEVH8FSE&keywords=jumper%2Bwires&qid=1653831397&s=industrial&sprefix=jumper%2Bwires%2Cindustrial%2C140&sr=1-1-spons&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUExRU9FNjZTWjhJVzlZJmVuY3J5cHRlZElkPUEwNjQ4OTcyM1RLQ05ZRU1DNlRFSyZlbmNyeXB0ZWRBZElkPUEwOTQ1NDM2MUpBN1RMSkJGREFMWiZ3aWRnZXROYW1lPXNwX2F0ZiZhY3Rpb249Y2xpY2tSZWRpcmVjdCZkb05vdExvZ0NsaWNrPXRydWU&th=1)
*   Fuse Holder Inline
    *   [BOJACK 5x20 mm Fuse Holder Inline](https://www.amazon.com/gp/product/B0813Q4S6P/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
    * Check your sprinkle system to see what the max draw is, mine recommended 0.75 Amps
*   Manual On/Off Switch (Override and disable the system)
    *   [Rocker Switch](https://www.amazon.com/COOLOOdirect-Solder-Rocker-Switch-Toggle/dp/B071Y7SMVQ/ref=sr_1_3?crid=3OIHRJPLSXAT4&keywords=electronic+switch&qid=1653831746&sprefix=electronic+switch%2Caps%2C172&sr=8-3)

## Hardware Assembly
I have a RainBird sprinkler system but this should work with any other system. If you want to keep the existing sprinkler system in line for various reasons or if you have an RF remote then you'll need to tap into the various channels and put this in parrallel. Otherwise run your sprinkler power lines into the Raspberry Pi relay. I have mine run in parrallel so I have a line run for each channel on the relay to the channel on the sprinkler system. I have an inline fuse and a manual on/off switch to cut power to the relay to manually control turning the system on or off.

![rainbird](images/rainbird.jpg "rainbird")

## Installation
Assuming the current path is ```/home/pi/git```
1. Python 3 (tested with version 3.10)
1. ```git clone https://github.com/tuxthepenguin84/raspberry-sprinkles.git```
1. ```pip install -r requirements.txt```
1. ```sudo mkdir /var/log/rs && chown -R pi:pi /var/log/rs```

## systemd
If you want to install Raspberry-Sprinkles as a service, copy the systemd service files to ```/lib/systemd/system/``` dir and reload systemd. Enable the service to start on boot.
1. ```sudo cp systemd/*.service /lib/systemd/system/```
1. ```sudo systemctl daemon-reload```
1. ```sudo systemctl enable rsapi rsauto```
1. ```systemctl start rsapi rsauto```

Raspberry-Sprinkles should now be running on http://127.0.0.1:5000/

## logrotate (optional)
Logrotate can handle any logs that need to be rotated.
1. ```sudo cp logrotate/logrotate-raspberry-sprinkles /etc/logrotate.d/raspberry-sprinkles```

## bashrc (optional)
If you want the console output similar to the main picture in this repo you'll need to install ```figlet``` and update your bashrc with the bottom contents of ```bashrc/bashrc-raspberry-sprinkles```

## Files
* reset.py - Deletes all schedules
* rsapi.py - Flask API that runs the backend of Raspberry-Sprinkles (tcp/5000)
* rsclient.py - Client library that makes it easy to interact with the API
* runauto.py - Runs automated schedules
* runschedule.py - Runs adhoc schedules
* runsprinkler.py - Runs adhoc watering/sprinkler requests
* schedule.json - (Not shown) this is a JSON file that contains your sprinklers and schedules
* schedule_builder.py - Builds your schedule.json based on sprinklers and specified schedules
* stop.py - Stops any in progress watering/sprinkler requests
* test_rsapi.py - Unit testing for Raspberry-Sprinkles
* run_unit_testing.sh - Used to call test_rsapi.py for unit testing
* requirements.txt - Python requirements for Raspberry-Sprinkles
* weather_params.json - Used for issuing rain delays automatically based on weather and location information

# Running Raspberry-Sprinkles
## Build A Sprinkler Schedule
Raspberry-Sprinkles can build any type of schedule you require for your sprinkler system and supports different types of schedules depending on the current season.

1. Edit schedule_builder.py and modify "Add Sprinkler" section based on how many sprinklers you have. You will need to add a Name and Gallons Per Min, if you don't know how many gallons per min your sprinklers are fill in any number.
1. Next edit the season section and begin adding entries for each sprinkler run. Days are as follows: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']. If you want the sprinkler to run every day use "Everyday". If you want a sprinkler to run the same schedule no matter what season add it to the ALL SEASONS section.
1. When you are done run the following to build a schedule.json:<br>
```/usr/bin/python3 /home/pi/git/raspberry-sprinkles/schedule_builder.py```
1. The rsapi service will automatically pickup the schedule.json and run at the requested times.
* There is a known bug where if one sprinkler is stopping in the same minute as another sprinkler is starting it will not start the sprinkler. As a result do not have any sprinklers end the same minute another sprinkler is starting.

## Run Sprinkler Schedule
Run schedule ID 1,5,9,13,17<br>
```curl -s -X PUT http://127.0.0.1:5000/runschedule -d scheduleids=1,5,9,13,17```

## Run Sprinkler
Run sprinkler 1 for 10 minutes<br>
```curl -s -X PUT http://127.0.0.1:5000/runadhoc/1 -d runtime=10```

## Stop Sprinklers
```curl -s -X DELETE http://127.0.0.1:5000/stoprunning```

## Rain Delay
Adds a rain delay for 24 hours (Increments by 24 hours on each run)<br>
```curl -s -X PATCH http://127.0.0.1:5000/raindelay```

View current rain delay<br>
```curl -s -X GET http://127.0.0.1:5000/raindelay```

Remove rain delay<br>
```curl -s -X DELETE http://127.0.0.1:5000/raindelay```

## Reset Sprinkler Schedule
```curl -s -X DELETE http://127.0.0.1:5000/resetall```

## Raspberry-Sprinkles Front End (UI)
While there is no official front end for Raspberry-Sprinkles, a basic UI can be constructed from another project call [Olivetin](https://github.com/OliveTin/OliveTin). Olivetin supports mobile browsers and makes a safe and simple web interface which can run predefined shell commands. See ```olivetin/raspberry-sprinkles-config.yaml``` for a sample configuration you can use and adapt into your own Olivetin instance.

![olivetin](images/olivetin.jpg "olivetin")

## HTTPS & Proxy
There is no https support. However, I recommend and use Nginx Proxy Manager which also supports access lists<br>
[nginx-proxy-manager](https://github.com/NginxProxyManager/nginx-proxy-manager)

## Possible Future Functionality

- ✅ | Add API Functionality
- ✅ | Support multiple schedules based on season
- ✅ | Weather integration for automated schedule adjustment - https://open-meteo.com/
- ⬜️ | Add API Key Auth: https://blog.teclado.com/api-key-authentication-with-flask/