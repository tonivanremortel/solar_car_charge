#!/usr/bin/env python3
from wallbox import Wallbox
import mysql.connector
import logging
import math
import configparser
import requests
import time

settings_ini = "/usr/share/solar_car_charge/settings.ini"

config = configparser.ConfigParser()
config.sections()
config.read(settings_ini)

# Wallbox info
w = Wallbox(config['wallbox']['user'], config['wallbox']['pass'])
chargerId = config['wallbox']['chargerid']

# MySQL info
db_user = config['mysql']['user']
db_pass = config['mysql']['pass']
db_host = config['mysql']['host']
db_db   = config['mysql']['database']

# EmonCMS
emon_host = config['emoncms']['host']
emon_node = config['emoncms']['node']
emon_api  = config['emoncms']['apikey']

# Logging
logging.basicConfig(filename='/var/log/wallbox.log', level=logging.INFO, format='%(asctime)s %(message)s')

# DB connection
mydb = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_db)
mycursor = mydb.cursor()

# Fetch settings from DB
mycursor.execute("SELECT topic,value FROM settings")
myresult = mycursor.fetchall()
settings = {}
for row in myresult:
    settings[row[0]] = row[1]

# Do not start when we are inactive
if ( settings["active"] == '0' ):
    logging.info('-- Status set to inactive')
    exit()

# Settings
minimal_kwh_to_start_charging = int(settings["minimal_kwh_to_start_charging"])*-1

def define_amp(power):
    abs_power = abs(power)
    if( abs_power < minimal_kwh_to_start_charging ):
        return 6
    else:
        new_amp = math.floor(abs_power/690)
        if ( new_amp < 6 ):
            return 6
        elif ( new_amp >= 16 ):
            return 16
        else:
            return new_amp

def send_emoncms(new_power,status,old_power,p1):
    emon_url = 'http://' + emon_host + '/emoncms/input/post.json?node=' + emon_node + '&fulljson={"wallbox_amp":' + str(new_power) + ',"wallbox_state":' + str(status) + ',"wallbox_old_amp":' + str(old_power) + ',"virtual_p1":' + str(p1) + '}&apikey=' + emon_api
    e = requests.get(emon_url)

# Sleep 10 seconds so we have the data from P1 which is read at the same time
time.sleep(10)

# Get the state of the charger
# Authenticate with the credentials above
w.authenticate()
chargerStatus = w.getChargerStatus(chargerId)

#print(chargerStatus)

# Read the available power from the database
# We calculate the past power availability by a difference in the export and import of the past 2 minutes
# To keep the SQL simple, we just fetch the data and calculate in code
mycursor.execute("SELECT `export`,`import` FROM meter WHERE `datetime` BETWEEN (DATE_SUB(NOW(), INTERVAL 3 MINUTE)) AND NOW()")
records = mycursor.fetchall()
p1_export = []
p1_import = []
for record in records:
    p1_export.append(record[0])
    p1_import.append(record[1])

# Diff between first & last
# As the kWh meter position is read out once per minute, we need to multiply by 60 to have the acurate current power.
# We check the diff between now and 2 minutes, so we also divide by 2
p1_export_diff = (p1_export[2] - p1_export[0]) / 2 * 60
p1_import_diff = (p1_import[2] - p1_import[0]) / 2 * 60

# Available power is thus p1_import_diff - p1_export_diff
# Negative value means we have excess power, positive value means we are getting power from the net
p1 = p1_import_diff - p1_export_diff

# Start of logic
# remote_action = 0 --> no car connected, not charging
# remote_action = 1 --> charging running
# remote_action = 2 --> charging paused
wallbox_current_amp = chargerStatus['config_data']['max_charging_current']
wallbox_desc = chargerStatus['status_description']
#wallbox_state = chargerStatus['config_data']['remote_action']
if(wallbox_desc == 'Ready'):
    # No car connected
    wallbox_state = 0
elif(wallbox_desc == 'Paused by user'):
    # Paused by us
    wallbox_state = 0
elif(wallbox_desc == 'Connected: waiting for car demand'):
    # Car full
    wallbox_state = 2
elif(wallbox_desc == 'Charging'):
    # Charging
    wallbox_state = 1
else:
    wallbox_state = 0

logging.info('-- Wallbox[%s]: %s A - P1: %s W - Minimal: %s W - %s', wallbox_state, wallbox_current_amp, p1, minimal_kwh_to_start_charging, wallbox_desc) 

# If we are not charging, we only look at P1
if(wallbox_state == 0):
    virtual_p1 = p1
    if( virtual_p1 < minimal_kwh_to_start_charging ):
        wallbox_new_amp = define_amp(virtual_p1)
        send_emoncms(wallbox_new_amp, 1, wallbox_current_amp, virtual_p1)
        try:
            w.setMaxChargingCurrent(chargerId,wallbox_new_amp)
            w.resumeChargingSession(chargerId)
            logging.info('Sufficient power: %s W. Start charging at %s A', virtual_p1, wallbox_new_amp)
        except:
            logging.info('Sufficient power: %s W. Start charging at %s A', virtual_p1, wallbox_new_amp)
    else:
        wallbox_new_amp = 6
        send_emoncms(wallbox_new_amp, 0, wallbox_current_amp, virtual_p1)
        try:
            w.setMaxChargingCurrent(chargerId,wallbox_new_amp)
            w.pauseChargingSession(chargerId)
            logging.info('Pause charging, not enough power: %s W - %s A', virtual_p1, wallbox_new_amp)
        except:
            logging.info('Pause charging, not enough power: %s W - %s A', virtual_p1, wallbox_new_amp)
elif(wallbox_state == 2):
    # Car is full, so pause and set to minimum amps
    virtual_p1 = p1
    wallbox_new_amp = 6
    send_emoncms(wallbox_new_amp, 0, wallbox_current_amp, virtual_p1)
    try:
        w.setMaxChargingCurrent(chargerId,wallbox_new_amp)
        w.pauseChargingSession(chargerId)
        logging.info('Pause charging, car is full: %s W - %s A', virtual_p1, wallbox_new_amp)
    except:
        logging.info('Pause charging, car is full: %s W - %s A', virtual_p1, wallbox_new_amp)
# Else we are charging, so we use P1 and distract the current charging power to get a virtual P1
# Issue: when the Wallbox is reporting it is charging, but it is not, this logic creates a jojo effect
# So ... how to know the real charging speed?
else:
    virtual_p1 = p1 - wallbox_current_amp*690
    if( virtual_p1 < minimal_kwh_to_start_charging ):
        wallbox_new_amp = define_amp(virtual_p1)
        send_emoncms(wallbox_new_amp, 1, wallbox_current_amp, virtual_p1)
        try:
            w.setMaxChargingCurrent(chargerId,wallbox_new_amp)
            logging.info('More power: %s W. Update charging to %s A', virtual_p1, wallbox_new_amp)
        except:
            logging.info('More power: %s W. Update charging to %s A', virtual_p1, wallbox_new_amp)
    else:
        wallbox_new_amp = 6
        send_emoncms(wallbox_new_amp, 0, wallbox_current_amp, virtual_p1)
        try:
            w.setMaxChargingCurrent(chargerId,wallbox_new_amp)
            w.pauseChargingSession(chargerId)
            logging.info('Pause charging, not enough power: %s W - %s A', virtual_p1, wallbox_new_amp)
        except:
            logging.info('Pause charging, not enough power: %s W - %s A', virtual_p1, wallbox_new_amp)

