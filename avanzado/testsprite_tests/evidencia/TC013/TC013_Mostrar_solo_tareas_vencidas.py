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
        
        # -> Enable the 'Solo vencidas' checkbox and click the 'Aplicar' button to apply filters.
        # overdue checkbox
        elem = page.get_by_role("checkbox", name="Solo vencidas")
        await elem.click(timeout=10000)
        
        # -> Enable the 'Solo vencidas' checkbox and click the 'Aplicar' button to apply filters.
        # Aplicar button
        elem = page.get_by_role("button", name="Aplicar")
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> La(s) tarea(s) visible(s) están vencidas y pendientes (muestran la etiqueta "Vencida" y el botón "Completar").
        # Assert-outcome: passed
        # Assert: The task displays the 'Vencida' label.
        await expect(page.locator("xpath=/html/body/ul/li/div/div[3]/span[3]").nth(0)).to_have_text("Vencida", timeout=15000), "The task displays the 'Vencida' label."
        # Assert-outcome: passed
        # Assert: The task shows a 'Completar' button indicating it is not completed.
        await expect(page.locator("xpath=/html/body/ul/li/form[1]/button").nth(0)).to_have_text("Completar", timeout=15000), "The task shows a 'Completar' button indicating it is not completed."
        
        # --> El filtro 'Solo vencidas' permanece activado después de aplicar los filtros (indicado en la URL).
        # Assert-outcome: passed
        # Assert: URL contains 'overdue=true', indicating the overdue filter is applied.
        await expect(page).to_have_url(re.compile("overdue=true"), timeout=15000), "URL contains 'overdue=true', indicating the overdue filter is applied."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    