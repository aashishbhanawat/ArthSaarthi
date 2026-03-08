import subprocess
import json
import time

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

print("Fetching open PRs...")
out = run(["gh", "pr", "list", "--state", "open", "--limit", "100", "--json", "number,title,mergeable"])
if out.returncode != 0:
    print(f"Error fetching PRs: {out.stderr}")
    exit(1)

prs = json.loads(out.stdout)
filtered_prs = [p for p in prs if 259 <= p.get('number', 0) <= 292]
filtered_prs.sort(key=lambda x: x['number'])
print(f"Found {len(filtered_prs)} open PRs in range 259-292 to process.")

for pr in filtered_prs:
    num = pr["number"]
    title = pr["title"]
    mergeable = pr.get("mergeable")

    print(f"\n--- Checking PR #{num}: {title} ---")

    if mergeable == "CONFLICTING":
        print(f"-> Skipping PR #{num} due to merge conflicts.")
        run(["gh", "pr", "comment", str(num), "-b", "Hi Jules! This PR has merge conflicts. Could you please rebase on main and resolve them?"])
        continue

    # Determine CI checks status
    checks_res = run(["gh", "pr", "checks", str(num)])
    checks_passed = (checks_res.returncode == 0)

    if not checks_passed:
        print(f"-> Skipping PR #{num} due to failing/pending CI checks.")
        # If it's failing, notify Jules.
        run(["gh", "pr", "comment", str(num), "-b", "Hi Jules! Looks like this PR has CI failures or pending checks. Could you please review and fix them so we can merge?"])
        continue

    # It passed checks and is not CONFLICTING. Let's merge it!
    # Because of branch protection (behind base branch), we use --auto.
    print(f"-> Target is MERGEABLE/UNKNOWN and CI passed. Attempting to merge PR #{num} with --auto...")
    merge_res = run(["gh", "pr", "merge", str(num), "--merge", "--auto"])

    if merge_res.returncode != 0:
        err = merge_res.stderr.strip()
        print(f"-> Failed to merge PR #{num}. Reason: {err}")
        # Let's try --admin as fallback if they really want it to merge NOW despite being behind.
        # But maybe we just comment if --auto fails due to some other branch rule.
        run(["gh", "pr", "comment", str(num), "-b", f"Hi Jules! We encountered an issue while attempting to merge this PR. Could you please check? Error: `{err}`"])
    else:
        # The auto merge text or success text will be in stdout/stderr
        success_msg = merge_res.stdout.strip()
        if success_msg:
            print(f"-> Successfully processed PR #{num}: {success_msg}")
        else:
            print(f"-> Successfully merged/queued PR #{num}!")

    time.sleep(1) # rate limiting protection

print("\nFinished processing all PRs.")
