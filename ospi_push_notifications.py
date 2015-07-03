#!/usr/bin/python

""" This script will check the OpenSprinkler API every 5 seconds and look for running stations.
    If a station is found running, it'll send a push notification through Instapush. It will only
	send a push notification once per zone, and only at start-up of the zone. It also checks for
	rain sensor status and will send notifications based on that sensor's status. 
	
	If the script crashes, it will log to the syslog and send an email to let you know it's crashed. 
	
	6/26/2015, Pat O'Brien. Licensed under the MIT License.
	6/30/2015, added Pushover as a push notification service.
	7/2/2015, added rain sensor notifications, split out options to a config file
				and added more logging for troubleshooting	
	"""

import os, syslog, urllib2, json, requests, yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

def sendEmail():
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = fromEmail
	msg['To'] = toEmail
	part1 = MIMEText(text, 'plain')
	msg.attach(part1)
	s = smtplib.SMTP(smtpServer)
	s.sendmail(fromEmail, toEmail, msg.as_string())
	s.quit()

	
# Load config file
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
try:
	with open(config_path, 'r') as file:
		config = yaml.load(file)
except:
	syslog.syslog("Unable to load %s. Check the file and try again." % config_path)

# Setup variables from config file
ospiPort = config["ospi"]["port"]
ospiApiPasswordHash = config["ospi"]["password"]
pushService = config["push"]["service"]
instapushAppID = config["push"]["instapush"]["appID"]
instapushAppSecret = config["push"]["instapush"]["appSecret"]
pushoverUserKey = config["push"]["pushover"]["userKey"]
pushoverAppToken = config["push"]["pushover"]["appToken"]
fromEmail = config["email"]["from"]
toEmail = config["email"]["to"]
smtpServer = config["email"]["server"]
subject = config["email"]["subject"]
text = config["email"]["subject"]

# Get Rain Sensor status
def getRainSensorStatus():
	try:
		ospiRainSensorStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/jc?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Rain Sensor Status. You might have a bad hashed password.")
		sendEmail()
	
	try:
		data = json.loads(ospiRainSensorStatus)
	except:
		syslog.syslog("Unable to parse OSPi Rain Sensor Status JSON Output.")
		sendEmail()
		
	rainSensor = data["rs"]
	return rainSensor

# Get Station Status
def getStatus():
	try:
		ospiStationStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/js?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Station Status. You might have a bad hashed password.")
		sendEmail()
	
	try:
		data = json.loads(ospiStationStatus)
	except:
		syslog.syslog("Unable to parse OSPi Station Status JSON Output.")
		sendEmail()
		
	stations = data["sn"]
	#print "Getting sprinkler status. Zones defined: %s. Zone data: %s" % (data["nstations"],data["sn"])
	return stations

# Send Push Notification
def sendPushNotification(type, zoneID):
	# Change verbiage based on event type
	if (type == "station_active"):
		event = "Zone %s is now active" % zoneID
		
	elif (type == "rainSensor_active"):
		event = "Rain sensor has detected rain"
	
	elif (type == "rainSensor_clear"):
		event = "Rain sensor has cleared"
	
	
	if (pushService == "instapush"):
		headers = {'Content-Type': 'application/json',
						'x-instapush-appid': instapushAppID,
						'x-instapush-appsecret': instapushAppSecret}
		payload = '{"event":"message","trackers":{"message":"' + event + '"}}'
					   
		ret = requests.post('http://api.instapush.im/post',
						headers = headers,
						data = payload)
		syslog.syslog("Notification sent to %s. Message: %s. Return message: %s" % (pushService, event, ret))
		#print ret
	
	elif (pushService == "pushover"):
		payload = {
                "token": pushoverAppToken,
                "user" : pushoverUserKey,
                "message": event }
		ret = requests.post("http://api.pushover.net/1/messages.json", data = payload)
		syslog.syslog("Notification sent to %s. Message: %s. Return message: %s" % (pushService, event, ret))
		#print ret
		

# Main loop to check the status and send notification if necessary	
def main():
	syslog.syslog('Push notification script started')
	notifyZone = 0
	notifySent = "n"
	currentStation = 0
	currentRainStatus = 0
	
	while True:
		# Get the station & rain status from the controller API
		rainSensor = getRainSensorStatus()
		stations = getStatus()
		
		# Rain sensor status
		if (rainSensor == 1): # Rain sensor active
			if (currentRainStatus == 0): # Still showing no rain, send notification and set rain detected
				currentRainStatus = 1
				sendPushNotification("rainSensor_active", 0)
				
		elif (rainSensor == 0): # Rain sensor not active
			if (currentRainStatus == 1): # Still showing rain. Send an all clear notification and clear the rain detected
				currentRainStatus = 0
				sendPushNotification("rainSensor_clear", 0)

				
		# Station zone status
		i = 1
		for zoneStatus in stations:
			if (zoneStatus == 1):
				#print "Zone %s is active" % i
				if ( (notifyZone == i) & (notifySent == "y") ):
					#print "Push notification already sent"
					tempVar = "blah"
				else:
					sendPushNotification("station_active", i)
					notifyZone = i
					notifySent = "y"
					#print "Sending push notification to %s" % pushService
					
			i = i + 1
		
		sleep(5)

if __name__ == '__main__':
	main()
