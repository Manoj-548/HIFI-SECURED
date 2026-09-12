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

        # 1. First Sign Up (User Generated 2FA Account)
        print("Registering First Master Owner Account via 2FA...")
        await page.click("button[onclick='toggleAuthMode()']") # switch to register tab
        await page.fill("#signUpUsername", "Manoj-548")
        await page.fill("#signUpEmail", "manoj548@token-secured.io")
        await page.fill("#signUpPasscode", "654321")
        await page.click("#btnRegister2FA")
        await page.wait_for_timeout(600)

        # 2. 2FA Sign In
        print("Authenticating Manoj-548 via 2FA Passcode...")
        await page.select_option("#userAccountSelector", "Manoj-548")
        await page.fill("#masterPasscodeInput", "654321")
        await page.click("button[onclick='unlockMasterVault()']")
        await page.wait_for_timeout(600)

        # 3. Add Collaborator (Developer User Generation)
        print("Generating Collaborator User (Dev-Alice) with RBAC permissions...")
        await page.click("button[onclick='switchTab(\"collaborators\")']")
        await page.fill("#collabUsernameInput", "Dev-Alice")
        await page.fill("#collabEmailInput", "alice@dev.io")
        await page.select_option("#collabRoleInput", "developer")
        await page.click("button[onclick='inviteCollaborator()']")
        await page.wait_for_timeout(600)

        # 4. Source Control & PR Approval Engine
        print("Testing Source Control PR Submission & 2FA Owner Approval...")
        await page.click("button[onclick='switchTab(\"source-control\")']")
        await page.fill("#prTitleInput", "Feature: Add Encrypted Token Cipher Stream")
        await page.select_option("#prAuthorSelect", "Dev-Alice")
        await page.fill("#prDiffInput", "Added cryptographic salt and AES-GCM cipher isolation module")
        await page.click("button[onclick='submitPullRequest()']")
        await page.wait_for_timeout(600)

        # Approve PR as Master Owner Manoj-548
        await page.click("button[onclick='approvePR(1)']")
        await page.wait_for_timeout(600)

        # 5. Token Generator
        print("Generating Invisible Secured Token...")
        await page.click("button[onclick='switchTab(\"dashboard\")']")
        await page.fill("#tokenLabelInput", "Manoj-548 Production Key")
        await page.select_option("#tokenExpiryInput", "60")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(500)
        await page.click("#modalReveal button.btn-primary")
        await page.wait_for_timeout(500)

        # 6. Test Security Stolen Password Alert Simulator
        print("Simulating Stolen Password / New Device Sign-In Attempt...")
        await page.click("button[onclick='simulateNewDeviceLogin()']")
        await page.wait_for_timeout(600)
        await page.fill("#otpCodeInput", "948201")
        await page.click("#modal2FAAlert button.btn-success")
        await page.wait_for_timeout(1000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"SUCCESS: 2FA, RBAC, PR Approval & Invisible Token test completed & recorded to {video_path}")

if __name__ == '__main__':
    asyncio.run(main())

