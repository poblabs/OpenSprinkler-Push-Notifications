#!/usr/bin/python

""" This script will check the OpenSprinkler API every 5 seconds and look for running stations.
    If a station is found running, it'll send a push notification through Instapush. It will only
	send a push notification once per zone, and only at start-up of the zone. """

import urllib2, json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from time import sleep

notifyZone = 0
notifySent = ""

def sendEmail():
	smtpServer = "localhost"
	fromEmail = "from@youremail"
	toEmail = ['to@youremail']
	subject = "OSPI Push Notification Script Failure"
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = fromEmail
	msg['To'] = ", ".join(toEmail)

	# Create the plain-text body of the message. 
	text = "The OSPI push notification script has crashed, or stopped. You should investigate this and restart it.\n\nssh to 192.168.0.60 and check /home/pi/ospi_push_notifications.py"
		
	part1 = MIMEText(text, 'plain')
	msg.attach(part1)
	s = smtplib.SMTP(smtpServer)
	s.sendmail(fromEmail, toEmail, msg.as_string())
	s.quit()

def getStatus():
	try:
		ospiStationStatus = urllib2.urlopen("http://localhost:8080/js?pw=<your API hex password>").read()
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
					'x-instapush-appid': "YOUR_INSTAPUSH_APPID",
					'x-instapush-appsecret': "YOUR_INSTAPUSH_APPSECRET"}
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
	for zone in stations:
		if (zone == 1):
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

