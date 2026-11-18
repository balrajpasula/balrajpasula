"""Rewrite the activity table in README.md from the user's public GitHub events."""
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

USER = os.environ.get("GH_USER", "balrajpasula")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
IST = timezone(timedelta(hours=5, minutes=30))
MAX_ROWS = 6

req = urllib.request.Request(
    f"https://api.github.com/users/{USER}/events/public?per_page=50",
    headers={"Accept": "application/vnd.github+json",
             **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})},
)
events = json.load(urllib.request.urlopen(req))


def describe(e):
    repo = e["repo"]["name"].split("/")[-1]
    p = e.get("payload", {})
    t = e["type"]
    if t == "PushEvent":
        n = p.get("size") or len(p.get("commits", [])) or 1
        return f"🚀 pushed {n} commit{'s' if n != 1 else ''} to **{repo}**"
    if t == "CreateEvent":
        return f"🌱 created {p.get('ref_type', 'repo')} {p.get('ref') or ''} in **{repo}**".replace("  ", " ")
    if t == "PullRequestEvent":
        return f"🔀 {p.get('action')} PR #{p.get('number')} in **{repo}**"
    if t == "IssuesEvent":
        return f"🐛 {p.get('action')} issue in **{repo}**"
    if t == "WatchEvent":
        return f"⭐ starred **{repo}**"
    if t == "ReleaseEvent":
        return f"🏷️ released {p.get('release', {}).get('tag_name', '')} in **{repo}**"
    return None


rows = []
for e in events:
    if e["repo"]["name"].lower() == f"{USER}/{USER}".lower():
        continue  # skip the bot's own README commits
    d = describe(e)
    if not d:
        continue
    ts = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).astimezone(IST)
    rows.append(f"| {ts:%b %d · %H:%M} | {d} |")
    if len(rows) == MAX_ROWS:
        break

table = "| time (IST) | event |\n|---|---|\n" + ("\n".join(rows) or "| — | quiet week, probably debugging prod |")

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
readme = re.sub(r"<!--ACTIVITY:START-->.*?<!--ACTIVITY:END-->",
                f"<!--ACTIVITY:START-->\n{table}\n<!--ACTIVITY:END-->", readme, flags=re.S)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
