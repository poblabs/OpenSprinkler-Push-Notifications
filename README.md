OpenSprinkler Push Notifications
=============

(c) drsprite <drsprite@github.com> - http://github.com/drsprite
Please read LICENSE for licensing info

This is a Python script that will check the <a href="http://opensprinkler.com" target="_blank">OpenSprinkler</a> API
for running sprinkler zones (or stations). If a station is running, it
will send you a push notification. It also will check to see if the rain
sensor has been activated and send a notification for that event as well. 

<img src="http://i.imgur.com/SABNQpOl.png">

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
2. Create a new app called `OpenSprinkler` (or whatever you'd like it to be called)
3. Install the app on your device to receive push notifications. 

### Support for IFTTT Maker channel:
1. Create your maker channel and get your secret key. https://ifttt.com/maker
2. Add the secret key, and your event name to the `config.yaml`. I chose my event name to be `OpenSprinkler`
3. Create a new recipe with the following info (you can tailor it to suite your needs, but for simple push notifications):
  1. Trigger channel: Maker
    1. Receive a web request
	2. Event name: OpenSprinkler
  2. That: 
    1. This is where you can say "iOS Notification" or "Android Notification" or "Email" or "SMS". Whatever you'd like to do.
  3. Complete the action field and create the recipe. 
    1. For the Notification field, I simply chose `{{EventName}}: {{Value1}}`.
	2. An example that this would display: `OpenSprinkler: Zone 1 is now active.`
	

## Script configuration:
1. First, make sure you have the required Python libraries. 
  1. Requests: `sudo easy_install requests`
  2. PyYAML: `sudo easy_install pyyaml`
2. Copy the `ospi_push_notifications.py` and `config.yaml` files to `/home/pi`
3. `chmod 755 /home/pi/ospi_push_notifications.py`
4. Edit config.yaml and update the items located within.
  1. Special Note: Your OSPi API password needs to be MD5 hashed. You can create this on the command line. SSH and log into the Pi. Then run:
    1. `echo -n hello | md5sum`.
    2. For example, "hello" is your OpenSprinkler password and it converts to 5d41402abc4b2a76b9719d911017c592. You would enter `"5d41402abc4b2a76b9719d911017c592"` into the `config.yaml`
  2. Also, if the config file has `{}` for a notification message, this is what will be used for the dynamic value for that notification. 
    1. For example, `start: "Zone {} is now active"`, will send the notification `"Zone 1 is now active"`. 
	2. You must keep the `{}` present in that notification message for the dynamic info to be sent through notification. 
5. You can run `sudo python /home/pi/ospi_push_notifications.py` and manually start a station from OpenSprinkler's web page to see if you get a push notification. 
6. Stop running the script by pressing `CTRL+C` if you receive a notification, and continue to install it as a service so it'll run on reboots.
7. Copy the service script `ospi-notifications` to `/etc/init.d`
8. `sudo chmod +x /etc/init.d/ospi-notifications`
9. To start the script on startups and reboots, run `sudo update-rc.d ospi-notifications defaults`
10. To manually start the service, `sudo service ospi-notifications start`
  1. Other commands you can run are `sudo service ospi-notifications stop | restart | status`
11. Now that the script is running as a background service, run a zone manually from your phone or the OpenSprinkler web page to see if you get a push notification. 
	
# DEBUG INFO

First, make sure you have the required Python libraries. See Script Configuration above. 

Then, if for some reason things aren't working, you can check your syslog. Typically this is at `/var/log/messages`. 
Depending on where the script failed, this should provide some information. Lastly, you can check the init.d log
for the notifications script located at `/var/log/ospi-notifications`. 

Otherwise check the permissions on the `/etc/init.d/ospi-notifications` script as well as the `/home/pi/ospi_push_notifications.py` script. 

