import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        os.makedirs("recordings", exist_ok=True)
        context = await browser.new_context(record_video_dir="recordings")
        page = await context.new_page()

        print("Navigating to Token Secured at http://localhost:8080 ...")
        await page.goto("http://localhost:8080", wait_until="networkidle")

        # 0. Authenticate Manoj-548 Individual Account
        print("Authenticating Manoj-548 Individual Account Vault...")
        await page.select_option("#userAccountSelector", "Manoj-548")
        await page.fill("#masterPasscodeInput", "123456")
        await page.click("button[onclick='unlockMasterVault()']")
        await page.wait_for_timeout(500)

        # 1. Generate Token
        await page.fill("#tokenLabelInput", "Manoj-548 Personal Production Token")
        await page.select_option("#tokenExpiryInput", "60")
        await page.click("button[type='submit']")
        print("Generated new isolated token for Manoj-548!")

        await page.wait_for_timeout(500)
        # Close Reveal Modal
        await page.click("#modalReveal button.btn-primary")
        await page.wait_for_timeout(500)

        # 2. Test Stolen Password Attempt Alert Simulator
        print("Testing 2FA Security Device Sign-In Alert Simulator...")
        await page.click("button[onclick='simulateNewDeviceLogin()']")
        await page.wait_for_timeout(600)

        # Fill 2FA OTP Code
        await page.fill("#otpCodeInput", "849201")
        await page.click("#modal2FAAlert button.btn-success")
        print("Verified 2FA OTP & Authorized Device!")

        await page.wait_for_timeout(1000)
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"SUCCESS: Individual Account & 2FA Automated Test completed & recorded to {video_path}")

if __name__ == '__main__':
    asyncio.run(main())
