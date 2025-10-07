import re
from playwright.sync_api import sync_playwright, Page, expect
import os

# --- Test Setup ---
# Get credentials from environment variables
email = os.environ.get("E2E_TEST_EMAIL", "admin@example.com")
password = os.environ.get("E2E_TEST_PASSWORD", "SecurePassword1!")
base_url = os.environ.get("BASE_URL", "http://127.0.0.1:3008")

def run_verification(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # --- Log In ---
        print("Logging in...")
        page.goto(f"{base_url}/")
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Log In").click()
        expect(page.get_by_role("heading", name="Dashboard")).to_be_visible(timeout=10000)
        print("Login successful.")

        # --- Navigate to the first portfolio ---
        print("Navigating to portfolio...")
        page.get_by_role("link", name="Portfolios").click()
        # Click the first portfolio link
        page.locator('.ag-row[row-index="0"] a').first.click()
        expect(page.get_by_role("heading", name=re.compile(r"Portfolio:"))).to_be_visible(timeout=10000)
        print("Portfolio page loaded.")

        # --- Add a BUY transaction to ensure the asset exists ---
        print("Adding a BUY transaction for an asset...")
        page.get_by_role("button", name="Add Transaction").click()

        # Wait for modal to appear
        expect(page.get_by_role("heading", name="Add Transaction")).to_be_visible()

        page.get_by_label("Asset", exact=True).fill("MSFT")
        page.get_by_text("MSFT (Microsoft Corporation)").click()
        page.get_by_label("Quantity").fill("10")
        page.get_by_label("Price").fill("100")
        page.get_by_role("button", name="Save Transaction").click()

        # Wait for the transaction to be processed and UI to update
        expect(page.get_by_text("MSFT")).to_be_visible(timeout=5000)
        print("Initial BUY transaction created.")


        # --- Open Corporate Action Form ---
        print("Opening corporate action form...")
        page.get_by_role("button", name="Add Transaction").click()
        expect(page.get_by_role("heading", name="Add Transaction")).to_be_visible()

        # Select the asset
        page.get_by_label("Asset", exact=True).fill("MSFT")
        page.get_by_text("MSFT (Microsoft Corporation)").click()

        # Select "Corporate Action"
        page.get_by_label("Transaction Type").select_option("CORPORATE_ACTION")
        print("Selected 'Corporate Action'.")

        # Screenshot 1: Initial Corporate Action state
        page.screenshot(path="jules-scratch/verification/01_corporate_action_selected.png")
        print("Screenshot 1 taken.")

        # --- Verify Stock Split Form ---
        print("Verifying Stock Split form...")
        page.get_by_label("Action Type").select_option("SPLIT")
        expect(page.get_by_text("Split Ratio")).to_be_visible()
        page.screenshot(path="jules-scratch/verification/02_stock_split_form.png")
        print("Screenshot 2 taken.")

        # --- Verify Bonus Issue Form ---
        print("Verifying Bonus Issue form...")
        page.get_by_label("Action Type").select_option("BONUS")
        expect(page.get_by_text("Bonus Ratio")).to_be_visible()
        page.screenshot(path="jules-scratch/verification/03_bonus_issue_form.png")
        print("Screenshot 3 taken.")

        # --- Verify Dividend Form ---
        print("Verifying Dividend form...")
        page.get_by_label("Action Type").select_option("DIVIDEND")
        expect(page.get_by_text("Total Amount")).to_be_visible()
        expect(page.get_by_label("Reinvest this dividend?")).to_be_visible()
        page.screenshot(path="jules-scratch/verification/04_dividend_form.png")
        print("Screenshot 4 taken.")

        print("Verification script completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        page.screenshot(path="jules-scratch/verification/error.png")

    finally:
        # --- Cleanup ---
        context.close()
        browser.close()

with sync_playwright() as playwright:
    run_verification(playwright)