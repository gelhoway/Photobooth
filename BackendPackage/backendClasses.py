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

#Admissions info added to the email for visitors without a valpo.edu address
ADMISSION_APPLY_URL = "https://www.valpo.edu/apply-to-valpo/"
ADMISSION_VISIT_URL = "https://www.valpo.edu/admission/visit/"
ADMISSION_INFO_URL = "https://www.valpo.edu/admission/"
ADMISSION_PROGRAMS_URL = "https://www.valpo.edu/academics/find-your-program/"
ADMISSION_EMAIL = "undergrad.admission@valpo.edu"
ADMISSION_PHONE = "219.464.5011"
#(name, link label, url, description)
VALPO_COLLEGES = [
    ("College of Arts and Sciences", "Arts & Sciences",
     "https://www.valpo.edu/college-of-arts-and-sciences/",
     "Sciences, humanities, social sciences, and the arts, from biology and psychology to music and communication."),
    ("College of Business", "Business",
     "https://www.valpo.edu/college-of-business/",
     "Accounting, finance, management, marketing, and more. AACSB-accredited, a distinction held by the top 5% of business schools worldwide."),
    ("College of Engineering", "Engineering",
     "https://www.valpo.edu/college-of-engineering/",
     "Bioengineering, civil, computer, electrical, and mechanical engineering, with hands-on design projects from your first year."),
    ("College of Nursing and Health Professions", "Nursing & Health",
     "https://www.valpo.edu/college-of-nursing-and-health-professions/",
     "Nursing, public health, and other paths into healthcare. Nursing is direct-admit, so you start in your major on day one."),
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

    #Valparaiso University brand colors
    VALPO_BROWN = "#5C3000"
    VALPO_DARK_BROWN = "#331A00"
    VALPO_GOLD = "#F5B80A"

    def _buildAdmissionHtml(self):
        """Builds the admissions section: quick links, the four colleges, and how to apply"""
        brown, darkBrown, gold = self.VALPO_BROWN, self.VALPO_DARK_BROWN, self.VALPO_GOLD
        outlineButton = f"display:block;background-color:#ffffff;color:{brown};text-decoration:none;text-align:center;border:2px solid {brown};border-radius:6px;padding:12px 6px;font-size:15px;font-weight:bold;"
        colleges = "".join(f"""
                <a href="{url}" style="display:block;text-decoration:none;color:#333333;margin-bottom:12px;">
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e6d9c8;border-top:5px solid {gold};border-radius:6px;">
                    <tr>
                      <td style="padding:16px 18px;">
                        <p style="margin:0 0 4px 0;font-size:17px;font-weight:bold;color:{brown};">{html.escape(name)}</p>
                        <p style="margin:0 0 12px 0;font-size:14px;line-height:1.45;color:#444444;">{html.escape(description)}</p>
                        <span style="display:inline-block;background-color:{brown};color:#ffffff;border-radius:4px;padding:8px 14px;font-size:14px;font-weight:bold;">Explore {html.escape(label)} &rarr;</span>
                      </td>
                    </tr>
                  </table>
                </a>"""
            for name, label, url, description in VALPO_COLLEGES
        )
        step = f"display:inline-block;width:26px;height:26px;line-height:26px;text-align:center;border-radius:13px;background-color:{gold};color:{darkBrown};font-weight:bold;"
        return f"""\
            <tr>
              <td style="padding:20px 32px 8px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td width="33%" style="padding:0 4px 0 0;">
                      <a href="{ADMISSION_APPLY_URL}" style="display:block;background-color:{brown};color:#ffffff;text-decoration:none;text-align:center;border-radius:6px;padding:14px 6px;font-size:15px;font-weight:bold;">Apply</a>
                    </td>
                    <td width="33%" style="padding:0 2px;">
                      <a href="{ADMISSION_VISIT_URL}" style="{outlineButton}">Visit</a>
                    </td>
                    <td width="33%" style="padding:0 0 0 4px;">
                      <a href="{ADMISSION_INFO_URL}" style="{outlineButton}">Get Info</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 4px 32px;">
                <h2 style="margin:0;font-size:20px;color:{brown};">Find your college</h2>
                <p style="margin:4px 0 0 0;font-size:14px;color:#666666;">Tap any college to explore its programs.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:12px 32px 0 32px;">{colleges}
              </td>
            </tr>
            <tr>
              <td style="padding:4px 32px 8px 32px;">
                <a href="{ADMISSION_PROGRAMS_URL}" style="display:block;text-decoration:none;background-color:#faf6f0;border:1px dashed {brown};border-radius:6px;padding:14px 18px;color:{brown};font-size:15px;">
                  <strong>Not sure yet?</strong> Browse every major and program &rarr;
                </a>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 4px 32px;">
                <h2 style="margin:0;font-size:20px;color:{brown};">Applying is easy</h2>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 32px 0 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:15px;line-height:1.45;">
                  <tr>
                    <td width="36" valign="top" style="padding:6px 0;"><span style="{step}">1</span></td>
                    <td style="padding:6px 0;"><a href="{ADMISSION_APPLY_URL}" style="color:{brown};font-weight:bold;">Start your online application</a></td>
                  </tr>
                  <tr>
                    <td width="36" valign="top" style="padding:6px 0;"><span style="{step}">2</span></td>
                    <td style="padding:6px 0;">Ask your school counselor to send your transcript</td>
                  </tr>
                  <tr>
                    <td width="36" valign="top" style="padding:6px 0;"><span style="{step}">3</span></td>
                    <td style="padding:6px 0;"><a href="{ADMISSION_VISIT_URL}" style="color:{brown};font-weight:bold;">Schedule a campus tour</a> and meet us in person</td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:24px 32px 8px 32px;">
                <a href="{ADMISSION_APPLY_URL}" style="display:block;background-color:{gold};color:{darkBrown};text-decoration:none;text-align:center;border-radius:6px;padding:16px;font-size:18px;font-weight:bold;">Apply to Valpo &rarr;</a>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:8px 32px 28px 32px;font-size:14px;color:#555555;line-height:1.6;">
                Questions? We're happy to help.<br>
                <a href="mailto:{ADMISSION_EMAIL}" style="color:{brown};font-weight:bold;">{ADMISSION_EMAIL}</a>
                &nbsp;&middot;&nbsp;
                <a href="tel:+1{ADMISSION_PHONE.replace('.', '')}" style="color:{brown};font-weight:bold;">{ADMISSION_PHONE}</a>
              </td>
            </tr>
"""

    def _buildAdmissionText(self):
        """Plain text version of the admissions section, for email clients that don't show HTML"""
        lines = ["", "", "Thinking about college? Explore Valparaiso University's four colleges:", ""]
        for name, label, url, description in VALPO_COLLEGES:
            lines += [name, description, url, ""]
        lines += [
            "Not sure yet? Browse every major and program: " + ADMISSION_PROGRAMS_URL,
            "",
            "Applying is easy:",
            "1. Start your online application: " + ADMISSION_APPLY_URL,
            "2. Ask your school counselor to send your transcript",
            "3. Schedule a campus tour: " + ADMISSION_VISIT_URL,
            "",
            "Questions? " + ADMISSION_EMAIL + " / " + ADMISSION_PHONE,
        ]
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

        #Send email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=60) as server:
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
