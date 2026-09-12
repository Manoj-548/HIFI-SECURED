import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        os.makedirs("recordings", exist_ok=True)
        context = await browser.new_context(record_video_dir="recordings")
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        print("Navigating to CipherVault at http://localhost:8080 ...")
        await page.goto("http://localhost:8080", wait_until="networkidle")
        title = await page.title()
        print(f"Page Title: {title}")

        # 1. Fill Token Generator
        await page.fill("#tokenLabelInput", "Production Payment API Token")
        await page.select_option("#tokenExpiryInput", "60")
        await page.click("button[type='submit']")
        print("Generated new token!")

        await page.wait_for_timeout(500)
        # Check One-time reveal modal
        reveal_text = await page.inner_text("#revealTokenCode")
        print(f"One-Time Secret Reveal: {reveal_text}")

        # Close Reveal Modal
        await page.click("#modalReveal button.btn-primary")
        await page.wait_for_timeout(500)

        # 2. Simulate Token Share / Utilization Verification
        print("Triggering Token Utilization & Verification Alert...")
        await page.click("button[onclick='simulateExternalShareAttempt()']")
        await page.wait_for_timeout(600)

        # Confirm Alert Modal appeared
        alert_title = await page.inner_text("#modalAlert .alert-popup-title")
        print(f"Intentionality Alert Popup Displayed: {alert_title}")

        # Click "Yes (Approve Intentional)"
        await page.click("#modalAlert button.btn-success")
        print("Approved Intentional Use!")

        await page.wait_for_timeout(1000)
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"SUCCESS: Automated test completed & recorded to {video_path}")

if __name__ == '__main__':
    asyncio.run(main())
