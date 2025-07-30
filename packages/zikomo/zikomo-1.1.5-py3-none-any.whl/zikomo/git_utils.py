import time
import json
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))

from zikomo.constants import BACKOFFICE_DIR,WEBSITES_DIR
from zikomo.utils import run

def get_latest_tag(tag_prefix):      
    try:        
        result=run("gh release list --limit 100")

        lines = result.splitlines()

        for line in lines:
            parts = line.split()
            if parts and parts[0].endswith(tag_prefix):
                return parts[0]

        return None  # No matching tag found
    except subprocess.CalledProcessError as e:
        print("Error running gh:", e)
        return None

def get_next_version(env):
    current_env=env if env.lower()!="prod" else "release"
    output = run("gh release list --limit 50")
    tags = [line.split()[0] for line in output.splitlines()]
    env_tags = [t for t in tags if re.match(rf"v\d+\.\d+\.\d+-{current_env}", t)]
    
    if not env_tags:
        print(f'Releases not found for {env}!')
        return f"v0.0.1-{env}"

    def numeric_version(tag):
        m = re.match(r"v(\d+)\.(\d+)\.(\d+)-", tag)
        if not m:
            return 0
        a, b, c = map(int, m.groups())
        return a * 100 + b * 10 + c

    latest_tag = max(env_tags, key=numeric_version)
    next_version_num = numeric_version(latest_tag) + 1

    a = next_version_num // 100
    b = (next_version_num // 10) % 10
    c = next_version_num % 10

    return f"v{a}.{b}.{c}-{current_env}"

def extract_pr_numbers_between_tags(from_tag, to_tag):
    print(f"🔍 Getting PRs from {from_tag} → {to_tag}")    
    run("git fetch --tags")
    log = run(f"git log --merges --pretty=format:'%s' {from_tag}..{to_tag}")
    return re.findall(r'#(\d+)', log)

def get_and_merge_prs(env):
    pr_nums, notes, remarks, slack_md = [], [], "", ""

    def format_pr_notes(num, title, body):
        pr_nums.append(f"#{num}")
        #notes.append(f"- PR #{num}: {title}\n{body}")
        slack_md_entry = f"*#{num}* – *{title}*\n"
        slack_remarks = ""
        
        for line in body.strip().splitlines():
            if line.strip():
                slack_remarks += f"• {line.strip()} "
                notes.append(f"• {line.strip()}")
                
        slack_remarks += "\n"
        return slack_md_entry, slack_remarks

    if env.lower() == "staging":
        raw = run("gh pr list --state open --limit 20 --json number,title,body,headRefName")
        prs = json.loads(raw)

        if not prs:
            return [], "", "", ""

        for pr in prs:
            num, title, body = pr["number"], pr["title"], pr.get("body", "")
            
            # Check mergeability
            pr_status = json.loads(run(f"gh pr view {num} --json mergeable"))
            
            if pr_status.get("mergeable") != "MERGEABLE":
                for i in range(30):
                    print(f"⚠️ Retrying {i}... PR #{num}")
                    time.sleep(10)
                    
                    pr_status = json.loads(run(f"gh pr view {num} --json mergeable"))
                    if pr_status.get("mergeable") == "MERGEABLE":
                        break
             
            # Indeed not mergeable, skip           
            if pr_status.get("mergeable") != "MERGEABLE":
                print(f"⚠️ Skipping PR #{num} – not mergeable.")
                continue

            run(f"gh pr merge {num} --merge")  # add --delete-branch if needed
            md, rmk = format_pr_notes(num, title, body)
            slack_md += md
            remarks += rmk

    else:  # UAT or LIVE
        tag_prefix = "release" if env.lower() == "prod" else env.lower()
            
        last_tag = get_latest_tag(tag_prefix)
        staging_tag = get_latest_tag("staging")

        if not last_tag or not staging_tag:
            print("❌ Could not find suitable tags.")
            return [], "", "", ""

        pr_ids = extract_pr_numbers_between_tags(last_tag, staging_tag)
        if not pr_ids:
            return [], "", "", ""

        for pr_id in pr_ids:
            pr_data = json.loads(run(f"gh pr view {pr_id} --json number,title,body"))
            num, title, body = pr_data["number"], pr_data["title"], pr_data.get("body", "")
            md, rmk = format_pr_notes(num, title, body)
            slack_md += md
            remarks += rmk

    return pr_nums, "\n".join(notes), remarks.strip(), slack_md.strip()

def git_sync():
    run("git checkout master")
    run("git pull origin master")
    run("git push origin master")

def create_release(version):
    run(f"gh release create {version} --notes={version}")


if __name__ == "__main__":
    tag = get_latest_tag("staging")
    if tag:
        print(f"Latest tag: {tag}")
    else:
        print("No tag found.")

