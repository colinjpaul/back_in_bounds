#!/usr/bin/env python3

version="1.4.0"

"""
Source: https://garminbadges.com/upload/garminbadges-updater.py

Change log:
1.4 Command line arguments to open web pages and more.
1.3 Fetched joined date for expeditions.
1.2 Version check. POST data in all requests.
1.1 Threading to speed it up. 
1.0 First release

Requirements:
Python3 and pip3 installation.

The python command can be different for different installs: python3, python or py

Run this before you run the script to install the dependencies:
python -m pip install garth

To run this script run:
python garminbadges-updater.py

It will ask for Garmin badges credentials and then Garmin Connect credentials. It will also ask for MFA key is MFA is activated in your Garmin Account.
To remove all credentials and start over delete the folder ~/.garth and run the script again or start the script with the argument: clear

"""

import garth
from getpass import getpass
import requests
import sys
import json
import os
import logging
from threading import Thread
import threading
from pathlib import Path
import webbrowser
#import time

userId = 0
updateKey = ""
pythonVersion = ""
debugMode = False

def main():
	#start_time = time.time()

	handleArguments(sys.argv)
	if(debugMode):
		printVersion()
		print("Verbose/debug mode enabled")
		print("Script started with command: " + ' '.join(sys.argv))

	global userId, updateKey

	configFileName = getConfigFileNameAndMakeSureFolderExists()

	loginToGarminBadgesAndConnect(configFileName)

	fetchUserInfoFromGarminBadgesToGlobalVariables(configFileName)

	doVersionCheck(pythonVersion, version)

	# Fetch earned Json from Garmin.
	garminEarnedJson = garth.connectapi("/badge-service/badge/earned")

	# createGarminBadgesJson
	strippedGarminEarnedJson = createGarminBadgesJson(garminEarnedJson, updateKey);

	# POST stripped Json to Garmin Badges and get badgeIds to fetch from Garmin.
	badgesToFetch = postJsonToGarminbadges(strippedGarminEarnedJson, "https://garminbadges.com/api/index.php/user/earned")

	# Fetch badges from Garmin
	garminBadgeJsonArray = fetchBadgesFromGarmin(badgesToFetch.json());

	# createGarminBadgesJson.
	garminBadgeJson = createGarminBadgesJson(garminBadgeJsonArray, updateKey);

	# POST the new badge json to Garmin Badges.
	gbBadgeResponse = postJsonToGarminbadges(garminBadgeJson, "https://garminbadges.com/api/index.php/user/challenges")

	# Open web pages
	openWebPages(sys.argv)

	if(debugMode):
		print("Script ended.")

	#print("--- %s seconds ---" % (time.time() - start_time))

def getConfigFileNameAndMakeSureFolderExists():
	configDir = os.path.expanduser('~') + "/.garminbadges/"
	configFileName = configDir + "config.json"
	Path(configDir).mkdir(parents=True, exist_ok=True)
	return configFileName

def handleArguments(arguments):
	global debugMode

	if "--version" in sys.argv:
		printVersion()
		sys.exit(0)
	if "--help" in sys.argv:
		printHelp()
		sys.exit(0)
	if "--V" in sys.argv:
		debugMode = True


def loginToGarminBadgesAndConnect(configFileName):
	try:
		# Check if config file exists
		f = open(configFileName, "r")
                
		if "--clear" in sys.argv:
			raise Exception
		garth.resume("~/.garth")
		garth.client.username
	except Exception as e:
		if(debugMode):
			print("Session is expired or an error occured. You'll need to log in again");
		gbUsername = input("Enter Garmin Badges username: ")
		gbEmail = input("Enter Garmin Badges email: ")

		config = {"gbUsername": gbUsername, "gbEmail": gbEmail}

		with open(configFileName, 'w') as f:
			json.dump(config, f)

		gcEmail = input("Enter Garmin Connect username: ")
		gcPassword = getpass("Enter Garmin Connect password: ")
		# If there's MFA, you'll be prompted during the login
		garth.login(gcEmail, gcPassword)
		garth.save("~/.garth")

def fetchUserInfoFromGarminBadgesToGlobalVariables(configFileName):
	global pythonVersion, updateKey, userId

	with open(configFileName, 'r') as f:
		config = json.load(f)

	# Get update key and user id from garminbadges.com
	updateKeyJson = {
		"username": config["gbUsername"],
		"email": config["gbEmail"]
	}
	response = postJsonToGarminbadges(updateKeyJson, "https://garminbadges.com/api/index.php/user/updatekey")
	userId = response.json()["id"]
	updateKey = response.json()["update_key"]
	pythonVersion = response.json()["python_script_version"]

