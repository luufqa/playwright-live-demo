# playwright-live-demo

Click a link and watch a real CI/CD pipeline: Docker build, Python + Playwright tests, Allure report — live, step by step.

## Project goal

This project shows that UI and API autotests in CI/CD are not hard.
Everything runs in Docker with one command: the same way on your computer and in GitHub Actions.

The tests check the public practice site [automationexercise.com](https://automationexercise.com).
This site is not part of this project.

## Run the demo

Open the link, click **Submit** and watch the pipeline live:

```text
https://github.com/luufqa/playwright-live-demo/issues/new?template=run-demo.md
```

## Run locally

You need only Docker.

```bash
docker build -t playwright-live-demo . && docker run --rm -v "$PWD/allure-results:/app/allure-results" playwright-live-demo
```

Run only the smoke tests:

```bash
docker run --rm playwright-live-demo pytest -m smoke
```

## What happens

1. Docker downloads `debian:trixie-slim` and installs Python 3.13 (stage `base`).
2. Docker installs Playwright, Chromium and Allure (stage `tests`).
3. A test user is created with the API.
4. Smoke tests run first. If they fail, the pipeline stops.
5. All other tests run.
6. The test user is deleted with the API.
7. The Allure report is ready.

## Tests

Expected result: **9 passed, 1 failed, 1 skipped.**

- The failed test is real: the site answers `200` to an unsupported `POST` request, but REST says it must be `405`.
- The skipped test shows how to skip a test on purpose: real payments are not allowed in the demo.

## Project structure

```text
├── api/        # API client for the site
├── data/       # test data
├── files/      # files for upload tests
├── locators/   # locators that are hard to find by role or text
├── pages/      # Page Object Model: one class for each page
├── tests/      # API and UI tests
├── showcase/   # only for this demo: live progress in the issue (not needed in a usual test project)
├── conftest.py # fixtures: API client, test user, screenshot on failure
├── pytest.ini  # site URL, browser, markers
└── Dockerfile  # two stages: base → tests
```

## License

[MIT](./LICENSE)
