import subprocess
import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

from zikomo.database_helper import update_schema_flow
from zikomo.constants import SOLUTION_ROOT

EF_PROJECTS = [
    "Zikomo.Logs.Database",
    "Zikomo.Main.Database",
    "Zikomo.Client.Database"
]

def run_cmd(cmd, cwd=SOLUTION_ROOT):
    print(" 🔹 Running command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True)
    return result.stdout.strip()

import re

def get_last_two_tags(env: str) -> tuple[str, str]:
    run_cmd(["git", "fetch", "--tags"])
    cmd = ["gh", "release", "list", "-L", "20"]
    output = run_cmd(cmd)
    lines = output.splitlines()

    # Match: v1.2.3-staging and extract version "1.2.3"
    pattern = re.compile(r"^(v(\d+\.\d+\.\d+)-" + re.escape(env) + r")\b")

    matched = []
    for line in lines:
        match = pattern.match(line)
        if match:
            full_tag = match.group(1)  # e.g., v1.2.3-staging
            version_str = match.group(2)  # e.g., 1.2.3
            numeric_key = int(version_str.replace(".", ""))  # e.g., 123
            matched.append((numeric_key, full_tag))

    if len(matched) < 2:
        raise ValueError(f"Not enough GitHub releases found for environment: {env}")

    matched.sort(key=lambda x: x[0])
    return matched[-2][1], matched[-1][1]


def has_new_migrations(project_path: str, old_tag: str, new_tag: str|None) -> bool:
    project_path = project_path.replace("\\", "/").rstrip("/")
    migrations_folder = f"{project_path}/Migrations"

    cmd = ["git", "diff", "--name-status", old_tag, new_tag]
    
    changes = run_cmd(cmd).splitlines()
    for line in changes:
        parts = line.split('\t', 1)
        if len(parts) == 2:
            status, file = parts
            if status == "A" and file.startswith(migrations_folder) and file.endswith(".cs"):
                print(f"🟢 Found new migration in {project_path}: {file}")
                return True
    return False

def apply_migrations(project_path: str,env: str):
    print(f"⚙️  Applying migrations for: {project_path}")
    
    match project_path:
        case "Zikomo.Logs.Database":
            update_schema_flow("log database",env)
            
        case "Zikomo.Main.Database":
            update_schema_flow("master database",env)
        
        case "Zikomo.Client.Database":
            update_schema_flow("client database",env)
       
        case _:
            raise ValueError(f"Unknown project: {project_path}")

def migrate_database(env: str):
    if env.lower() in ["live","prod", "production"]:
        env="release"
        
    try:
        prev_tag, latest_tag = get_last_two_tags(env)
        print(f"🔍 Checking changes from {prev_tag} → {latest_tag}")
    except ValueError as e:
        print(f"⚠️ {e} — applying all migrations as fallback.")
        prev_tag = None
        latest_tag = None

    any_applied = False
    for project in EF_PROJECTS:
        try:
            if prev_tag is None or has_new_migrations(project, prev_tag, latest_tag):
                apply_migrations(project,env.lower())
                any_applied = True
            else:
                print(f"✅ No new migrations in {project}")
        except Exception as e:
            print(f"❌ Error checking/applying migrations for {project}: {e}")

    if not any_applied:
        print("✅ No new migrations found in any project.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deploy.py <env>")
        print("Example: python deploy.py staging")
        sys.exit(1)

    migrate_database(sys.argv[1])
