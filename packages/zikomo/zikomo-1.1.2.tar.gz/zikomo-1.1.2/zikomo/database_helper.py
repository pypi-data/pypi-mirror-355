import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

import subprocess
from datetime import datetime
from pathlib import Path
from zikomo.discord_bot import send_discord_message
from zikomo.constants import *
from zikomo.utils import (
    run, send_slack, send_email, get_random_image_url,
    get_docs_url, get_project_site_url,
    SSH_HOSTS, SLACK_CHANNEL_ID_IMRAN)

def generate_schema_script(project_name: str, startup_project: str, db_context: str, output_dir: str) -> Path | None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"script_{project_name}_{timestamp}.sql"
    file_path = Path(output_dir) / file_name

    # dotnet ef command to generate SQL
    command = [
        "dotnet", "ef", "migrations", "script",
        "-s", startup_project,
        "-p", project_name,
        "-c", db_context,
        "--output", str(file_path),
        "--idempotent"
    ]

    print(f"📜 Generating migration script for `{project_name}` → {file_path.name}")

    result = subprocess.run(
        command,
        check=True,
        cwd=SOLUTION_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print("❌ Error generating migration script:")
        print(result.stderr)
        return None

    # 🚫 Remove BOM if present
    if file_path.exists():
        with open(file_path, "rb") as f:
            content = f.read()
        bom = b'\xef\xbb\xbf'
        if content.startswith(bom):
            print("🚫 BOM found in SQL file, removing it...")
            content = content[len(bom):]
            with open(file_path, "wb") as f:
                f.write(content)
            print("✅ BOM removed successfully.")

    print(f"✅ Migration script generated at: {file_path}")
    return file_path

def apply_to_postgres(file_path: Path, db_name: str, db_user: str = "postgres", db_host: str = "localhost", db_port: int = 5432, db_password: str = ""):
    os.environ["PGPASSWORD"] = db_password

    # psql command to run the SQL script
    command = [
        "psql",
        f"--dbname={db_name}",
        f"--host={db_host}",
        f"--port={str(db_port)}",
        f"--username={db_user}",
        "-f", str(file_path)
    ]
    
    print(f"🔄 Applying script to `{db_name}`...")
    result = subprocess.run(command)

    if result.returncode != 0:
        print("❌ Failed to apply schema to Postgres.")
    else:
        print(f"✅ Schema successfully applied to {db_name}.\n")

def restart_server(env): 
    host = SSH_HOSTS[env]   
    cmd = f"sudo reboot"    
    try:
        run(f'ssh {host} "{cmd}"')
    except Exception as e:
        #print(f"❌ Error restarting server on {host}: {e}")
        pass
    
    print(f"🖥️  Server restarted successfully on {host}.")
    
def restart_containers(env): 
    host = SSH_HOSTS[env]   
    cmd = f"sudo docker compose -f /var/www/mini/mini-stack.yml restart mini frontends"
    cmd_prune="sudo docker image prune -f"
    
    run(f'ssh {host} "{cmd}"')
    run(f'ssh {host} "{cmd_prune}"')
    print(f"🖥️  Containers restarted successfully on {host}.")
    
def update_schema_flow(target,env):    
    db_name = ""
    db_user = "developer"    
    db_password = "Developer#8087"
    db_context=""
    db_host=""
    db_port=5432
    project_name=""    
    client_databases=[
        "ZikomoMini.BaseClient",
        "ZikomoMini.HolidayBuzz", 
        "ZikomoMini.BOH",
        "ZikomoMini.SuperEscapes",
        "ZikomoMini.TAYL"
        ]
    
    if target.lower() in ["log database","logs database"]:
        project_name = "Zikomo.Logs.Database"
        db_name="ZikomoMini.LogsMaster"
        db_context = "DatabaseContextLogs"
        output_dir=OUTPUT_DIR+"\\Logs"

    if target.lower()=="master database":
        project_name = "Zikomo.Main.Database"
        db_context="DatabaseContextMain"
        db_name="ZikomoMini.Master"
        output_dir=OUTPUT_DIR+"\\Master"
            
    # clients
    if target.lower()=="client database":
        project_name = "Zikomo.Client.Database"
        db_context="DatabaseContextClient"
        output_dir=OUTPUT_DIR+"\\Client"

    if env.lower()=="staging":
        db_host = "mini.staging.zikomo.io"
        db_port = 5432
    
    if env.lower()=="uat":
        db_host = "mini.uat.zikomo.io"
        db_port = 5432
        
    if env.lower()=="prod" or env.lower()=="production":
        db_host = "manage.zikomosolutions.com"
        db_port = 5435
    
    # ⚙️ Generate and apply
    os.chdir(PROJECT_DIR)    
    file_path = generate_schema_script(project_name, STARTUP_PROJECT, db_context, OUTPUT_DIR)
    
    
    if file_path:
        if target.lower()=="client database":
            for client_db in client_databases:
                apply_to_postgres(file_path, client_db, db_user, db_host, db_port, db_password)
        else:
            apply_to_postgres(file_path, db_name, db_user, db_host, db_port, db_password)
        
        # DELETE FILE
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️  Deleted temporary file: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")
            
        # RESTART
        restart_containers(env)
        
        # NOTIFY
        image_url = get_random_image_url(env)
        message="Schema applied to the database"
        
        send_slack(env,"Backoffice", project_name, message, image_url,SLACK_CHANNEL_ID_IMRAN)
        send_email(env, project_name, message, "Backoffice")
        send_discord_message(
        env,
        project_name="Backoffice",
        version=project_name,        
        update_points=message,
        image_url=image_url,
        docs_url=get_docs_url(env,project_name),
        site_url=get_project_site_url(env,project_name)        
    )
if __name__ == "__main__":
    #update_schema_flow("master database","staging")
    update_schema_flow("logs database","staging")
    #update_schema_flow("client database","staging")
    #image_url = get_random_image_url("staging")   
    #send_slack("Staging","Backoffice", "version", "notes_text", image_url or "",SLACK_CHANNEL_ID_IMRAN)
    #send_email("Staging", "Database", "1. Schema applied to database\n2. Point2", "Backoffice")
