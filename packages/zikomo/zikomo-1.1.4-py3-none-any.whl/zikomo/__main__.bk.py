import argparse
from .helper import main_deploy,send_slack,IMAGE_HOST_URL

VALID_PROJECTS = ["backoffice", "websites","flightbite"]

def deploy(env, project):
    print(f"🚀 Deploying '{project}' to environment '{env}'")
    #main_deploy(env,project)
    #send_slack("Staging",project, "v1.2.3-staging", "1.Point1\r\n2.point2", IMAGE_HOST_URL+"staging/2.png")
    
def main():
    parser = argparse.ArgumentParser(prog="zikomo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    deploy_parser = subparsers.add_parser("deploy", help="Deploy a project")
    
    env_group = deploy_parser.add_mutually_exclusive_group(required=True)
    env_group.add_argument("--staging", action="store_true")
    env_group.add_argument("--uat", action="store_true")
    env_group.add_argument("--production", action="store_true")
    
    # Project with validation
    deploy_parser.add_argument(
        "--project", 
        required=True, 
        choices=VALID_PROJECTS,
        help=f"Project name (valid: {', '.join(VALID_PROJECTS)})"
    )

    args = parser.parse_args()

    env = "staging" if args.staging else "uat" if args.uat else "prod"
    
    if args.command == "deploy":
        deploy(env, args.project)

#MAIN
if __name__ == "__main__":
    main()
