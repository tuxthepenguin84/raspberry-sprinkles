#!/bin/bash
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

CSI="$(printf '\033')["
red_text="${CSI}91m"
green_text="${CSI}92m"
yellow_text="${CSI}93m"
blue_text="${CSI}94m"
magenta_text="${CSI}95m"
cyan_text="${CSI}96m"
reset_text="${CSI}0m"
clear_line="${CSI}0K"

up="[${green_text}✓${reset_text}] Up"
healthy="[${green_text}✓${reset_text}] Healthy"
down="[${red_text}✗${reset_text}] Down"
unhealthy="[${green_text}✓${reset_text}] Unhealthy"
off="[${green_text}✓${reset_text}] Off"
none="[${green_text}✓${reset_text}] None"
running="[${green_text}✓${reset_text}] Running"
unknown="[${yellow_text}?${reset_text}] Unknown"

# Status
docker_ver=$(docker --version | awk '{print $3}' | sed 's/,//g')
docker_ver_green="${green_text}v${docker_ver}${reset_text}"
compose_ver=$(docker compose version | awk '{print $NF}' | sed 's/v//g')
compose_ver_green="${green_text}v${compose_ver}${reset_text}"

if docker inspect --format '{{.State.Running}}' sprinklesapi 2>/dev/null | grep -q "true"; then
  api_status="${up}"
  if docker inspect --format '{{.State.Health.Status}}' sprinklesapi 2>/dev/null | grep -q "healthy"; then
    api_health="${healthy}"
    api_raindelay=$(curl -s /raindelay | jq .endate)
    if echo "${api_raindelay}" | grep -q "null"; then
      rain_delay="${none}"
    else
      rain_delay=$(echo "${api_raindelay}")
    fi
    api_sprinklerstatus=$(curl -s /status)
    if echo "${api_sprinklerstatus}" | grep -q "stopped"; then
      sprinklers="${off}"
    elif "${api_sprinklerstatus}" | grep -q "running"; then
      sprinklers="${running}"
    else
      sprinklers="${unknown}"
    fi
    next_run=$(curl -s /nextrun | xargs)
  else
    api_health="${unhealthy}"
    sprinklers="${unknown}"
    rain_delay="${unknown}"
    next_run="${unknown}"
  fi
else
  api_status="${down}"
  api_health=""
  sprinklers="${unknown}"
  rain_delay="${unknown}"
  next_run="${unknown}"
fi

if docker inspect --format '{{.State.Running}}' sprinklesscheduler 2>/dev/null | grep -q "true"; then
  scheduler_status="${up}"
  if docker inspect --format '{{.State.Health.Status}}' sprinklesscheduler 2>/dev/null | grep -q "healthy"; then
    scheduler_health="${healthy}"
  else
    scheduler_health="${unhealthy}"
  fi
else
  scheduler_status="${down}"
  scheduler_health=""
fi

# System
if [ -f "/sys/firmware/devicetree/base/model" ]; then
  device=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
else
  device=$(cat /sys/devices/virtual/dmi/id/product_family)
fi
default_interface=$(ip route | grep default | awk '{print $5}')
ip_address=$(ip addr show dev "$default_interface" | grep -oP 'inet \K[\d.]+')
uptime=$(uptime -p | cut -d\  -f2-)
core_count=$(nproc --all 2> /dev/null)
cpu_load_1=$(awk '{print $1}' < /proc/loadavg)
cpu_load_1_green="${green_text}${cpu_load_1}${reset_text}"
cpu_load_5=$(awk '{print $2}' < /proc/loadavg)
cpu_load_5_green="${green_text}${cpu_load_5}${reset_text}"
cpu_load_15=$(awk '{print $3}' < /proc/loadavg)
cpu_load_15_green="${green_text}${cpu_load_15}${reset_text}"
cpu=$(cat /sys/class/thermal/thermal_zone0/temp)
temperature="$(printf %.1f "$(echo "${cpu}" | awk '{print $1 / 1000}')")°C"
temperature_cyan="${cyan_text}${temperature}${reset_text}"
memory_percent=$(awk '/MemTotal:/{total=$2} /MemFree:/{free=$2} /Buffers:/{buffers=$2} /^Cached:/{cached=$2} END {printf "%.1f", (total-free-buffers-cached)*100/total}' '/proc/meminfo')
memory_percent_green="${green_text}${memory_percent}${reset_text}%"

printf '\e[H\e[2J\e[3J'
echo "   _______  ___  _____  ____ ____   ________"
echo "  / __/ _ \/ _ \/  _/ |/ / //_/ /  / __/ __/"
echo " _\ \/ ___/ , _// //    / ,< / /__/ _/_\ \  "
echo "/___/_/  /_/|_/___/_/|_/_/|_/____/___/___/  "
echo ""
echo "STATUS ===================================================="
echo " Docker:     ${docker_ver_green} | Compose: ${compose_ver_green}"
echo " API:        ${api_status} ${api_health}"
echo " Scheduler:  ${scheduler_status} ${scheduler_health}"
echo " Sprinklers: ${sprinklers}"
echo " Rain Delay: ${rain_delay}"
echo " Next Run:   ${next_run}"
echo ""
echo "SYSTEM ===================================================="
echo " Device:   ${device}"
echo " Hostname: $(hostname) IP: ${ip_address}"
echo " Uptime:   ${uptime}"
echo " CPU Temp: ${temperature_cyan} CPU Load: ${cpu_load_1_green}, ${cpu_load_5_green}, ${cpu_load_15_green}"
echo " Mem Used: ${memory_percent_green}"
echo ""