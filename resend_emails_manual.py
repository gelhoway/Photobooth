#resend_emails_manual.py  Copyright (C) 2024  Valparaiso University

#Manually resend photos for submissions the backend missed.
#Usage:
#   python resend_emails_manual.py person@example.com ABCD [other@example.com EFGH ...]
#or, with no arguments, sends to the entries in the `missing` list below.
#Prefer the command line so real email addresses never end up in this file (or in git).

import configparser
import sys
from pathlib import Path
from BackendPackage import MailController

# Load the existing email settings.
config = configparser.ConfigParser()
config.read("config.ini")

EMAIL_ADDRESS = config["EMAIL"]["EmailAddress"]
EMAIL_PASSWORD = config["EMAIL"]["EmailPassword"]
EMAIL_TITLE = config["EMAIL"]["EmailTitle"]
EMAIL_BODY = config["EMAIL"]["EmailBody"]
EMAIL_SENDER_NAME = config["EMAIL"].get("EmailSenderName", "Photobooth")

mailController = MailController(EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_SENDER_NAME)

# Missing submissions: (recipient email, folder code).
missing = [
    ("example@gmail.com", "aaaa"),
]

# Command line pairs override the list above.
args = sys.argv[1:]
if args:
    if len(args) % 2 != 0:
        sys.exit("Usage: python resend_emails_manual.py EMAIL KEY [EMAIL KEY ...]")
    missing = list(zip(args[0::2], args[1::2]))

for email, folder_code in missing:
    folder_code = folder_code.strip().upper()
    folder = Path("Images") / folder_code

    print("\n-----------------------------------")
    print("Recipient:", email)
    print("Folder code:", folder_code)

    if not folder.is_dir():
        print("SKIPPED: Photo folder does not exist.")
        continue

    photos = [
        p for p in folder.iterdir()
        if p.is_file()
    ]

    if not photos:
        print("SKIPPED: No files found in photo folder.")
        continue

    print("Files to attach:", len(photos))

#    confirm = input("Send this email? Type YES to confirm: ")
#    if confirm != "YES":
#        print("Skipped.")
#        continue

    try:
        success = mailController.sendMessage(
            EMAIL_TITLE,
            EMAIL_BODY,
            email,
            folder_code
        )

        if success:
            print("SUCCESS: Email sent to", email)
        else:
            print("FAILED: MailController returned False")

    except Exception as exc:
        print("ERROR:", type(exc).__name__, str(exc))

print("\nFinished processing the list.")
