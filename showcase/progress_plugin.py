from showcase import status
import time
import json
import os

FILE = status.DEMO_DIR / f"{os.environ['DEMO_STAGE']}.json"
progress = {"total": 0, "done": 0, "passed": 0, "failed": 0, "skipped": 0, "last": "", "last_outcome": "", "finished": False}
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
    save(force=True)


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and not report.passed):
        progress["done"] += 1
        progress[report.outcome] += 1
        progress["last"] = report.nodeid.split("::")[-1].split("[")[0]
        progress["last_outcome"] = report.outcome
        save()


def pytest_sessionfinish(session):
    progress["finished"] = True
    save(force=True)
