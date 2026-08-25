import urllib.request
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Retrieve GitHub credential dynamically via Git Credential Manager
def get_git_credential():
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input='protocol=https\nhost=github.com\n\n')
    user, token = None, None
    for line in out.splitlines():
        if line.startswith('username='):
            user = line.split('=', 1)[1]
        elif line.startswith('password='):
            token = line.split('=', 1)[1]
    return user, token

USER, TOKEN = get_git_credential()
REPO_NAME = "CC-SDA-SAP-HANA"

if not TOKEN or not USER:
    print("Error: Could not retrieve GitHub credentials from Git Credential Manager.")
    sys.exit(1)

print("================================================================================")
print(f" CREATING GITHUB REPOSITORY '{REPO_NAME}' FOR USER '{USER}'")
print("================================================================================")

url = "https://api.github.com/user/repos"
payload = {
    "name": REPO_NAME,
    "description": "SAP Convergent Charging (SAP CC) Grace Period & SDA Virtual Tables Analysis Repository",
    "private": False,
    "has_issues": True,
    "has_projects": True,
    "has_wiki": True
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "User-Agent": "Antigravity-AI-Agent"
})

try:
    with urllib.request.urlopen(req) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        repo_html_url = res_data.get("html_url")
        print(f"[OK] Repository '{REPO_NAME}' successfully created on GitHub!")
        print(f"     HTML URL : {repo_html_url}")
except urllib.error.HTTPError as e:
    if e.code == 422:
        print(f"[!] Repository '{REPO_NAME}' already exists on GitHub. Pushing changes.")
        repo_html_url = f"https://github.com/{USER}/{REPO_NAME}"
    else:
        print(f"HTTP Error {e.code}: {e.reason}")

auth_remote_url = f"https://{USER}:{TOKEN}@github.com/{USER}/{REPO_NAME}.git"
subprocess.run(["git", "branch", "-M", "main"], cwd=r"c:\Users\prana\Downloads\earthlink-app")
subprocess.run(["git", "remote", "remove", "origin"], cwd=r"c:\Users\prana\Downloads\earthlink-app", stderr=subprocess.DEVNULL)
subprocess.run(["git", "remote", "add", "origin", auth_remote_url], cwd=r"c:\Users\prana\Downloads\earthlink-app")

push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=r"c:\Users\prana\Downloads\earthlink-app", capture_output=True, text=True)

if push_res.returncode == 0:
    print(f"\n✅ SUCCESS! Repository live on GitHub: https://github.com/{USER}/{REPO_NAME}")
else:
    print("\n❌ Git Push Error:", push_res.stderr)
