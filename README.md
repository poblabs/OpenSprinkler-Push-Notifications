OpenSprinkler Push Notifications
=============

(c) drsprite <drsprite@github.com> - http://github.com/drsprite
Please read LICENSE for licensing info

This is a simple Python script that will check the OpenSprinkler API
for running sprinkler zones (or stations). If a station is running, it
will use the Instapush service to send a push notification to your
device. 

<img src="http://i.imgur.com/ho8C1qtl.png">

### INSTALLATION

1. Sign up for Instapush at www.instapush.im
2. Create a new App on Instapush's website with these settings:
    a. Title: message
	b. Tracker: message
	c. Push message: {message}
3. Click Basic Info on your newly created app and save the Application ID and the Application Secret.
4. Install the Instapush app on your device. The app is basic and is only needed to receive the push notification. 
5. Copy the ospi_push_notifications.py file to /home/pi
6. chmod 755 /home/pi/ospi_push_notifications.py
7. Edit ospi_push_notifications.py and update these items:
   a. Your From Email
   b. Your To Email
   c. Your Instapush App ID 
   d. Your Instapush App Secret
   e. Your OpenSprinkler API password in hashed format. For example, if your password is "hello", the hash is 5d41402abc4b2a76b9719d911017c592
8. You can run "sudo python /home/pi/ospi_push_notifications.py" and manually start a station to see if you get a push notification. 
9. Stop running the script if you're happy, and install it as a "service"
10. Copy the service script ospi-notifications to /etc/init.d
11. sudo chmod +x /etc/init.d/ospi-notifications
12. To start the script on startups and reboots, run sudo update-rc.d ospi_notifications defaults
13. To start the service, sudo service ospi-notifications start
14. Run a zone manually to see if you get a push notification. 
	
### DEBUG INFO

If for some reason things aren't working, you can check the init.d script's log file,
located at /var/log/ospi-notifications. This could give you some insight on what's wrong. 
Otherwise check the permissions on the /etc/init.d/ospi-notifications script as well as
the /home/pi/ospi_push_notifications.py script. 

