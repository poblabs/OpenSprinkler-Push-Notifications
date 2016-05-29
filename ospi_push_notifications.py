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
	7/6/2015, Added IFTTT Maker channel https://ifttt.com/maker as push notification service. 
				Thanks nystrom! (https://opensprinkler.com/forums/users/nystrom/)
	7/8/2015, Updated the notifications to use the station name from the API as opposed to a static "Zone #"
				Fixed rain sensor notifications. If the sensor option is disabled, do not check for the status
				Updated sendEmail() to include the message that is logged to syslog

	8/12/2015, KDB - Added the following:
				- Support for Program start and end notifications
				- Moved functionality checks to individual objects. Easier to follow and minor 
				  efficiency gains. 
				- Added generic "message" as default for the notification routine. 
				- can now specify pushover "sound" in the config file.
				- Added some comments and error handling output to help with debugging...etc.

    	4/29/2016, Added logmsg() to simplify logging
	"""

import os, syslog, urllib2, json, requests, yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

# How long to sleep for each iteration of the run loop
POLL_SLEEP = 10

def logmsg(msg):
    print msg
    syslog.syslog(syslog.LOG_INFO, 'OpenSprinkler Notification: %s' % msg)

def sendEmail(message):
	body = text.format(message)
	msg = "\r\n".join([
		"From: " + fromEmail,
		"To: " + toEmail,
		"Subject: " + subject,
		"",
		body
	])

	if (smtpServer == "gmail"):
		username = config["email"]["gmailUsername"]
		password = config["email"]["gmailPassword"]
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.ehlo()
		server.starttls()
		server.login(username,password)
		server.sendmail(fromEmail, toEmail, msg)
		server.quit()
	elif (smtpServer == "localhost"):
		s = smtplib.SMTP("localhost")
		s.sendmail(fromEmail, toEmail, msg)
		s.quit()
		
	logmsg("Email sent to %s. Exiting script due to error." % toEmail)
	exit() # Exit Python since we have encountered an error. Added this in due to multiple emails being sent.

	
# Load config file
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
try:
	with open(config_path, 'r') as file:
		config = yaml.load(file)
except:
	logmsg("Unable to load %s. Check the file exists and try again." % config_path)

# Setup variables from config file
ospiPort = config["ospi"]["port"]
ospiApiPasswordHash = config["ospi"]["password"]
pushService = config["push"]["service"]
instapushAppID = config["push"]["instapush"]["appID"]
instapushAppSecret = config["push"]["instapush"]["appSecret"]
pushoverUserKey = config["push"]["pushover"]["userKey"]
pushoverAppToken = config["push"]["pushover"]["appToken"]
#KDB make sure sound is there for pushover, just in case an old config file is being used.
if "sound" in config["push"]["pushover"]:
	pushoverSound = config["push"]["pushover"]["sound"]
else:
	pushoverSound = "pushover"
iftttEventName = config["push"]["ifttt"]["eventName"]
iftttUserKey = config["push"]["ifttt"]["userKey"]
fromEmail = config["email"]["from"]
toEmail = config["email"]["to"]
smtpServer = config["email"]["server"]
subject = config["email"]["subject"]
text = config["email"]["text"]

#-----------------------------------------------------------------------------
# KDB - Check program Status
# return True if a program is running, false if it is not

def getProgramStatus():
	try:
		ospiProgramStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/jc?pw=" + ospiApiPasswordHash).read()
	except:
		error = "Unable to load the OSPi API URL for Program Status You might have a bad hashed password or the OSPi is not online."
		logmsg(error)
		sendEmail(error)
	
	try:
		data = json.loads(ospiProgramStatus)
	except:
		error = "Unable to parse OSPi Program Status JSON Output."
		logmsg(error)
		sendEmail(error)

	# Loop over the PS fields - if the first element is not 0, we have a program running (something is queued up )
	for station in data['ps']:
		if station[0] != 0:
			return station[0]

	return 0
#-----------------------------------------------------------------------------
# Get the program Name -- hacked this from the OpenSprinkler GUI javascript
def getProgramName(pid):

	if pid == 255 or pid == 99:
		return "Manual"
	elif pid == 254 or pid == 98:
		return "Run-Once"
	else:
		# get the available programs from the system
		try:
			progsData = urllib2.urlopen("http://localhost:" + ospiPort + "/jp?pw=" + ospiApiPasswordHash).read()
		except:
			error = "Unable to load the OSPi API URL for Program Names."
			logmsg(error)
			sendEmail(error)
			return "Uknown"
		
		try:
			progs = json.loads(progsData)
		except:
			error = "Unable to parse OSPi Program Data JSON Output."
			logmsg(error)
			sendEmail(error)
			return "Uknown"

		if pid <= len(progs['pd']):
			return str(progs['pd'][pid-1][5])
		else:
			return "Unknown"

#-----------------------------------------------------------------------------
# Get Station Status
def getStationStatus():
	try:
		ospiStationStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/js?pw=" + ospiApiPasswordHash).read()
	except:
		error = "Unable to load the OSPi API URL for Station Status. You might have a bad hashed password or the OSPi is not online."
		logmsg(error)
		sendEmail(error)
	
	try:
		data = json.loads(ospiStationStatus)
	except:
		error = "Unable to parse OSPi Station Status JSON Output."
		logmsg(error)
		sendEmail(error)
		
	stations = data["sn"]
	#print "Getting sprinkler status. Zones defined: %s. Zone data: %s" % (data["nstations"],data["sn"])
	return stations

# Get the name of the station
def getStationName(id):
	try:
		ospiStationName = urllib2.urlopen("http://localhost:" + ospiPort + "/jn?pw=" + ospiApiPasswordHash).read()
	except:
		error = "Unable to load the OSPi API URL for Station Names & Attributes. You might have a bad hashed password or the OSPi is not online."
		logmsg(error)
		sendEmail(error)
	
	try:
		data = json.loads(ospiStationName)
	except:
		error = "Unable to parse OSPi Station Names & Attributes JSON Output."
		logmsg(error)
		sendEmail(error)
	
	# The list of stations starts at 0. We need to subtract 1 to get the right ID in the list
	id = id - 1
	stationName = data["snames"][id]
	return stationName

# Get Rain Sensor status
def getRainSensorStatus():
	# Is the rain sensor enabled?
	try:
		ospiRainSensorEnabled = urllib2.urlopen("http://localhost:" + ospiPort + "/jo?pw=" + ospiApiPasswordHash).read()
		enabled = json.loads(ospiRainSensorEnabled)
	except:
		error = "Unable to load the OSPi API URL for Options. You might have a bad hashed password or the OSPi is not online."
		logmsg(error)
		sendEmail(error)
		
	if ( enabled["urs"] == 1):
		# Get the rain status
		try:
			ospiRainSensorStatus = urllib2.urlopen("http://localhost:" + ospiPort + "/jc?pw=" + ospiApiPasswordHash).read()
		except:
			error = "Unable to load the OSPi API URL for Rain Sensor Status. You might have a bad hashed password or the OSPi is not online."
			logmsg(error)
			sendEmail(error)
		
		try:
			data = json.loads(ospiRainSensorStatus)
		except:
			error = "Unable to parse OSPi Rain Sensor Status JSON Output."
			logmsg(error)
			sendEmail(error)
			
		rainSensor = data["rs"]
		return rainSensor
	

# Get the watering level
def getWaterLevel():
	try:
		ospiWaterLevel = urllib2.urlopen("http://localhost:" + ospiPort + "/jo?pw=" + ospiApiPasswordHash).read()
	except:
		error = "Unable to load the OSPi API URL for Water Level. You might have a bad hashed password or the OSPi is not online."
		logmsg(error)
		sendEmail(error)
	
	try:
		data = json.loads(ospiWaterLevel)
	except:
		error = "Unable to parse OSPi Water Level JSON Output."
		logmsg(error)
		sendEmail(error)

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
	else:
		event = notifyType  # just use the notify type - for simple messaging
	
	if (pushService == "instapush"):
		headers = {'Content-Type': 'application/json',
						'x-instapush-appid': instapushAppID,
						'x-instapush-appsecret': instapushAppSecret}
		payload = '{"event":"message","trackers":{"message":"' + event + '"}}'
					   
		ret = requests.post('http://api.instapush.im/post',
						headers = headers,
						data = payload)
		logmsg("Notification sent to %s. Message: %s. Return message: %s" % (pushService, event, ret))
		#print ret
	
	elif (pushService == "pushover"):
		payload = {
                "token": pushoverAppToken,
                "user" : pushoverUserKey,
                "sound": pushoverSound,
                "message": event }
		ret = requests.post("http://api.pushover.net/1/messages.json", data = payload)
		logmsg("Notification sent to %s. Message: %s. Return message: %s" % (pushService, event, ret))
		#print ret
		
	elif (pushService == "ifttt"):
		url = "http://maker.ifttt.com/trigger/" + iftttEventName + "/with/key/" + iftttUserKey
		payload = { 'value1': event }
		ret = requests.post(url, data = payload)
		logmsg("Notification sent to %s. Message: %s. Return message %s" % (pushService, event, ret))
		#print ret
		
#----------------------------------------------------
# KDB - define a base class for our status check activities

class Status(object):

	def __init__(self, config):
		object.__init__(self)
		return

	# STATIC Method used to determine if this check is enabled. This is used to populate
	# the active checks list in the run loop
	@staticmethod
	def isEnabled(config):
		return False 

	# method that performs the check. 
	def check(self):
		pass

#----------------------------------------------------
# Per station status check logic
class stationStatus(Status):

	def __init__(self, config):

		Status.__init__(self,  config)

		self.notifyStart = config["stations"]["notify"]["start"] == "yes"
		self.notifyStop = config["stations"]["notify"]["stop"] == "yes"		
		self.currentStation = 0

	@staticmethod
	def isEnabled(config):
		return (config["stations"]["notify"]["start"] == "yes" or config["stations"]["notify"]["stop"] == "yes")

	def check(self):
		stations = getStationStatus()
		i = 1
		for zoneStatus in stations:
			if (zoneStatus == 1):
				if (self.currentStation != i):

					# Zone change detected. Send notification that previous zone stopped, except if previous zone was 0
					if ( (self.currentStation != 0) & self.notifyStop):
						logmsg("Station has gone idle: %s" % self.currentStation)
						sendPushNotification("station_idle", self.currentStation)
					
					self.currentStation = i
					# New zone is active, send notification
					if (self.notifyStart):
						logmsg("Station is now active: %s" % i)
						sendPushNotification("station_active", i)

			elif ( (zoneStatus == 0) & (self.currentStation == i) ):
				# All stations off, including a previously-on station. Send idle notification, and reset station to 0
				if (self.currentStation != 0) & (self.notifyStop ):
					logmsg("Station has gone idle: %s" % self.currentStation)
					sendPushNotification("station_idle", self.currentStation)
					self.currentStation = 0
					
			i = i + 1

#----------------------------------------------------
# per Program status check logic
class programStatus(Status):

	def __init__(self, config):

		Status.__init__(self,  config)

		self.notifyStart = config["programs"]["notify"]["start"] == "yes"
		self.notifyStop = config["programs"]["notify"]["stop"] == "yes"		
		self.currentProgramName = "Unknown"
		self.bProgramRunning = False

	@staticmethod
	def isEnabled(config):
		return (config["programs"]["notify"]["start"] == "yes" or config["programs"]["notify"]["stop"] == "yes")

	def check(self):
		pid = getProgramStatus()
		bStatus = pid != 0
		# change of program state?
		if bStatus != self.bProgramRunning:
			if bStatus and self.notifyStart:
				self.currentProgramName = getProgramName(pid)
				txt = "Started " + self.currentProgramName + " Program"
				logmsg(txt)
				sendPushNotification(txt, None)
			elif not bStatus and  self.notifyStop:
				txt = "Ending " + self.currentProgramName + " Program"
				logmsg(txt)
				sendPushNotification(txt, None)		
				self.currentProgramName = "Unknown"			

			self.bProgramRunning = bStatus

#----------------------------------------------------
# Rain sensor status check logic
class rainSensorStatus(Status):

	def __init__(self, config):

		Status.__init__(self,  config)

		self.notify = config["rain"]["notify"] == "yes"
		self.currentRainStatus = 0

	@staticmethod
	def isEnabled(config):
		return (config["rain"]["notify"] == "yes")

	def check(self):
		rainSensor = getRainSensorStatus()
		if rainSensor == self.currentRainStatus:
			return  # No change

		# Do we have rain now?
		if (rainSensor == 1):
			logmsg("Rain sensor is now active")
			sendPushNotification("rainSensor_active", 0)
		else:
			# No rain now
			logmsg("Rain sensor has cleared")
			sendPushNotification("rainSensor_clear", 0)

		self.currentRainStatus = rainSensor

#----------------------------------------------------
# Water Level status check logic

class waterLevelStatus(Status):

	def __init__(self, config):

		Status.__init__(self,  config)

		self.notify = config["waterlevel"]["notify"] == "yes"
		self.currentWaterLevel = 0

	@staticmethod
	def isEnabled(config):
		return (config["waterlevel"]["notify"] == "yes")

	def check(self):
		waterLevel = getWaterLevel()
		if (self.currentWaterLevel != waterLevel):
			# New water level detected
			self.currentWaterLevel = waterLevel
			logmsg("Water level has changed to: %s" % waterLevel)
			sendPushNotification("waterLevel", waterLevel)

#----------------------------------------------------
# Main loop to check the status and send notification if necessary	
def main():
	logmsg('OSPi push notification script started.')
	
	# What checks do we need to make in the processing loop?
	statusChecks = []
	if stationStatus.isEnabled(config):
		statusChecks.append(stationStatus(config))

	if programStatus.isEnabled(config):
		statusChecks.append(programStatus(config))

	if rainSensorStatus.isEnabled(config):
		statusChecks.append(rainSensorStatus(config))

	if waterLevelStatus.isEnabled(config):
		statusChecks.append(waterLevelStatus(config))

	# if we have no checks, bail
	if len(statusChecks) == 0:
		logmsg("No status checks specified in the config file. Exiting.")
		return

	# Start the run loop
	try:
		while True:

			for activity in statusChecks:
				activity.check()

			# sleep 
			sleep(POLL_SLEEP)

	except Exception as errEx:
		logmsg("OSPi push notification script stopped." + str(errEx))

if __name__ == '__main__':
	main()
