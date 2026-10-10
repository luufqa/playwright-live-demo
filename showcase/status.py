from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request
import json
import time
import sys
import os
import re

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
STAGE_EVENTS = {
    ("queue", "done"): "Your turn: GitHub Actions gave us a clean Linux runner",
    ("base", "running"): "Docker starts building the base image",
    ("base", "done"): "Base image is ready",
    ("image", "running"): "Docker builds the test image on top of the base image",
    ("image", "done"): "Test image is ready: the container can start",
    ("report", "running"): "Allure collects the results into an HTML report",
}
MAIN_PACKAGES = ("pytest", "pytest-playwright", "playwright", "allure-pytest")


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


def add_event(status: dict, stage: str, text: str, kind: str = "info"):
    status["events"].append({"time": time.time(), "stage": stage, "text": text, "kind": kind})


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
        return f"{progress['done']}/{progress['total']} · ✅ {progress['passed']} ❌ {progress['failed']} ⏭️ {progress['skipped']}"
    if stage == "report" and state == "done":
        return f"[open report]({status['report_url']})"
    return {"running": "in progress…", "done": "ready", "failed": "failed"}.get(state, "")


def totals() -> dict:
    results = [test_progress(stage) for stage in ("smoke", "regression")]
    return {key: sum(result[key] for result in results if result) for key in ("passed", "failed", "skipped")}


def snapshot(status: dict) -> dict:
    """All data for the live page."""
    stages = []
    for stage, label in STAGES.items():
        state = stage_state(status, stage)
        stages.append({"id": stage, "label": label, "state": state, "details": details(status, stage, state)})
    return {
        "percent": percent(status),
        "finished": status["finished"],
        "queue": status["queue"],
        "run_url": status["run_url"],
        "report_url": status["report_url"] if status["stages"]["report"] == "done" else "",
        "post_url": status["post_url"],
        "stages": stages,
        "tests": {stage: test_progress(stage) for stage in ("smoke", "regression")},
        "events": status["events"][-80:],
        "totals": totals(),
    }


def render(status: dict) -> str:
    data = snapshot(status)
    value = data["percent"]
    bar = "▓" * (value // 5) + "░" * (20 - value // 5)
    lines = [
        f"## 🚀 Demo run · {value}%",
        "",
        f"`{bar}` **{value}%**",
        "",
        f"🎬 **[Watch it live, step by step]({status['page_url']})** · ▶️ [Raw log]({status['run_url']})",
        "",
        "| | Stage | Result |",
        "|---|---|---|",
    ]
    for stage in data["stages"]:
        lines.append(f"| {ICONS[stage['state']]} | {stage['label']} | {stage['details']} |")
    if status["finished"]:
        lines += ["", summary(status)]
    hidden = json.dumps(data, ensure_ascii=False).replace("--", "-\\u002d")
    lines += ["", f"<!-- status: {hidden} -->"]
    return "\n".join(lines)


def summary(status: dict) -> str:
    result = totals()
    lines = [
        "### 🏁 Finished",
        f"✅ {result['passed']} passed · ❌ {result['failed']} failed · ⏭️ {result['skipped']} skipped",
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
                    "Please wait until it finishes, then start a new one.\n\n"
                    f"<!-- duplicate: {running['number']} -->"
        })
        github("PATCH", f"/issues/{issue}", {"state": "closed", "state_reason": "not_planned"})
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"allowed={str(allowed).lower()}\n")


