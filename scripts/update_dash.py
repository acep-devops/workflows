import os, json, sys, urllib.request
from datetime import datetime, timezone

# Get environment variables
raw_str = os.environ.get("RAW_JSON", "")
if not raw_str:
    print("::error::RAW_JSON returned empty from GitHub API.")
    sys.exit(1)

data = json.loads(raw_str)

if "errors" in data:
    print("::error::GitHub API Error:", json.dumps(data["errors"]))
    sys.exit(1)

search = data.get("data", {}).get("search", {})
nodes = search.get("nodes", [])
total_count = search.get("issueCount", len(nodes))

if not nodes:
    message = "### 📋 Live PR Queue\n\n🎉 *No open PRs waiting for review!*"
else:
    # Added a new list for bot PRs
    needs_review, changes_requested, approved, bots = [], [], [], []
    now = datetime.now(timezone.utc)

    for pr in nodes:
        repo = pr.get("repository", {}).get("name", "repo")
        num = pr.get("number")
        url = pr.get("url")
        title = pr.get("title", "")
        author = pr.get("author", {}).get("login", "unknown") if pr.get("author") else "unknown"
        decision = pr.get("reviewDecision")
        created_raw = pr.get("createdAt")
        mergeable = pr.get("mergeable", "UNKNOWN") # Grab conflict status

        days_old = 0
        if created_raw:
            try:
                dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                days_old = max(0, (now - dt).days)
            except Exception:
                pass

        time_str = "Today" if days_old == 0 else f"{days_old}d ago"
        stale = " ⚠️" if days_old > 14 else ""
        conflict = " 🚨 CONFLICT" if mergeable == "CONFLICTING" else ""

        # Using the clean inline code formatting for the date, plus the conflict flag
        line = f"**[{repo}#{num}]({url})** {title} (*@{author}*) `{time_str}`{stale}{conflict}"

        # Sort Bots first so they don't clutter human reviews
        if author.lower() in ["dependabot", "renovate", "github-actions", "dependabot[bot]"]:
            bots.append(line)
        elif decision == "APPROVED":
            approved.append(line)
        elif decision == "CHANGES_REQUESTED":
            changes_requested.append(line)
        else:
            needs_review.append(line)

    message = f"### 📋 Live PR Queue ({total_count} Open)\n\n"
    if needs_review:
        message += "#### ⏳ Needs Review\n" + "\n".join(needs_review) + "\n\n"
    if changes_requested:
        message += "#### 🔴 Waiting on Author (Changes Requested)\n" + "\n".join(changes_requested) + "\n\n"
    if approved:
        message += "#### ✅ Ready to Merge (Approved)\n" + "\n".join(approved) + "\n\n"

    # Append the bots section at the very bottom
    if bots:
        message += "#### 🤖 Dependency Updates\n" + "\n".join(bots) + "\n\n"

    refresh_time = now.strftime("%b %d, %H:%M UTC")
    message += f"---\n*🔄 Last refreshed: {refresh_time}*"

mm_url = os.environ.get("MM_URL", "").rstrip("/")
post_id = os.environ.get("POST_ID", "")
mm_token = os.environ.get("MM_TOKEN", "")

if not mm_url or not post_id or not mm_token:
    print("::error::Missing required environment variables (MM_URL, POST_ID, or MM_TOKEN).")
    sys.exit(1)

endpoint = f"{mm_url}/api/v4/posts/{post_id}"
payload = json.dumps({"id": post_id, "message": message}).encode("utf-8")

req = urllib.request.Request(
    endpoint,
    data=payload,
    headers={
        "Authorization": f"Bearer {mm_token}",
        "Content-Type": "application/json"
    },
    method="PUT"
)

try:
    with urllib.request.urlopen(req) as resp:
        print(f"Successfully updated Mattermost! HTTP Status: {resp.status}")
except Exception as e:
    print(f"::error::Failed to update Mattermost: {e}")
    sys.exit(1)
