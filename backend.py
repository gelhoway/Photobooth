#backend.py  Copyright (C) 2024  Valparaiso University

import sys
import time
from BackendPackage import MailController, DataRetriever
import configparser

#Flush prints immediately so they show up in the service log
sys.stdout.reconfigure(line_buffering=True)

#Parse config.ini
config = configparser.ConfigParser()
config.read("config.ini")

#Sender Email Address
EMAIL_ADDRESS = config['EMAIL']['EmailAddress']
#Sender Address Password
EMAIL_PASSWORD = config['EMAIL']['EmailPassword']
#Title of email
EMAIL_TITLE = config['EMAIL']['EmailTitle']
#Body of email
EMAIL_BODY = config['EMAIL']['EmailBody']
#Url to google sheet linked with the form
SHEET_URL = config['URLS']['SheetUrl']

#Define a GmailController
mailController = MailController(EMAIL_ADDRESS, EMAIL_PASSWORD)

#Define a DataReceiver
dataController = DataRetriever(SHEET_URL)

while True:
    time.sleep(5)
    #Never let one bad check or send stop the loop
    try:
        result = dataController.checkChanges()
        if(result):
            email, folderId = dataController.getRecentData(1)
            print("Sending pictures associated with key " + str(folderId[0]) + " to email " + str(email[0]))
            result = mailController.sendMessage(EMAIL_TITLE, EMAIL_BODY, email[0], folderId[0])
            if(result):
                print("Pictures associated with key " + str(folderId[0]) + " sent successfully")
            else:
                print("Pictures associated with key " + str(folderId[0]) + " failed to send")
    except Exception as e:
        print("Backend error: " + repr(e))
