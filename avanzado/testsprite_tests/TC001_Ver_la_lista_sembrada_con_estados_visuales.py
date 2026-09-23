import asyncio
import re
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--ipc=host",
                "--single-process"
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        # Wider default timeout to match the agent's DOM-stability budget;
        # auto-waiting Playwright APIs (expect, locator.wait_for) inherit this.
        context.set_default_timeout(15000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> navigate
        await page.goto("http://localhost:8010")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # --> Assertions to verify final state
        
        # --> Seeded tasks are present on the main page.
        # Assert-outcome: passed
        # Assert: A seeded task is shown with a 'Completar' button.
        await expect(page.locator("xpath=/html/body/ul/li[2]/form[1]/button").nth(0)).to_have_text("Completar", timeout=15000), "A seeded task is shown with a 'Completar' button."
        
        # --> Some tasks are shown as completed (they show only a 'Borrar' button).
        # Assert-outcome: passed
        # Assert: First seeded task shows a 'Borrar' button (indicating it is completed).
        await expect(page.locator("xpath=/html/body/ul/li[1]/form/button").nth(0)).to_have_text("Borrar", timeout=15000), "First seeded task shows a 'Borrar' button (indicating it is completed)."
        # Assert-outcome: passed
        # Assert: Another seeded task shows a 'Borrar' button (indicating it is completed).
        await expect(page.locator("xpath=/html/body/ul/li[5]/form/button").nth(0)).to_have_text("Borrar", timeout=15000), "Another seeded task shows a 'Borrar' button (indicating it is completed)."
        
        # --> An overdue task is highlighted with a visible 'Vencida' label.
        # Assert-outcome: passed
        # Assert: The task displays a 'Vencida' label.
        await expect(page.locator("xpath=/html/body/ul/li[2]/div/div[3]/span[3]").nth(0)).to_have_text("Vencida", timeout=15000), "The task displays a 'Vencida' label."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    