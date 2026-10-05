import asyncio
import os


APP_URL = os.getenv(
    "STREAMLIT_APP_URL",
    "https://gitpulse-64rqmapppv4wwlu8qpghuam.streamlit.app/",
)
APP_READY_SELECTOR = ", ".join(
    (
        "[data-testid='stApp']",
        "[data-testid='stAppViewContainer']",
        "section.main",
    )
)


async def main() -> None:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()

        print(f"Opening {APP_URL}")
        await page.goto(APP_URL, wait_until="domcontentloaded", timeout=120_000)
        await page.wait_for_timeout(5_000)

        wake_button = page.get_by_role("button", name="Yes, get this app back up!")
        if await wake_button.count() > 0:
            print("App is asleep. Clicking wake-up button.")
            await wake_button.click()
            await page.wait_for_timeout(60_000)
        else:
            print("Wake-up button not shown.")

        try:
            await page.wait_for_selector(APP_READY_SELECTOR, timeout=120_000)
            print("Streamlit app shell loaded.")
        except PlaywrightTimeoutError:
            title = await page.title()
            print(f"Timed out waiting for app shell. Page title: {title!r}")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
