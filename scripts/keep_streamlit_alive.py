import asyncio
import datetime as dt
import json
import os
from pathlib import Path
from typing import Literal

import requests


DEFAULT_APP_URL = "https://gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app/"
LOG_FILE = Path(os.getenv("WAKE_LOG_FILE", "wakeup_log.txt"))
STATE_FILE = Path(os.getenv("WAKE_STATE_FILE", ".wake/wakeup_state.json"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
WAKE_INTERVAL_HOURS = float(os.getenv("WAKE_INTERVAL_HOURS", "10"))
WAKE_CONFIRM_TIMEOUT_SECONDS = float(os.getenv("WAKE_CONFIRM_TIMEOUT_SECONDS", "120"))
ENFORCE_WAKE_INTERVAL = os.getenv("ENFORCE_WAKE_INTERVAL", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

CheckState = Literal["awake", "asleep", "woken", "inconclusive", "errors"]

SLEEP_MARKERS = (
    "yes, get this app back up!",
    "this app has gone to sleep due to inactivity",
    "zzzz",
)
WAKING_MARKERS = (
    "this app is waking up",
    "your app is waking up",
    "please wait",
    "this may take a few moments",
)
APP_SELECTORS = (
    "[data-testid='stApp']",
    "[data-testid='stAppViewContainer']",
    "[data-testid='stSidebar']",
    "section.main",
    "main",
)


def app_urls() -> list[str]:
    raw_urls = os.getenv("STREAMLIT_APP_URLS") or os.getenv("STREAMLIT_APP_URL") or DEFAULT_APP_URL
    urls = [url.strip() for url in raw_urls.replace("\n", ",").split(",") if url.strip()]
    return list(dict.fromkeys(urls))


def log(message: str) -> None:
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{line}\n")


def should_skip_for_interval() -> bool:
    if not ENFORCE_WAKE_INTERVAL or WAKE_INTERVAL_HOURS <= 0:
        return False
    if not STATE_FILE.exists():
        return False

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        last_run = dt.datetime.fromisoformat(state["last_run_utc"])
    except (KeyError, ValueError, json.JSONDecodeError, OSError):
        return False

    if last_run.tzinfo is None:
        last_run = last_run.replace(tzinfo=dt.timezone.utc)

    elapsed = dt.datetime.now(dt.timezone.utc) - last_run
    if elapsed.total_seconds() < WAKE_INTERVAL_HOURS * 3600:
        log(f"Skipping run; last check was {elapsed} ago.")
        return True

    return False


def write_state() -> None:
    state = {"last_run_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def http_precheck(url: str) -> tuple[CheckState, str]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "GitPulse Streamlit wake check"},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return "inconclusive", f"HTTP precheck failed: {exc}"

    body = response.text.lower()
    if any(marker in body for marker in SLEEP_MARKERS):
        return "asleep", f"sleep marker found in HTTP response ({response.status_code})"
    if response.ok:
        return "awake", f"HTTP response looked awake ({response.status_code})"

    return "inconclusive", f"HTTP response was {response.status_code}"


async def app_content_loaded(page) -> bool:
    from playwright.async_api import Error as PlaywrightError

    try:
        body_text = (await page.locator("body").inner_text(timeout=2_000)).strip().lower()
    except PlaywrightError:
        body_text = ""

    if any(marker in body_text for marker in SLEEP_MARKERS + WAKING_MARKERS):
        return False

    for selector in APP_SELECTORS:
        if await page.locator(selector).count() > 0:
            return True

    return len(body_text) >= 40


async def wake_with_browser(url: str) -> tuple[CheckState, str]:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            await page.wait_for_timeout(5_000)

            wake_button = page.get_by_role("button", name="Yes, get this app back up!")
            if await wake_button.count() > 0:
                await wake_button.first.click()
                try:
                    await page.wait_for_function(
                        "() => !document.body.innerText.toLowerCase().includes('yes, get this app back up!')",
                        timeout=WAKE_CONFIRM_TIMEOUT_SECONDS * 1000,
                    )
                except PlaywrightTimeoutError:
                    pass

                if await app_content_loaded(page):
                    return "woken", "wake button clicked and app content loaded"

                return "errors", "wake button clicked but app content did not load"

            if await app_content_loaded(page):
                return "awake", "app content loaded in browser"

            title = await page.title()
            return "errors", f"wake button not found and app content not detected; title={title!r}"
        finally:
            await browser.close()


async def check_app(url: str) -> tuple[CheckState, str]:
    precheck_state, precheck_detail = http_precheck(url)
    log(f"HTTP precheck for {url}: {precheck_state} ({precheck_detail})")

    if precheck_state == "awake":
        return precheck_state, precheck_detail

    return await wake_with_browser(url)


async def main() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("", encoding="utf-8")

    log("Execution started.")
    if ENFORCE_WAKE_INTERVAL:
        log(f"Wake interval enabled: {WAKE_INTERVAL_HOURS:g} hour(s).")
    else:
        log("Wake interval disabled; checking apps every run.")

    if should_skip_for_interval():
        log("Execution finished.")
        return

    summary: dict[CheckState, int] = {
        "awake": 0,
        "asleep": 0,
        "woken": 0,
        "inconclusive": 0,
        "errors": 0,
    }

    urls = app_urls()
    for index, url in enumerate(urls, start=1):
        log(f"Checking app {index}/{len(urls)}: {url}")
        try:
            state, detail = await check_app(url)
        except Exception as exc:
            state, detail = "errors", f"unexpected error: {exc}"

        summary[state] += 1
        log(f"Result for {url}: {state} ({detail})")

    write_state()
    log(f"Summary: {summary}")
    log("Execution finished.")

    if summary["errors"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