def doVersionCheck(latestVersion, currentVersion):
	if (latestVersion == currentVersion):
		return
	else:
		latestVersionArray = [int(num) for num in latestVersion.split('.')]
		currentVersionArray = [int(num) for num in currentVersion.split('.')]

		# Ignore patch version
		latestVersionArray.pop()
		currentVersionArray.pop()

		for latestVersionValue, currentVersionValue in zip(latestVersionArray, currentVersionArray):
			if latestVersionValue > currentVersionValue:
				print("Script is outdated and will not run. Get the latest version (v.{}) at https://garminbadges.com/upload/garminbadges-updater.py".format(latestVersion))
				sys.exit()

def fetchOneBadgeFromGarmin(badgeNo, badgeUuid, badgeJson):
	try:
		garminBadgeResponse = garth.connectapi("/badge-service/badge/detail/v2/" + str(badgeNo))
		if badgeUuid:
			garminBadgeResponseUuid = garth.connectapi("/badgechallenge-service/badgeChallenge/" + badgeUuid)
			garminBadgeResponse["joinDateLocal"] = garminBadgeResponseUuid["joinDateLocal"]
		badgeJson.append(garminBadgeResponse)
	except Exception as e:
		if not garminBadgeResponse:
			badgeJson.append("")
		else:
			badgeJson.append(garminBadgeResponse)
	return True

def fetchBadgesFromGarmin(badgesToFetch):
	NO_OF_THREADS_BEFORE_START = threading.active_count()
	badgeJson = []
	threads = []
	threadIndex = 0
	runningThreads = 0
	
	maxNumberOfRunningThreads = 10

	# Create all threads
	for badge in badgesToFetch:
		process = Thread(target=fetchOneBadgeFromGarmin, args=[badge["badgeNo"], badge["badgeUuid"], badgeJson])
		threads.append(process)

	# Limit the number of started threads to not exceed the thread pool
	while len(badgeJson) < len(threads):
		if(threadIndex < len(threads) and threading.active_count() - NO_OF_THREADS_BEFORE_START < maxNumberOfRunningThreads):
			threads[threadIndex].start()
			threadIndex += 1
	return badgeJson


def postJsonToGarminbadges(json, url):
	headers = {'Content-type': 'application/json'}
	return requests.post(url, headers=headers, json=json)

def createGarminBadgesJson(json, updateKey):
	newJson = []
	joinDateLocal = None;

	unitArray = {
		1: "mi_km",
		2: "ft_m",
		3: "activities",
		4: "days",
		5: "steps",
		6: "mi",
		7: "seconds"
	}

	for badge in json:
		if not badge:
			continue
		badgeUnit = ""
		try:
			badgeUnit = unitArray[badge["badgeUnitId"]]
		except KeyError as e:
			badgeUnit = ""

		if "joinDateLocal" in badge:
			joinDateLocal = badge["joinDateLocal"]
			
		newBadge = {
			"badgeId": badge["badgeId"],
			"badgeName": badge["badgeName"],
			"count": badge["badgeEarnedNumber"],
			"earned_date": badge["badgeEarnedDate"],
			"badgeProgressValue": badge["badgeProgressValue"],
			"badgeTargetValue": badge["badgeTargetValue"],
			"badgeUnit": badgeUnit,
			"userJoined": True if badge["userJoined"] else False,
			"joinDateLocal": joinDateLocal,
			"createdBy": "Python script v." + version
		}
		newJson.append(newBadge);

	newJson = {
		"update_key": updateKey,
		"badges": newJson
	}

	return newJson


def openWebPages(arguments):
	global userId
	if "--open-badges" in sys.argv:
		webbrowser.open_new_tab("https://garminbadges.com/index.php?userId=" + str(userId))
	if "--open-challenges" in sys.argv:
		webbrowser.open_new_tab("https://garminbadges.com/challenges.php?userId=" + str(userId))

def printVersion():
	print("Garminbadges Updater v." + version)

def printHelp():
	print("Usage: garminbadges-updater.py [options]\n")
	print("Options and arguments:")
	print("   --clear           : Enter user credentials again.")
	print("   --help            : This information about options and arguments.")
	print("   --open-badges     : Open badge page after update.")
	print("   --open-challenges : Open challenge page after update.")
	print("   --version         : Print version of the script.")
	print("   --V               : Verbose/debug mode.")


if __name__ == "__main__":
	main()
