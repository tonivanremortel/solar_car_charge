# Solar Car Charge
An attempt to charge a BEV with solar energy only via the P1 port readout over the network and the Wallbox API.

## Background
In the past Belgium had a reverse turning power meter for every home with solar panels.
So a logic setup was to install sufficient solar panels which cover the BEV consumption and charge your car every night.
Installing a simple car charger was a good idea ...

However that reverse turning meter is gone, so now when you generate electricity during the day and consume it during the night, you almost pay double (once to send the electricity on the net, and once to get it back).

Today I have a digital power meter with an open P1 port and a Wallbox Pulsar Plus to charge the car.
As there is no option (yet) to charge the car with the excess solar energy only, I created these scripts to automate it a bit.

## How it works
* One script reads out the P1 data via the network and dumps the info in a database.
* Another script reads out the database and defines if and with what power the Wallbox should charge the car.
* A simple mobile WebUI to enable or disable the system so you can charge whenever you like :-)

## How it works at my place
* I installed the HomeWizard P1 meter as our digital power meter is +/- 30m away from the house. This P1 meter has a simple API which returns the data as JSON. The script get_p1_meter.py fetches this JSON and dumps the meter position into the MySQL database.
* The script set_wallbox.py uses the Wallbox API Python module to talk to the Wallbox. It reads the database and checks the average excess power of the past 2 minutes to define if and how fast the Wallbox must charge.

## Prerequisites
* A Linux system which can run 24/7, preferrably Ubuntu 20.04
* A running MySQL
  * apt install mysql-server
* Apache2 with PHP
  * apt install apache2 libapache2-mod-php
* Python modules
  * pip install wallbox
* APT packages
  * apt install mysql-connector-python
* HomeWizard P1 meter: https://www.homewizard.nl/homewizard-wi-fi-p1-meter
* An open P1 port on your digital meter
* Wallbox Pulsar Plus (or another Wallbox, but I haven't tested those) connected to your network
* Guts, balls, patience and probably also an electric car ;-)

## Installation
1. Get this code
1. Create a MySQL database called 'solar_car_charge'
1. Create a user that can use that database (don't use root please)
1. Import the solar_car_charge.sql file to set up the database structure
1. Install the prerequisites for Python and APT
1. Copy the scripts from the 'src' directory to /usr/share/solar_car_change
1. Copy the index.php from the 'www' directory to /var/www/html
1. Edit /usr/share/solar_car_charge/settings.ini and fill in all the info needed
1. Edit /var/www/html/index.php and change the database info on the first lines (probably only the user & password)
1. Test out all scripts. Both should not return any info on the CLI. If they do: fix the errors :-)
   1. /usr/share/solar_car_change/get_p1_meter.py
   1. /usr/share/solar_car_change/set_wallbox.py 
1. Check the logfile /var/log/wallbox.log for any charging state change.

## Sample log file info
> 2021-03-23 16:29:02,974 -- Wallbox: 6 A - P1: -4200.0 W - Minimal: -3450 W
> 2021-03-23 16:29:03,320 Sufficient power: -4200.0 W. Start charging at 6 A
> 2021-03-23 16:30:03,279 -- Wallbox: 6 A - P1: -4170.0 W - Minimal: -3450 W
> 2021-03-23 16:30:03,642 Sufficient power: -4170.0 W. Start charging at 6 A
> 2021-03-23 16:31:03,486 -- Wallbox: 6 A - P1: -2070.0 W - Minimal: -3450 W
> 2021-03-23 16:31:03,854 Pause charging, not enough power: -2070.0 W - 6 A

