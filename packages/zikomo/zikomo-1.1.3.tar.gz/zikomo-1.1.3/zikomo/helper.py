import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

import json
import re
import argparse
from datetime import datetime
from zikomo.constants import *
from zikomo.utils import run, send_slack, send_email, get_random_image_url,get_docs_url, get_project_site_url,SSH_HOSTS, SLACK_CHANNEL_ID_IMRAN,SLACK_CHANNEL_ID_GENERAL
from zikomo.git_utils import *
from zikomo.discord_bot import send_discord_message

# -------------------- CONFIG --------------------
image = ""
image_latest = ""
# ------------------------------------------------

def build_and_push_docker(image, image_latest, version):
    tag = version.replace("v", "")
    
    run(f"docker build -t {image_latest} -t {image} --build-arg VERSION={tag} .")
    run("az acr login --name zikomo")
    run(f"docker push {image}")
    run(f"docker push {image_latest}")

# DEPLOY
def deploy_to_server(env):
    host = SSH_HOSTS[env]
    cmd = f"sudo docker compose -f /var/www/mini/mini-stack.yml pull && sudo docker compose -f /var/www/mini/mini-stack.yml up -d"
    cmd_prune="sudo docker image prune -f"
    
    run(f'ssh {host} "{cmd}"')
    run(f'ssh {host} "{cmd_prune}"')

def log_release(version, image, pr_list, remarks):
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%I:%M %p")
    pr_str = ",".join(pr_list)
    
    #remarks=remarks.replace("\r\n"," • ")
    #remarks=remarks.replace("• •"," • ")
    #remarks=remarks.replace("• -"," • ")
    remarks = re.sub(r'[\r\n]+', ' • ', remarks)
    remarks = re.sub(r'\s*•\s*•\s*', ' • ', remarks)
    remarks = re.sub(r'\s*•\s*-\s*', ' • ', remarks)
    remarks = remarks.strip()

    row = f"| {date} | {time} | {image} | {version} | {pr_str} |{remarks} |\n"
    
    with open(RELEASE_DOCS_FILE, "a", encoding="utf-8") as f:
        f.write(row)
    
    print(f"📝 Appended release info to {RELEASE_DOCS_FILE}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--uat", action="store_true")
    parser.add_argument("--prod", action="store_true")
    return parser.parse_args()

def update_docs_site():
    os.chdir("E:\\ZikomoSolutions\\Projects\\ZikomoDocs\\developer-docs")
    
    run("git add .")
    run(f'git commit -m "info"')
    run("git push")
    run("mkdocs build")
    run("netlify deploy --prod --dir=site")

def set_docs_path(env,project):
    global RELEASE_DOCS_FILE    

    if env=="staging":
        RELEASE_DOCS_FILE=f"E:\\ZikomoSolutions\\Projects\\ZikomoDocs\\developer-docs\\docs\\api\\releases\\{project}\\staging-2025.md"
    elif env=="uat":
        RELEASE_DOCS_FILE=f"E:\\ZikomoSolutions\\Projects\\ZikomoDocs\\developer-docs\\docs\\api\\releases\\{project}\\uat-2025.md"
    else:
        RELEASE_DOCS_FILE=f"E:\\ZikomoSolutions\\Projects\\ZikomoDocs\\developer-docs\\docs\\api\\releases\\{project}\\production-2025.md"

def switch_dir(project):        
    match project.lower():
        case "flightbite":
          os.chdir(FLIGHTBITE_DIR)                          
          
        case "backoffice":
          os.chdir(BACKOFFICE_DIR)           
                       
        case "websites":
          os.chdir(WEBSITES_DIR) 
          
def set_version(env,project):
    global image,image_latest
    
    version=get_next_version(env)
    tag = version.replace("v", "")
    
    match project.lower():
        case "flightbite":                         
          image = f"{FLIGHTBITE_REGISTRY}:{tag}"
          image_latest = f"{FLIGHTBITE_REGISTRY}:{env}-latest"
          
        case "backoffice":          
          image = f"{BACKOFFICE_REGISTRY}:{tag}"
          image_latest = f"{BACKOFFICE_REGISTRY}:{env}-latest"
                       
        case "websites":          
          image = f"{WEBSITES_REGISTRY}:{tag}"
          image_latest = f"{WEBSITES_REGISTRY}:{env}-latest"                           
    
    return version

# MAIN WORKFLOW
def main_deploy(env,project):
    global image,image_latest
    
    switch_dir(project)            
    version = set_version(env,project)    
    print(f"\n🚀 Releasing to {env.upper()}: {version}")

    pr_nums, notes_text, remarks_text, slack_md = get_and_merge_prs(env)
    if not pr_nums:
        print("✅ All caught up! No PRs to deploy.")
        return
    
    git_sync()
    create_release(version)
    build_and_push_docker(image, image_latest, version)
    deploy_to_server(env)
    
    # LOG TO RELEASE NOTES
    set_docs_path(env,project)
    log_release(version, image, pr_nums, remarks_text)

    print("\n📚 Updating developer docs...")
    update_docs_site()
    
    # NOTIFY
    print("\n📢 Sending notifications...")
    image_url = get_random_image_url(env.lower())
    
    send_slack(env,project, version, notes_text, image_url or "",SELECTED_SLACK_CHANNEL_ID)
    send_email(env, version, notes_text, project)
    send_discord_message(
        env,
        project_name=project,
        version=version,        
        update_points=notes_text,
        image_url=image_url,
        docs_url=get_docs_url(env,project),
        site_url=get_project_site_url(env,project)        
    )
        
    print(f"\n✅ {project} with {version} deployed to {env}.")
    
if __name__ == "__main__":    
    #main_deploy("staging","websites")
    update_docs_site()
    #send_slack("Staging", "123", "1.Point1\r\n2.point2", IMAGE_HOST_URL+"staging/2.png")
    