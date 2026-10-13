#backendClasses.py  Copyright (C) 2024  Valparaiso University

import smtplib, ssl #standard lib
import html #standard lib
import mimetypes #standard lib
import os #standard lib
import re #standard lib
from email.message import EmailMessage #standard lib
from email.utils import formataddr #standard lib
import pandas as pd #pandas
from pathlib import Path #pathlib

class MailController:
    """Functions:
        sendMessage(title, body, destEmail, folderKey)
    """
    def __init__(self, email, password, senderName="Photobooth"):
        self.email = email
        self.password = password
        self.senderName = senderName

    #Valparaiso University brand colors
    VALPO_BROWN = "#5C3000"
    VALPO_DARK_BROWN = "#331A00"
    VALPO_GOLD = "#F5B80A"

    def _buildHtml(self, title, body, photoCount):
        """Builds a Valpo brown and gold themed, email-client friendly HTML version of the message body"""
        paragraphs = "".join(
            f'<p style="margin:0 0 12px 0;">{html.escape(line)}</p>'
            for line in body.splitlines() if line.strip()
        )
        plural = "photo" if photoCount == 1 else "photos"
        brown, darkBrown, gold = self.VALPO_BROWN, self.VALPO_DARK_BROWN, self.VALPO_GOLD
        return f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background-color:#f3eee8;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3eee8;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:8px;overflow:hidden;font-family:Arial,Helvetica,sans-serif;color:#333333;">
            <tr>
              <td style="background-color:{brown};padding:24px 32px;border-bottom:6px solid {gold};">
                <p style="margin:0 0 4px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{gold};font-weight:bold;">Valparaiso University</p>
                <h1 style="margin:0;font-size:24px;color:#ffffff;">{html.escape(title)}</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 12px 32px;font-size:15px;line-height:1.5;">
                {paragraphs}
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 28px 32px;">
                <table role="presentation" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="background-color:{gold};color:{darkBrown};border-radius:4px;padding:10px 18px;font-size:15px;font-weight:bold;">
                      {photoCount} {plural} attached
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="background-color:{darkBrown};padding:16px 32px;font-size:12px;color:#d9c9b8;">
                Go Beacons! This is an automated message from the Valpo photo booth. Please do not reply.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    def sendMessage(self, title, body, destEmail, folderKey):
        """Sends a email using gmail to destEmail, containing files in folder Images/folderKey

            title: title of email
            body: body of email (plain text, a styled HTML version is generated automatically)
            destEmail: email address to send the email to
            folderKey: name of folder the pictures you want to send are stored in
                relative path to attachments should be Images/folderKey with all attachments inside folder folderKey
            Returns: bool (True if successfully sent, False if not)
        """
        #Grab images in accessed image folder, oldest first so they arrive in the order taken
        try:
            images = sorted((Path('Images') / folderKey).iterdir(), key=os.path.getmtime)
        except OSError:
            print("Invalid Key")
            return False
        images = [i for i in images if i.is_file()]
        if not images:
            print("No pictures found for key " + folderKey)
            return False

        #Create message with a plain text body and an HTML alternative
        message = EmailMessage()
        message["From"] = formataddr((self.senderName, self.email))
        message["To"] = destEmail
        message["Subject"] = title
        message.set_content(body)
        message.add_alternative(self._buildHtml(title, body, len(images)), subtype="html")

        #Attach images with their real type and a clean, numbered file name
        for number, image in enumerate(images, start=1):
            mimeType, _ = mimetypes.guess_type(image.name)
            maintype, subtype = (mimeType or "application/octet-stream").split("/", 1)
            message.add_attachment(
                image.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=f"photobooth-{number}{image.suffix.lower()}",
            )

        #Send email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.email, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as e:
            print("ERROR SENDING EMAIL: " + str(e))
            return False
        return True

class DataRetriever:
    """Checks if there are changes to a given google sheet and gets data from a given google sheet
    
        Functions:
        checkChanges()
        getRecentData(num)
    """
    def __init__(self, sheetsUrl):
        """Inititalizes dataRetreiver with given link to public google sheet"""
        # Regular expression to match and capture the necessary part of the URL
        pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'
        # Replace function to construct the new URL for CSV export
        # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
        downloadUrl = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'
        # Replace using regex
        downloadUrl = re.sub(pattern, downloadUrl, sheetsUrl)
        #Store csv download link
        self.csvUrl = downloadUrl
        try:
            self.currentData = pd.read_csv(self.csvUrl)
        except:
            self.currentData = None
            print("Spreadsheet Empty (Init)")

    def checkChanges(self):
        """Checks to see if any changes have been made to the data retriever website

            Returns: bool (True if different, False otherwise)
        """
        #Get frame and compare
        try:
            df2 = pd.read_csv(self.csvUrl)
        except:
            df2 = None
            print("Spreadsheet Empty (Compare)")
            return False
        #If no change
        if(self.currentData.equals(df2)):
            return False
        #Change detected
        else:
            #Update currentData with new data
            self.currentData = df2
            return True

    def getRecentData(self, num):
        """Retrieves the most recent num entries from current dataframe

            Returns: email (list of emails), folderKey (list of folder keys)
                email and folderKey lists are ordered by most recent response
        """
        email = []
        folderId = []
        try:
            for i in range(num):
                entry = self.currentData.iloc[-(i+1)]
                entry = entry.values.tolist()
                email.append(entry[1])
                folderId.append(entry[2].upper())
            return email, folderId
        except:
            print("Sheet Emptied")
            email.append(" ")
            folderId.append(" ")
            return email, folderId
