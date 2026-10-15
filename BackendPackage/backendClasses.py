#backendClasses.py  Copyright (C) 2024  Valparaiso University

import smtplib, ssl #standard lib
import html #standard lib
import mimetypes #standard lib
import os #standard lib
import re #standard lib
import time #standard lib
from email.message import EmailMessage #standard lib
from email.utils import formataddr #standard lib
import pandas as pd #pandas
from pathlib import Path #pathlib

#Admissions info added to the email for visitors without a valpo.edu address
ADMISSION_APPLY_URL = "https://www.valpo.edu/apply-to-valpo/"
ADMISSION_VISIT_URL = "https://www.valpo.edu/admission/visit/"
ADMISSION_EMAIL = "undergrad.admission@valpo.edu"
#(short name, url)
VALPO_COLLEGES = [
    ("Arts & Sciences", "https://www.valpo.edu/college-of-arts-and-sciences/"),
    ("Business", "https://www.valpo.edu/college-of-business/"),
    ("Engineering", "https://www.valpo.edu/college-of-engineering/"),
    ("Nursing & Health", "https://www.valpo.edu/college-of-nursing-and-health-professions/"),
]

def isValpoEmail(address):
    """Returns True if address is a Valparaiso University (@valpo.edu) email address"""
    return address.strip().lower().endswith("@valpo.edu")

class MailController:
    """Functions:
        sendMessage(title, body, destEmail, folderKey)
            Non valpo.edu recipients also get the admissions section
    """
    def __init__(self, email, password, senderName="Photobooth"):
        self.email = email
        self.password = password
        self.senderName = senderName

    #Times to try sending an email before giving up, and seconds to wait between tries
    SEND_ATTEMPTS = 3
    RETRY_DELAY = 5

    #Valparaiso University brand colors
    VALPO_BROWN = "#5C3000"
    VALPO_DARK_BROWN = "#331A00"
    VALPO_GOLD = "#F5B80A"

    def _buildAdmissionHtml(self):
        """Builds the short admissions section: a big Apply Now button and links to the four colleges"""
        brown, darkBrown, gold = self.VALPO_BROWN, self.VALPO_DARK_BROWN, self.VALPO_GOLD
        chip = f"display:block;background-color:#ffffff;color:{brown};text-decoration:none;text-align:center;border-radius:6px;padding:12px 2px;font-size:13px;font-weight:bold;white-space:nowrap;"
        #Colleges as a 2 x 2 grid of buttons
        rows = []
        for i in range(0, len(VALPO_COLLEGES), 2):
            cells = "".join(
                f'<td width="50%" style="padding:4px;"><a href="{url}" style="{chip}">{html.escape(name)}</a></td>'
                for name, url in VALPO_COLLEGES[i:i + 2]
            )
            rows.append(f"<tr>{cells}</tr>")
        colleges = "".join(rows)
        return f"""\
            <tr>
              <td style="padding:8px 32px 28px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{brown};border-radius:8px;">
                  <tr>
                    <td align="center" style="padding:28px 24px 8px 24px;">
                      <p style="margin:0 0 6px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{gold};font-weight:bold;">Picture yourself here</p>
                      <h2 style="margin:0 0 8px 0;font-size:28px;line-height:1.15;color:#ffffff;">Your next photo could be on campus.</h2>
                      <p style="margin:0 0 20px 0;font-size:15px;line-height:1.5;color:#f0e2cf;">Find your path at Valpo. Start your application today.</p>
                      <a href="{ADMISSION_APPLY_URL}" style="display:block;background-color:{gold};color:{darkBrown};text-decoration:none;text-align:center;border-radius:8px;padding:18px;font-size:20px;font-weight:bold;letter-spacing:1px;">APPLY NOW &rarr;</a>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:16px 20px 4px 20px;">
                      <p style="margin:0 0 4px 0;text-align:center;font-size:13px;color:#f0e2cf;">Explore our colleges</p>
                      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{colleges}</table>
                    </td>
                  </tr>
                  <tr>
                    <td align="center" style="padding:12px 24px 22px 24px;font-size:13px;color:#f0e2cf;">
                      <a href="{ADMISSION_VISIT_URL}" style="color:{gold};font-weight:bold;">Visit campus</a>
                      &nbsp;&middot;&nbsp;
                      <a href="mailto:{ADMISSION_EMAIL}" style="color:{gold};font-weight:bold;">Questions?</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
"""

    def _buildAdmissionText(self):
        """Plain text version of the admissions section, for email clients that don't show HTML"""
        lines = ["", "", "Picture yourself at Valpo! Start your application today.",
                 "APPLY NOW: " + ADMISSION_APPLY_URL, "", "Explore our colleges:"]
        lines += [f"- {name}: {url}" for name, url in VALPO_COLLEGES]
        lines += ["", "Visit campus: " + ADMISSION_VISIT_URL, "Questions? " + ADMISSION_EMAIL]
        return "\n".join(lines)

    def _buildHtml(self, title, body, photoCount, includeAdmission=False):
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
{self._buildAdmissionHtml() if includeAdmission else ''}            <tr>
              <td style="background-color:{darkBrown};padding:16px 32px;font-size:12px;color:#d9c9b8;">
                Go Beacons! Sent from the Valpo photo booth.
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
        #Visitors without a valpo.edu address also get the admissions section
        includeAdmission = not isValpoEmail(destEmail)
        message.set_content(body + self._buildAdmissionText() if includeAdmission else body)
        message.add_alternative(self._buildHtml(title, body, len(images), includeAdmission), subtype="html")

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

        #Send email, retrying on a fresh connection if the upload stalls or drops partway
        for attempt in range(1, self.SEND_ATTEMPTS + 1):
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=60) as server:
                    server.login(self.email, self.password)
                    server.send_message(message)
                return True
            except (smtplib.SMTPException, OSError) as e:
                print(f"ERROR SENDING EMAIL (attempt {attempt} of {self.SEND_ATTEMPTS}): {e}")
                if attempt < self.SEND_ATTEMPTS:
                    time.sleep(self.RETRY_DELAY)
        return False

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
        #First successful read (sheet was unreachable at startup); use it as the baseline
        if(self.currentData is None):
            self.currentData = df2
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
                email.append(str(entry[1]).strip())
                folderId.append(str(entry[2]).strip().upper())
            return email, folderId
        except:
            print("Sheet Emptied")
            email.append(" ")
            folderId.append(" ")
            return email, folderId
