import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        os.makedirs("recordings", exist_ok=True)
        context = await browser.new_context(record_video_dir="recordings")
        page = await context.new_page()

        print("Navigating to Token Secured at http://127.0.0.1:8080 ...")
        await page.goto("http://127.0.0.1:8080", wait_until="networkidle")

        # 1. Registration & 2FA Authentication
        print("Registering Master Owner Account via 2FA Auth Overlay...")
        await page.click("#toggleSignUpBtn")
        await page.fill("#authUsernameInput", "Manoj-548")
        await page.fill("#authEmailInput", "manoj548@token-secured.io")
        await page.fill("#masterPasscodeInput", "654321")
        await page.click("#authForm button[type='submit']")
        await page.wait_for_timeout(1000)

        # 2. Test Encrypted Password Vault Item Creation
        print("Testing Encrypted Password Vault Entry creation...")
        await page.evaluate("openModal('modalVaultItem')")
        await page.wait_for_timeout(400)

        await page.fill("#vaultHolderInput", "Manoj-548 (Master Owner)")
        await page.fill("#vaultServiceNameInput", "AWS Production Console")
        await page.fill("#vaultUsernameInput", "aws_master_root@enterprise.org")
        await page.fill("#vaultPasswordInput", "SuperSecureVaultPass#2026!")
        await page.fill("#vaultUrlInput", "https://console.aws.amazon.com")
        await page.click("#modalVaultItem button[type='submit']")
        await page.wait_for_timeout(1000)

        # 3. Test Password Generator Tool Modal
        print("Testing Password Generator Tool...")
        await page.evaluate("openPasswordGeneratorModal()")
        await page.wait_for_timeout(500)
        await page.click("button[onclick='copyGeneratedPassword()']")
        await page.wait_for_timeout(500)

        # 4. Test Platform Invisible Tokens Desk
        print("Testing Platform Invisible Tokens Desk...")
        await page.click("button[data-view='invisible-tokens']")
        await page.wait_for_timeout(800)

        # Open Issue Token Modal
        print("Issuing unique Invisible Token for Telegram Bot Gateway...")
        await page.click("button[onclick='openCreatePlatformTokenModal()']")
        await page.wait_for_timeout(400)
        await page.select_option("#platformSelectInput", "Telegram Bot Gateway")
        await page.fill("#platformTokenLabelInput", "Telegram DevOps Bot Stream")
        await page.fill("#platformScopesInput", "bot, messages:send, alerts")
        await page.click("#modalPlatformInvisibleToken button[type='submit']")
        await page.wait_for_timeout(1000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"SUCCESS: 2FA Auth, Password Vault & Invisible Tokens Desk UI test completed & recorded to {video_path}")

if __name__ == '__main__':
    asyncio.run(main())



