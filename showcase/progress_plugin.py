from showcase import status
import time
import json
import os

FILE = status.DEMO_DIR / f"{os.environ['DEMO_STAGE']}.json"
progress = {"total": 0, "done": 0, "passed": 0, "failed": 0, "skipped": 0, "current": "", "tests": [], "notes": [], "finished": False}
titles = {}
last_publish = 0.0


def save(force: bool = False):
    """Write the progress file and update the bot comment at most every 3 seconds."""
    global last_publish
    FILE.write_text(json.dumps(progress))
    if force or time.time() - last_publish > 3:
        last_publish = time.time()
        try:
            status.publish(status.load())
        except OSError:
            pass


def pytest_collection_finish(session):
    progress["total"] = len(session.items)
    for item in session.items:
        titles[item.nodeid] = getattr(item.function, "__allure_display_name__", item.name)
    save(force=True)


def pytest_fixture_setup(fixturedef):
    if fixturedef.argname == "user":
        progress["notes"].append({"time": time.time(), "kind": "info", "text": "Fixture «user»: create a test user with the API (before the browser starts)"})
        save()


def pytest_fixture_post_finalizer(fixturedef):
    if fixturedef.argname == "user" and fixturedef.cached_result is not None:
        progress["notes"].append({"time": time.time(), "kind": "info", "text": "Fixture «user»: delete the test user with the API"})
        save()


def pytest_runtest_logstart(nodeid):
    progress["current"] = titles.get(nodeid, nodeid)
    save()


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and not report.passed):
        progress["done"] += 1
        progress[report.outcome] += 1
        progress["current"] = ""
        progress["tests"].append({
            "nodeid": report.nodeid,
            "percent": progress["done"] * 100 // progress["total"],
            "title": titles.get(report.nodeid, report.nodeid),
            "outcome": report.outcome,
            "duration": round(report.duration, 1),
            "time": time.time(),
        })
        save()


def pytest_sessionfinish(session):
    progress["finished"] = True
    save(force=True)
