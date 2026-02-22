import os
import json
from playwright.sync_api import sync_playwright

def verify_accessibility():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))

        # Mock authentication
        page.add_init_script("""
            localStorage.setItem('token', 'mock_token');
            localStorage.setItem('deployment_mode', 'desktop');
        """)

        # Mock user me
        page.route("**/api/v1/users/me", lambda route: route.fulfill(
             status=200,
             content_type="application/json",
             body=json.dumps({
                "id": "1",
                "email": "test@example.com",
                "full_name": "Test User",
                "is_admin": True,
                "is_active": True
            })
        ))

        # Navigate to Transactions page
        try:
            print("Navigating to Transactions page...")

            # Mock auth status
            page.route("**/api/v1/auth/status", lambda route: route.fulfill(
                 status=200,
                 content_type="application/json",
                 body=json.dumps({"is_authenticated": True, "user": {"id": "1", "email": "test@example.com", "is_admin": True}})
            ))

            # Mock the API response for /api/v1/transactions
            page.route("**/api/v1/transactions**", lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "transactions": [
                        {
                            "id": "1",
                            "transaction_type": "BUY",
                            "asset": {
                                "ticker_symbol": "AAPL",
                                "name": "Apple Inc.",
                                "currency": "USD",
                                "asset_type": "STOCK"
                            },
                            "quantity": 10,
                            "price_per_unit": 150,
                            "transaction_date": "2023-01-01T00:00:00Z",
                            "portfolio_id": "1"
                        }
                    ],
                    "total": 1
                })
            ))

            # Also mock portfolios to avoid errors/loading states that might block
            page.route("**/api/v1/portfolios**", lambda route: route.fulfill(
                 status=200,
                 content_type="application/json",
                 body=json.dumps([{"id": "1", "name": "My Portfolio"}])
            ))

            # Mock useAssets if needed, or other calls
            page.route("**/api/v1/assets**", lambda route: route.fulfill(
                 status=200, content_type="application/json", body="[]"
            ))

            page.goto("http://localhost:3000")

            # Click Transactions link
            print("Clicking Transactions link...")
            page.get_by_role("link", name="Transactions").click()

            # Wait for page to load
            page.wait_for_timeout(3000)

            # Take a screenshot of the page state
            os.makedirs("/home/jules/verification", exist_ok=True)
            page.screenshot(path="/home/jules/verification/page_state.png")
            print("Page state screenshot saved.")

            # Check Edit button aria-label
            print("Checking Edit button...")
            edit_btn = page.locator("button[aria-label='Edit BUY transaction for AAPL']")
            if edit_btn.count() > 0:
                print("SUCCESS: Found Edit button with correct aria-label")
            else:
                print("FAILURE: Did not find Edit button with correct aria-label")
                # Debug: print all button aria-labels
                buttons = page.locator("button").all()
                for b in buttons:
                    label = b.get_attribute("aria-label")
                    if label:
                        print(f"Button aria-label: {label}")
                    else:
                        print(f"Button text: {b.text_content()}")

            # Trigger Delete Modal
            print("Checking Delete button...")
            delete_btn = page.locator("button[aria-label='Delete BUY transaction for AAPL']")
            if delete_btn.count() > 0:
                print("SUCCESS: Found Delete button with correct aria-label")
                delete_btn.click()

                # Wait for modal
                page.wait_for_selector(".modal-content")

                # Check Close button in modal
                print("Checking Close button in modal...")
                close_btn = page.locator("button[aria-label='Close']")
                if close_btn.count() > 0:
                    print("SUCCESS: Found Close button with correct aria-label in modal")

                    # Take screenshot of the modal to see the X icon
                    page.screenshot(path="/home/jules/verification/modal_accessibility.png")
                    print("Screenshot saved to /home/jules/verification/modal_accessibility.png")
                else:
                    print("FAILURE: Did not find Close button in modal")
                    page.screenshot(path="/home/jules/verification/modal_failure.png")
            else:
                print("FAILURE: Did not find Delete button with correct aria-label")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_accessibility()
