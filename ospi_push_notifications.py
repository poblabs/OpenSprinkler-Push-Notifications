#!/usr/bin/python

""" This script will check the OpenSprinkler API every 5 seconds and look for running stations.
    If a station is found running, it'll send a push notification through Instapush. It will only
	send a push notification once per zone, and only at start-up of the zone.
	
	If the script crashes, it can send an email to let you know it's crashed. 
	
	6/26/2015, Pat O'Brien. Licensed under the MIT License.
	6/30/2015, added Pushover as a push notification service.
	
	"""

import urllib2, json, requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

# Configure these variables.

# You can use this site to convert your plaintext password to hash: http://www.miraclesalad.com/webtools/md5.php
# For example, "hello" converts to 5d41402abc4b2a76b9719d911017c592. You would enter 5d41402abc4b2a76b9719d911017c592 below
ospiApiPasswordHash = "YOUR_OSPi_PASSWORD_IN_HASH" 

# Select your push notification service. Options are "pushover" or "instapush"
pushService = "instapush"

# Instapush settings
instapushAppID = "INSTAPUSH_APP_ID"
instapushAppSecret = "INSTAPUSH_APP_SECRET"

# Pushover settings
pushoverUserKey = "PUSHOVER_USER_KEY"
pushoverAppToken = "PUSH_OVER_APP_TOKEN"

# Email setup. This is used if the script crashes.
fromEmail = "YOUR@FROM_EMAIL"
toEmail = ['YOUR@TO_EMAIL']
smtpServer = "localhost"
subject = "OSPi Push Notification Script Failure"
text = "The OSPi push notification script has crashed, or stopped. You should investigate this and restart it.\n\nssh to your OSPi and check /home/pi/ospi_push_notifications.py"


#########################################################
#
# Don't need to edit anything below, unless you want to. 
#
#########################################################
notifyZone = 0
notifySent = "n"

def sendEmail():
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = fromEmail
	msg['To'] = ", ".join(toEmail)
	part1 = MIMEText(text, 'plain')
	msg.attach(part1)
	s = smtplib.SMTP(smtpServer)
	s.sendmail(fromEmail, toEmail, msg.as_string())
	s.quit()

def getStatus():
	try:
		ospiStationStatus = urllib2.urlopen("http://localhost:8080/js?pw=" + ospiApiPasswordHash).read()
	except:
		sendEmail()
	
	try:
		data = json.loads(ospiStationStatus)
	except:
		sendEmail()
		
	stations = data["sn"]
	#print "Getting sprinkler status. Zones defined: %s. Zone data: %s" % (data["nstations"],data["sn"])
	return stations

def sendPushNotification(zoneID):
	#Send push notifications
	event = "Zone %s is now active" % zoneID
	
	if (pushService == "instapush"):
		headers = {'Content-Type': 'application/json',
						'x-instapush-appid': instapushAppID,
						'x-instapush-appsecret': instapushAppSecret}
		payload = '{"event":"message","trackers":{"message":"' + event + '"}}'
					   
		ret = requests.post('http://api.instapush.im/post',
						headers = headers,
						data = payload)
		#print ret
	
	elif (pushService == "pushover"):
		payload = {
                "token": pushoverAppToken,
                "user" : pushoverUserKey,
                "message": event }
		ret = requests.post("http://api.pushover.net/1/messages.json", data = payload)
		
		#print ret
	

# Main loop to check the station status and send notification if necessary
while True:
	
	# Get the station status from the controller API
	stations = getStatus()
	
	i = 1
	for zoneStatus in stations:
		if (zoneStatus == 1):
			#print "Zone %s is active" % i
			if ( (notifyZone == i) & (notifySent == "y") ):
				#print "Push notification already sent"
				tempVar = "blah"
			else:
				sendPushNotification(i)
				notifyZone = i
				notifySent = "y"
				#print "Sending push notification to %s" % pushService
				
		#else:
		#	print "No zones running."

		i = i + 1
	
	#print ""
	sleep(5)

