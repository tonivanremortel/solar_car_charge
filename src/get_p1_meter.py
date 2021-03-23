#!/usr/bin/env python3
import requests
import json
import mysql.connector
import configparser

settings_ini = "/usr/share/solar_car_charge/settings.ini"

config = configparser.ConfigParser()
config.sections()
config.read(settings_ini)

# Our database
db_user = config['mysql']['user']
db_pass = config['mysql']['pass']
db_host = config['mysql']['host']
db_db   = config['mysql']['database']

# Connect to the database
mydb = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_db)
mycursor = mydb.cursor()

# EmonCMS
emon_host = config['emoncms']['host']
emon_node = config['emoncms']['node']
emon_api  = config['emoncms']['apikey']

# Fetch the P1 meter data
p1_url = 'http://' + config['homewizard_p1']['ip'] + '/api/v1/data'
r = requests.get(p1_url)
if ( r.status_code == 200 ):
    # Request OK, add data to DB
    data = json.loads(r.text)
    # Get the current power. Would be better to read out export power and compare to previous readout
    power = data["active_power_w"]
    p1_export = (data["total_power_export_t1_kwh"] + data["total_power_export_t2_kwh"]) * 1000
    p1_import = (data["total_power_import_t1_kwh"] + data["total_power_import_t2_kwh"]) * 1000

    sql = "INSERT INTO meter (`datetime`,`power`,`export`,`import`) VALUES (NOW(), {}, {}, {})".format(power,p1_export,p1_import)
else:
    # Request NOK, set data to 0
    sql = "INSERT INTO meter (`datetime`,`power`) VALUES (NOW(),0)"

mycursor.execute(sql)
mydb.commit()
