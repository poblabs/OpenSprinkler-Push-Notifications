OpenSprinkler Push Notifications
=============

(c) drsprite <drsprite@github.com> - http://github.com/drsprite
Please read LICENSE for licensing info

This is a simple Python script that will check the OpenSprinkler API
for running sprinkler zones (or stations). If a station is running, it
will use the Instapush service to send a push notification to your
device. 

<img src="http://i.imgur.com/ho8C1qtl.png">

# INSTALLATION

### Support for Instapush:
1. Sign up for Instapush at www.instapush.im
2. Create a new App on Instapush's website with these settings:
  1. Title: `message`
  2. Tracker: `message`
  3. Push message: `{message}`
3. Click Basic Info on your newly created app and save the Application ID and the Application Secret.
4. Install the Instapush app on your device. The app is basic and is only needed to receive the push notification. 

### Support for Pushover:
1. Sign up for Pushover at http://pushover.net
2. Create a new app called OpenSprinkler
3. Install the app on your device to receive push notifications. 

### Script configuration:
1. Copy the ospi_push_notifications.py file to /home/pi
2. `chmod 755 /home/pi/ospi_push_notifications.py`
3. Edit ospi_push_notifications.py and update these items:
  1. Your push notification service. Options are "instapush" or "pushover"
  2. Your push service App ID or token
  3. Your push service App Secret or user token
  4. Your From Email
  5. Your To Email
  6. Your OpenSprinkler API password in hashed format. For example, if your password is "hello", the hash is 5d41402abc4b2a76b9719d911017c592
4. You can run `sudo python /home/pi/ospi_push_notifications.py` and manually start a station to see if you get a push notification. 
5. Stop running the script if you're happy, and install it as a service.
6. Copy the service script ospi-notifications to /etc/init.d
7. `sudo chmod +x /etc/init.d/ospi-notifications`
8. To start the script on startups and reboots, run `sudo update-rc.d ospi_notifications defaults`
9. To start the service, `sudo service ospi-notifications start`
10. Run a zone manually to see if you get a push notification. 
	
# DEBUG INFO

First, you will need the Python requests library. Install it via `sudo easy_install requests`

Then, if for some reason things aren't working, you can check the init.d script's log file,
located at /var/log/ospi-notifications. This could give you some insight on what's wrong. 
Otherwise check the permissions on the /etc/init.d/ospi-notifications script as well as
the /home/pi/ospi_push_notifications.py script. 

