import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

import argparse
from zikomo.helper import main_deploy
from zikomo.database_helper import update_schema_flow,restart_server
from zikomo.utils import send_email
from zikomo.migrate_db import migrate_database

VALID_PROJECTS = ["backoffice", "websites", "flightbite"]
VALID_UPDATE_TARGETS = ["master database","log database","logs database","client database"]
VALID_ENVS = {
    "staging": "staging",
    "uat": "uat",
    "production": "prod",
    "prod": "prod",
    "live": "prod",
    "release": "prod",
    
}

VALID_PREPOSITIONS = ["to", "on"]
VALID_SERVERS = ["server"]

def deploy(env, project):
    print(f"🚀 Deploying '{project}' to environment '{env}'")
    main_deploy(env, project)

# Check if new migrations exist between two latest tags and then update the database
def migrate_db(target, env):
    print(f"🔄 Checking migrations & updating '{target}' on '{env}'")
    migrate_database(env)    

# Directly update the database schema
def update_database(target, env):
    print(f"🔄 Updating '{target}' on '{env}'")
    update_schema_flow(target,env)    
    #send_email("Staging", "Database", "1. Schema applied to database\n2. Point2", "Backoffice")

def reboot_server(env, server):
    print(f"🔄 Rebooting '{server}' on '{env}'")
    restart_server(env)
    
    
def main():
    parser = argparse.ArgumentParser(prog="mini", description="Zikomo Mini CLI Assistant, developed by Imran A. Shah")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a project")
    deploy_parser.add_argument("project", choices=VALID_PROJECTS, help="Project to deploy")
    deploy_parser.add_argument("preposition", choices=VALID_PREPOSITIONS, help="'to' or 'on'")
    deploy_parser.add_argument("environment", choices=VALID_ENVS.keys(), help="Target environment")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update client systems")
    update_parser.add_argument("target", nargs=2, help="Update target (e.g., client database)")
    update_parser.add_argument("preposition", choices=VALID_PREPOSITIONS, help="'to' or 'on'")
    update_parser.add_argument("environment", choices=VALID_ENVS.keys(), help="Target environment")

    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Check if new migrations exist and update the database")
    migrate_parser.add_argument("target", nargs=2, help="Migrate target (e.g., client database)")
    migrate_parser.add_argument("preposition", choices=VALID_PREPOSITIONS, help="'to' or 'on'")
    migrate_parser.add_argument("environment", choices=VALID_ENVS.keys(), help="Target environment")

    # Reboot command
    reboot_parser = subparsers.add_parser("reboot", help="Reboot a server")
    reboot_parser.add_argument("environment", choices=VALID_ENVS.keys(), help="Target environment")
    reboot_parser.add_argument("server", choices=VALID_SERVERS, help="Server to reboot")

    args = parser.parse_args()

    #COMMAND: deploy
    if args.command == "deploy":
        env = VALID_ENVS[args.environment.lower()]
        deploy(env, args.project)

    #COMMAND: update
    elif args.command == "update":
        env = VALID_ENVS[args.environment.lower()]
        target = " ".join(args.target).lower()
        
        if target not in VALID_UPDATE_TARGETS:
            print(f"❌ Unsupported update target: '{target}'")
            return
        
        update_database(target, env)
    #COMMAND: migrate
    elif args.command == "migrate":
        env = VALID_ENVS[args.environment.lower()]
        target = " ".join(args.target).lower()
        
        if target not in VALID_UPDATE_TARGETS:
            print(f"❌ Unsupported migrate target: '{target}'")
            return

        migrate_db(target, env)

    elif args.command == "reboot":
        env = VALID_ENVS[args.environment.lower()]
        reboot_server(env, args.server)

# MAIN
if __name__ == "__main__":
    main()
