from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request
import json
import time
import sys
import os

MAX_RUNS = 3
DEMO_DIR = Path("demo")
STATUS_FILE = DEMO_DIR / "status.json"

STAGES = {
    "queue": "Queue",
    "base": "Docker: base image (Debian + Python)",
    "image": "Docker: test image (Playwright + Chromium + Allure)",
    "smoke": "Smoke tests (critical checks)",
    "regression": "Regression tests",
    "report": "Allure report",
}
PERCENT = {
    "queue": (0, 5),
    "base": (5, 20),
    "image": (20, 40),
    "smoke": (40, 50),
    "regression": (50, 90),
    "report": (90, 100),
}
ICONS = {"waiting": "⬜", "running": "⏳", "done": "✅", "failed": "❌", "skipped": "⏭️"}
TEST_ICONS = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}


def github(method: str, path: str, data: dict = None):
    """Call the GitHub REST API with the workflow token."""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}{path}",
        method=method,
        data=json.dumps(data).encode() if data else None,
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read() or "null")


def load() -> dict:
    return json.loads(STATUS_FILE.read_text())


def save(status: dict):
    STATUS_FILE.write_text(json.dumps(status))


def test_progress(stage: str):
    """Read the progress file that the pytest plugin writes for a test stage."""
    file = DEMO_DIR / f"{stage}.json"
    return json.loads(file.read_text()) if file.exists() else None


def stage_state(status: dict, stage: str) -> str:
    progress = test_progress(stage) if stage in ("smoke", "regression") else None
    if progress is None:
        return status["stages"][stage]
    if not progress["finished"]:
        return "running"
    return "failed" if progress["failed"] else "done"


def percent(status: dict) -> int:
    value = 0
    for stage in STAGES:
        start, end = PERCENT[stage]
        state = stage_state(status, stage)
        if state in ("done", "failed", "skipped"):
            value = end
        elif state == "running":
            progress = test_progress(stage)
            if progress and progress["total"]:
                value = start + (end - start) * progress["done"] // progress["total"]
            else:
                value = start
            break
        else:
            break
    return value


def details(status: dict, stage: str, state: str) -> str:
    if stage == "queue":
        queue = status["queue"]
        return f"position {queue['position']} of {queue['total']}" if queue else "your turn"
    if stage in ("smoke", "regression"):
        progress = test_progress(stage)
        if not progress:
            return ""
        text = f"{progress['done']}/{progress['total']} · ✅ {progress['passed']} ❌ {progress['failed']} ⏭️ {progress['skipped']}"
        if progress["last"]:
            text += f" · last: {TEST_ICONS[progress['last_outcome']]} `{progress['last']}`"
        return text
    if stage == "report" and state == "done":
        return f"[open report]({status['report_url']})"
    return {"running": "in progress…", "done": "ready", "failed": "failed"}.get(state, "")


