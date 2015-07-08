#!/usr/bin/python

""" This script will check the OpenSprinkler API every 5 seconds and look for running stations.
    If a station is found running, it'll send a push notification through Instapush. It will only
	send a push notification once per zone, and only at start-up of the zone. It also checks for
	rain sensor status and will send notifications based on that sensor's status. 
	
	If the script crashes, it will log to the syslog and send an email to let you know it's crashed. 
	
	6/26/2015, Pat O'Brien. Licensed under the MIT License. Initial release.
	6/30/2015, added Pushover as a push notification service.
	7/2/2015, added rain sensor notifications, split out options to a config file
				and added more logging for troubleshooting	
	7/5/2015, This is a big update since the initial release of the script:
				Re-wrote the entire station notification to be able to notify when the station has turned off.
				Added more options to the config file, such as individual notify on/off and also
					the ability to customize individual notification messages. 
				Added water level notification. 
					Thanks Joe! (https://opensprinkler.com/forums/users/jchiar/)
				Added more verbose logging. 
				Lastly, re-organized the functions and main loop code.
	7/6/2016, Added IFTTT Maker channel https://ifttt.com/maker as push notification service. 
				Thanks nystrom! (https://opensprinkler.com/forums/users/nystrom/)
	7/8/2016, Updated the notifications to use the station name from the API as opposed to a static "Zone #"
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
	syslog.syslog("Unable to load %s. Check the file exists and try again." % config_path)

# Setup variables from config file
ospiPort = config["ospi"]["port"]
ospiApiPasswordHash = config["ospi"]["password"]
pushService = config["push"]["service"]
instapushAppID = config["push"]["instapush"]["appID"]
instapushAppSecret = config["push"]["instapush"]["appSecret"]
pushoverUserKey = config["push"]["pushover"]["userKey"]
pushoverAppToken = config["push"]["pushover"]["appToken"]
iftttEventName = config["push"]["ifttt"]["eventName"]
iftttUserKey = config["push"]["ifttt"]["userKey"]
fromEmail = config["email"]["from"]
toEmail = config["email"]["to"]
smtpServer = config["email"]["server"]
subject = config["email"]["subject"]
text = config["email"]["subject"]

# Get Station Status
def getStationStatus():
	try:
		ospiStationStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/js?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Station Status. You might have a bad hashed password or the OSPi is not online.")
		sendEmail()
	
	try:
		data = json.loads(ospiStationStatus)
	except:
		syslog.syslog("Unable to parse OSPi Station Status JSON Output.")
		sendEmail()
		
	stations = data["sn"]
	#print "Getting sprinkler status. Zones defined: %s. Zone data: %s" % (data["nstations"],data["sn"])
	return stations

# Get the name of the station
def getStationName(id):
	try:
		ospiStationName = urllib2.urlopen("http://localhost:" + ospiPort + "/jn?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Station Names & Attributes. You might have a bad hashed password or the OSPi is not online.")
		sendEmail()
	
	try:
		data = json.loads(ospiStationName)
	except:
		syslog.syslog("Unable to parse OSPi Station Names & Attributes JSON Output.")
		sendEmail()
	
	# The list of stations starts at 0. We need to subtract 1 to get the right ID in the list
	id = id - 1
	stationName = data["snames"][id]
	return stationName

# Get Rain Sensor status
def getRainSensorStatus():
	try:
		ospiRainSensorStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/jc?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Rain Sensor Status. You might have a bad hashed password or the OSPi is not online.")
		sendEmail()
	
	try:
		data = json.loads(ospiRainSensorStatus)
	except:
		syslog.syslog("Unable to parse OSPi Rain Sensor Status JSON Output.")
		sendEmail()
		
	rainSensor = data["rs"]
	return rainSensor

# Get the watering level
def getWaterLevel():
	try:
		ospiWaterLevel = urllib2.urlopen("http://localhost:" + ospiPort + "/jo?pw=" + ospiApiPasswordHash).read()
	except:
		syslog.syslog("Unable to load the OSPi API URL for Water Level. You might have a bad hashed password or the OSPi is not online.")
		sendEmail()
	
	try:
		data = json.loads(ospiWaterLevel)
	except:
		syslog.syslog("Unable to parse OSPi Water Level JSON Output.")
		sendEmail()

	waterLevel = data["wl"]
	#print "Water level currently is %s%%" % waterLevel
	return waterLevel

# Send Push Notification
def sendPushNotification(notifyType, notifyInfo):
	# Change verbiage based on event type
	if (notifyType == "station_active"):
		stationName = getStationName(notifyInfo)
		event = config["stations"]["messages"]["start"].format(stationName)
		
	elif (notifyType == "station_idle"):
		stationName = getStationName(notifyInfo)
		event = config["stations"]["messages"]["stop"].format(stationName)
		
	elif (notifyType == "rainSensor_active"):
		event = config["rain"]["messages"]["active"]
	
	elif (notifyType == "rainSensor_clear"):
		event = config["rain"]["messages"]["clear"]
		
	elif (notifyType == "waterLevel"):
		event = config["waterlevel"]["message"].format(notifyInfo)
	
	
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
		
	elif (pushService == "ifttt"):
		url = "http://maker.ifttt.com/trigger/" + iftttEventName + "/with/key/" + iftttUserKey
		payload = { 'value1': event }
		ret = requests.post(url, data = payload)
		syslog.syslog("Notification sent to %s. Message: %s. Return message %s" % (pushService, event, ret))
		#print ret
		

# Main loop to check the status and send notification if necessary	
def main():
	syslog.syslog('OSPi push notification script started.')
	currentStation = 0
	currentRainStatus = 0
	currentWaterLevel = 0
	
	try:
		while True:
		
			# Station zone status
			stations = getStationStatus()
			i = 1
			for zoneStatus in stations:
				if (zoneStatus == 1):
					if (currentStation != i):
						# Zone change detected. Send notification that previous zone stopped, except if previous zone was 0
						if ( (currentStation != 0) & (config["stations"]["notify"]["stop"] == "yes") ):
							syslog.syslog("Station has gone idle: %s" % currentStation)
							sendPushNotification("station_idle", currentStation)
						currentStation = i
						# New zone is active, send notification
						if (config["stations"]["notify"]["start"] == "yes"):
							syslog.syslog("Station is now active: %s" % i)
							sendPushNotification("station_active", i)

				elif ( (zoneStatus == 0) & (currentStation == i) ):
					# All stations off, including a previously-on station. Send idle notification, and reset station to 0
					if ( (currentStation != 0) & (config["stations"]["notify"]["stop"] == "yes") ):
						syslog.syslog("Station has gone idle: %s" % currentStation)
						sendPushNotification("station_idle", currentStation)
						currentStation = 0
						
				i = i + 1

			# Rain sensor status & notifications
			if (config["rain"]["notify"] == "yes"):
				rainSensor = getRainSensorStatus()
				if (rainSensor == 1): # Rain sensor active
					if (currentRainStatus == 0): # We showed no rain, now we have rain, send notification and set rain detected
						currentRainStatus = 1
						syslog.syslog("Rain sensor is now active")
						sendPushNotification("rainSensor_active", 0)
				elif ( (config["rain"]["notify"] == "yes") & (rainSensor == 0) ): # Rain sensor not active
					if (currentRainStatus == 1): # We showed rain, now we have no rain. Send an all clear notification and clear the rain detected
						currentRainStatus = 0
						syslog.syslog("Rain sensor has cleared")
						sendPushNotification("rainSensor_clear", 0)

			# Water level notifications
			if (config["waterlevel"]["notify"] == "yes"):
				waterLevel = getWaterLevel()
				if (currentWaterLevel != waterLevel):
					# New water level detected
					currentWaterLevel = waterLevel
					syslog.syslog("Water level has changed to: %s" % waterLevel)
					sendPushNotification("waterLevel", waterLevel)
					

			sleep(5)
	except:
		syslog.syslog("OSPi push notification script stopped.")

if __name__ == '__main__':
	main()