def queue():
    """Create the bot comment and wait until fewer than MAX_RUNS demos run before us."""
    issue = int(os.environ["ISSUE"])
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    status = {
        "issue": issue,
        "comment_id": None,
        "page_url": f"https://{owner}.github.io/{repo}/?issue={issue}",
        "run_url": os.environ["RUN_URL"],
        "report_url": os.environ["REPORT_URL"],
        "post_url": os.environ["POST_URL"],
        "queue": None,
        "stages": {stage: "waiting" for stage in STAGES},
        "events": [],
        "finished": False,
    }
    status["stages"]["queue"] = "running"
    add_event(status, "queue", f"Request received from issue #{issue}")
    status["comment_id"] = github("POST", f"/issues/{issue}/comments", {"body": "⏳ Starting…"})["id"]
    save(status)
    publish(status)
    while True:
        demos = open_demos()
        ahead = [demo for demo in demos if demo["number"] < issue]
        if len(ahead) < MAX_RUNS:
            break
        position = len(ahead) - MAX_RUNS + 1
        if status["queue"] != {"position": position, "total": len(demos)}:
            status["queue"] = {"position": position, "total": len(demos)}
            add_event(status, "queue", f"In queue: position {position} of {len(demos)}")
            save(status)
            publish(status)
        time.sleep(15)
    status["queue"] = None
    status["stages"]["queue"] = "done"
    add_event(status, "queue", STAGE_EVENTS[("queue", "done")], "ok")
    save(status)
    publish(status)


def stage(name: str, state: str):
    status = load()
    status["stages"][name] = state
    text = STAGE_EVENTS.get((name, state))
    if text:
        add_event(status, name, text, "ok" if state == "done" else "info")
    save(status)
    publish(status)


def docker_event(line: str, steps: dict):
    """Turn one line of the Docker build log into a short event, or None."""
    match = re.search(r"load metadata for docker\.io/library/(\S+)", line)
    if match:
        return f"Request to Docker Hub: {match.group(1)}", "info"
    match = re.match(r"#(\d+) \[(\w+) \d+/\d+\] FROM docker\.io/library/([^@\s]+)", line)
    if match:
        steps[match.group(1)] = True
        return f"Pull image {match.group(3)}", "cmd"
    match = re.match(r"#(\d+) \[(\w+) \d+/\d+\] (RUN|COPY|WORKDIR) (.+)", line)
    if match:
        steps[match.group(1)] = True
        command = " ".join(match.group(4).split())
        return f"[{match.group(2)}] {match.group(3)} {command[:110]}", "cmd"
    match = re.match(r"#(\d+) (DONE ([\d.]+)s|CACHED)$", line)
    if match and steps.pop(match.group(1), False):
        return ("from cache: already built", "ok") if match.group(2) == "CACHED" else (f"done in {match.group(3)} s", "ok")
    match = re.search(r"Setting up python3\.\d+ \((\S+)\)", line)
    if match:
        return f"Python {match.group(1).split('-')[0]} installed", "ok"
    match = re.search(r"Successfully installed (.+)", line)
    if match:
        packages = [package.rsplit("-", 1) for package in match.group(1).split()]
        main = [f"{name} {version}" for name, version in packages if name in MAIN_PACKAGES]
        return f"Installed: {', '.join(main)}", "ok"
    if "Installing dependencies..." in line:
        return "Installing system libraries for Chromium", "info"
    match = re.search(r"\d Downloading (.+?) \(playwright", line)
    if match:
        return f"Downloading {match.group(1)}", "info"
    return None


def docker(name: str):
    """Read the Docker build log from stdin, print it and send short events to the live page."""
    status = load()
    steps = {}
    last_publish = 0.0
    for line in sys.stdin:
        print(line, end="", flush=True)
        event = docker_event(line.strip(), steps)
        if event and (event[1] != "info" or all(old["text"] != event[0] for old in status["events"] if old["stage"] == name)):
            add_event(status, name, *event)
            save(status)
            if time.time() - last_publish > 3:
                last_publish = time.time()
                publish(status)
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
    add_event(status, "report", "Allure report is published" if report_published == "true" else "Report was not published",
              "ok" if report_published == "true" else "fail")
    status["finished"] = True
    save(status)
    publish(status)
    github("PATCH", f"/issues/{status['issue']}", {"state": "closed", "state_reason": "completed"})


if __name__ == "__main__":
    command, *arguments = sys.argv[1:]
    {"check": check, "queue": queue, "stage": stage, "docker": docker, "finish": finish}[command](*arguments)
