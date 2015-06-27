#!/usr/bin/python

""" This script will check the OpenSprinkler API every 5 seconds and look for running stations.
    If a station is found running, it'll send a push notification through Instapush. It will only
	send a push notification once per zone, and only at start-up of the zone.
	
	If the script crashes, it can send an email to let you know it's crashed. 
	
	6/26/2015, Pat O'Brien. Licensed under the MIT License. 
	
	"""

import urllib2, json, requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

# Configure these variables.
ospiApiPasswordHex = "YOUR_OSPi_PASSWORD_IN_HEX"
instapushAppID = "YOUR_INSTAPUSH_APP_ID"
instapushAppSecret = "YOUR_INSTAPUSH_APP_SECRET"

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
		ospiStationStatus = urllib2.urlopen("http://localhost:8080/js?pw=" + ospiApiPasswordHex).read()
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
	#Send push notification to Instapush
	event = "Zone %s is now active" % zoneID
	headers = {'Content-Type': 'application/json',
					'x-instapush-appid': instapushAppID,
					'x-instapush-appsecret': instapushAppSecret}
	payload = '{"event":"message","trackers":{"message":"' + event + '"}}'
				   
	ret = requests.post('http://api.instapush.im/post',
					headers = headers,
					data = payload)
	
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
				#print "Sending push notification"
				
		#else:
		#	print "No zones running."

		i = i + 1
	
	#print ""
	sleep(5)

