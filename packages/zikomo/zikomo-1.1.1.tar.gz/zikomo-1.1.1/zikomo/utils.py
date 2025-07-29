import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

import smtplib
import random
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import subprocess
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from zikomo.constants import *

SLACK_CHANNEL_ID_IMRAN="U066S4TAPJS"
SLACK_CHANNEL_ID_GENERAL="C066YLPB62F"
IMAGE_HOST_URL = "https://zikomo.azureedge.net/media/general/images/"

SSH_HOSTS = {
    "staging": "staging",
    "uat": "uat",
    "prod": "prod"
}

def run(cmd, cwd=None):
    print(f"\n🔹 {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True,encoding='utf-8',errors='replace', cwd=cwd)
    
    if result.returncode != 0:
        if not "closed by remote host" in result.stderr.strip() :            
            print("❌ ERROR:", result.stderr.strip())
            print(f"Command failed: {cmd}")
            raise Exception(f"Command failed: {cmd}")
    
    return result.stdout.strip()

def get_random_image_url(env):    
    chosen = random.randint(1, 7)
    image=f"{IMAGE_HOST_URL}{env}/{chosen}.png"
    
    return image

def get_docs_url(env,project):
    current_env=env.lower() if env.lower()!="prod" else "production"
    return f"https://developers.zikomosolutions.com/api/releases/{project}/{current_env}-2025/"

def get_project_site_url(env,project):
    match project.lower():     
        case "backoffice":
            if env.lower()=="staging" :
                return "https://mini.staging.zikomo.io"     
            if env.lower()=="uat":
                return "https://mini.uat.zikomo.io"    
            if  env.lower()=="prod":
                return "https://manage.zikomosolutions.com"
        
        case "websites":
            if env.lower()=="staging":
                return "https://demo.staging.zikomo.io"    
            if env.lower()=="uat":
                return "https://demo.uat.zikomo.io"    
            if env.lower()=="prod":
                return "https://superescapes.co.uk"
            
        case "flightbite":
            if env.lower()=="staging":
                return "https://flightbite.staging.zikomo.io"    
            if env.lower()=="uat":
                return "https://flightbite.uat.zikomo.io"    
            if env.lower()=="prod":
                return "https://flightbite.zikomosolutions.com"

def send_slack(env,project, version, slack_text, image_url,channel_id):
    SLACK_TOKEN="xoxb-6233873111973-8582839710000-PjZ3ZEpVPI1ytaDQ1o3wkeb2"
    now = datetime.now()
    current_date = now.strftime("%d-%b-%Y")  
    current_time = now.strftime("%I:%M %p") 
    
    client = WebClient(token=SLACK_TOKEN)
    
    slack_text = slack_text.replace("• •"," • ")
    slack_text = slack_text.replace("• -", "• ")
    slack_text = slack_text.replace("**", "*")

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"{env.upper()} Updated: {version} - {slack_text}", 
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f":loudspeaker: {env.upper()} UPDATED"
                    }
                },
                {
                    "type": "section",                    
                    "fields": [
                        {"type": "mrkdwn","text": f":spiral_calendar_pad: {current_date}"},
                        {"type": "mrkdwn","text": f":clock1: {current_time}"},                                                
                    ]
                },
                {
                    "type": "section",                    
                    "fields": [                        
                        {"type": "mrkdwn","text": f":gear: {project}"},
                        {"type": "mrkdwn","text": f":1234: {version}"},
                    ]
                },
                {"type": "divider"},                
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": "Update image"
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Following features and fixes have been published in this release:*"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": slack_text}
                },
                {
                    "type": "actions",
                    "block_id": "actionblock789",
                    "elements": [                        
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text":f":scroll: Visit {project} docs"
                            },
                            "url": get_docs_url(env,project)
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text":f":globe_with_meridians: Visit {project}"
                            },
                            "url": get_project_site_url(env,project)
                        }
                    ]
                }
            ]
        )
        print("Message sent:", response["ts"])
    except SlackApiError as e:
        print("Error:", e.response)      

# MAIL
def get_email_template(env, version, pr_text, project):
    pr_text = pr_text.replace("• •", "• ")
    pr_text = pr_text.replace("• -", "• ")
    pr_text = pr_text.replace("**", "")
    pr_text = pr_text.replace("\n", "<br>")
    
    now = datetime.now()
    current_date = now.strftime("%d-%b-%Y")  
    current_time = now.strftime("%I:%M %p") 
    
    _dir = Path(__file__).parent.resolve()
    file_path = _dir / 'email_template.html'

    #file_path = os.path.abspath('./email_template.html')
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    message = f"{env.upper()} Updated: {version}" 
    html = html.replace("{message}", message)   
    html = html.replace("{environment}", env.upper())
    html = html.replace("{version}", version)
    html = html.replace("{pr_text}", pr_text)
    html = html.replace("{date}", current_date)
    html = html.replace("{time}", current_time)
    html = html.replace("{project}", project)

    return html

def send_email(env, version, pr_text, project):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{env.upper()} Deployment: {version}"
    msg["From"] = EMAIL_SETTINGS["sender"] # type: ignore
    msg["To"] = ", ".join(EMAIL_SETTINGS["receiver"]) # type: ignore

    html = get_email_template(env, version, pr_text, project)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(EMAIL_SETTINGS["smtp_server"], EMAIL_SETTINGS["smtp_port"]) as server: # type: ignore
        server.starttls()
        server.login(EMAIL_SETTINGS["username"], EMAIL_SETTINGS["password"])
        server.sendmail(EMAIL_SETTINGS["sender"], EMAIL_SETTINGS["receiver"], msg.as_string())
    
    print(f"📧 Email sent to {', '.join(EMAIL_SETTINGS['receiver'])} for {env.upper()} deployment: {version}")  # type: ignore