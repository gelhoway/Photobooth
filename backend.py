#backend.py  Copyright (C) 2024  Valparaiso University

import time
import traceback
from BackendPackage import MailController, DataRetriever
import configparser

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
#Display name shown as the sender of the email
EMAIL_SENDER_NAME = config['EMAIL'].get('EmailSenderName', 'Photobooth')
#Url to google sheet linked with the form
SHEET_URL = config['URLS']['SheetUrl']

#Define a GmailController
mailController = MailController(EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_SENDER_NAME)

#Define a DataReceiver
dataController = DataRetriever(SHEET_URL)

while True:
    time.sleep(5)
    #Keep running even if a single check fails, so one bad response or network blip can't stop emails
    try:
        result = dataController.checkChanges()
        if(result):
            email, folderId = dataController.getRecentData(1)
            print("Sending pictures associated with key " + folderId[0] + " to email " + email[0])
            result = mailController.sendMessage(EMAIL_TITLE, EMAIL_BODY, email[0], folderId[0])
            if(result):
                print("Pictures associated with key " + folderId[0] + " sent successfully")
            else:
                print("Pictures associated with key " + folderId[0] + " failed to send")
    except Exception:
        print("ERROR IN BACKEND LOOP")
        traceback.print_exc()