def render(status: dict) -> str:
    value = percent(status)
    bar = "▓" * (value // 5) + "░" * (20 - value // 5)
    stages = {stage: stage_state(status, stage) for stage in STAGES}
    lines = [
        f"## 🚀 Demo run · {value}%",
        "",
        f"`{bar}` **{value}%**",
        "",
        "| | Stage | Result |",
        "|---|---|---|",
    ]
    for stage, label in STAGES.items():
        lines.append(f"| {ICONS[stages[stage]]} | {label} | {details(status, stage, stages[stage])} |")
    lines += ["", f"▶️ [Watch the live log]({status['run_url']})"]
    if status["finished"]:
        lines += ["", summary(status)]
    lines += ["", f"<!-- status: {json.dumps({'percent': value, 'stages': stages})} -->"]
    return "\n".join(lines)


def summary(status: dict) -> str:
    results = [test_progress(stage) for stage in ("smoke", "regression")]
    passed = sum(result["passed"] for result in results if result)
    failed = sum(result["failed"] for result in results if result)
    skipped = sum(result["skipped"] for result in results if result)
    lines = [
        "### 🏁 Finished",
        f"✅ {passed} passed · ❌ {failed} failed · ⏭️ {skipped} skipped",
        "The failed test is expected: the site answers `200` to an unsupported `POST`, but REST says it must be `405`.",
    ]
    if status["stages"]["report"] == "done":
        lines.append(f"📊 **[Open the Allure report]({status['report_url']})**")
    if status["post_url"]:
        lines.append(f"💬 Was it useful? [Share your thoughts under the post]({status['post_url']})")
    return "\n\n".join(lines)


def publish(status: dict):
    """Update the bot comment and the issue title."""
    github("PATCH", f"/issues/comments/{status['comment_id']}", {"body": render(status)})
    title = "Demo run · finished" if status["finished"] else f"Demo run · {percent(status)}%"
    if status["queue"]:
        title = f"Demo run · in queue ({status['queue']['position']})"
    github("PATCH", f"/issues/{status['issue']}", {"title": title})


def open_demos() -> list:
    """Open demo issues from the last 40 minutes, oldest first."""
    issues = github("GET", "/issues?labels=demo&state=open&sort=created&direction=asc&per_page=100")
    since = datetime.now(timezone.utc) - timedelta(minutes=40)
    return [
        issue for issue in issues
        if "pull_request" not in issue and datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")) > since
    ]


def check():
    """Allow only one running demo per person."""
    issue = int(os.environ["ISSUE"])
    github("POST", f"/issues/{issue}/labels", {"labels": ["demo"]})
    earlier = [
        demo for demo in open_demos()
        if demo["user"]["login"] == os.environ["AUTHOR"] and demo["number"] < issue
    ]
    allowed = not earlier
    if not allowed:
        running = earlier[0]
        github("POST", f"/issues/{issue}/comments", {
            "body": f"👋 You already have a demo running: #{running['number']} — **{running['title']}**.\n"
                    "Please wait until it finishes, then start a new one."
        })
        github("PATCH", f"/issues/{issue}", {"state": "closed", "state_reason": "not_planned"})
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"allowed={str(allowed).lower()}\n")


def queue():
    """Create the bot comment and wait until fewer than MAX_RUNS demos run before us."""
    issue = int(os.environ["ISSUE"])
    status = {
        "issue": issue,
        "comment_id": None,
        "run_url": os.environ["RUN_URL"],
        "report_url": os.environ["REPORT_URL"],
        "post_url": os.environ["POST_URL"],
        "queue": None,
        "stages": {stage: "waiting" for stage in STAGES},
        "finished": False,
    }
    status["stages"]["queue"] = "running"
    status["comment_id"] = github("POST", f"/issues/{issue}/comments", {"body": "⏳ Starting…"})["id"]
    save(status)
    while True:
        demos = open_demos()
        ahead = [demo for demo in demos if demo["number"] < issue]
        if len(ahead) < MAX_RUNS:
            break
        position = len(ahead) - MAX_RUNS + 1
        if status["queue"] != {"position": position, "total": len(demos)}:
            status["queue"] = {"position": position, "total": len(demos)}
            save(status)
            publish(status)
        time.sleep(15)
    status["queue"] = None
    status["stages"]["queue"] = "done"
    save(status)
    publish(status)


def stage(name: str, state: str):
    status = load()
    status["stages"][name] = state
    save(status)
    publish(status)


def finish(report_published: str):
    """Mark unfinished stages, show the summary and close the issue."""
    status = load()
    status["stages"]["report"] = "done" if report_published == "true" else "failed"
    for name in STAGES:
        state = stage_state(status, name)
        if state == "running":
            status["stages"][name] = "failed"
        elif state == "waiting":
            status["stages"][name] = "skipped"
    status["finished"] = True
    save(status)
    publish(status)
    github("PATCH", f"/issues/{status['issue']}", {"state": "closed", "state_reason": "completed"})


if __name__ == "__main__":
    command, *arguments = sys.argv[1:]
    {"check": check, "queue": queue, "stage": stage, "finish": finish}[command](*arguments)
