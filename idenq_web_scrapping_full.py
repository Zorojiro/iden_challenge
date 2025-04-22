import asyncio
from playwright.async_api import async_playwright
import json
import os

# --- Configuration ---
URL = "https://hiring.idenhq.com/"
EMAIL = "shubhamrgalande@gmail.com"
PASSWORD = "injqH0Fm"
AUTH_STATE_PATH = "auth_state.json"

# Login and save session state
async def login_and_save_state(page, context):
    print("Logging in and saving session...")
    await page.goto(URL)  # Go to login page
    await page.fill("input[type='email']", EMAIL)  # Enter email
    await page.fill("input[type='password']", PASSWORD)  # Enter password
    await page.click("button[type='submit']")  # Submit login form
    await page.wait_for_load_state("networkidle")  # Wait for page to load
    # Wait for and click through onboarding buttons
    await page.wait_for_selector('button:has-text("Launch Challenge")', state="visible")
    await page.locator('button:has-text("Launch Challenge")').click()  # Start challenge
    await page.locator('button:has-text("Start Journey")').click()  # Start journey
    await page.locator('button:has-text("Continue Search")').click()  # Continue search
    await page.locator('button:has-text("Inventory Section")').click()  # Go to inventory
    await page.wait_for_load_state("networkidle")  # Wait for inventory to load
    await context.storage_state(path=AUTH_STATE_PATH)  # Save session state
    print("Session saved.")

# Scroll until enough product cards are loaded
async def scroll_until_at_least(page, target_count=50):
    for _ in range(30):
        cards = await page.locator("div.rounded-md.border").all()  # Get all product cards
        if len(cards) >= target_count:
            break  # Stop if enough cards are loaded
        await page.mouse.wheel(0, 3000)  # Scroll down
        await asyncio.sleep(1)  # Wait for new cards to load

# Extract product data from cards
async def extract_products(page, limit=50):
    cards = await page.locator("div.rounded-md.border").all()  # Get all product cards
    async def extract(card):
        name = await card.locator("h3.font-medium").text_content()  # Product name
        id_cat = await card.locator("div.text-sm.text-muted-foreground").inner_text()  # ID and category
        pid, cat = id_cat.replace("ID: ", "").split("•")
        stats = await card.locator("div.flex.flex-col.items-center").all()  # Product stats
        # Extract stats in parallel
        stock, material, brand, updated = await asyncio.gather(
            stats[0].locator("span.font-medium").text_content(),
            stats[1].locator("span.font-medium").text_content(),
            stats[2].locator("span.font-medium").text_content(),
            stats[3].locator("span.font-medium").text_content(),
        )
        return {
            "name": name.strip(),
            "id": int(pid.strip()),
            "category": cat.strip(),
            "stock": int(stock),
            "material": material,
            "brand": brand,
            "updated": updated
        }
    # Extract data for each card in parallel
    return await asyncio.gather(*(extract(card) for card in cards[:limit]))

# Save products to a JSON file
def save_products(products, path="inventory_data.json"):
    with open(path, "w") as f:
        json.dump(products, f, indent=4)  # Write products to file
    print(f"Scraped and saved {len(products)} products.")

# Create browser context and page, handle session state
async def create_context_and_page(browser):
    if os.path.exists(AUTH_STATE_PATH):
        with open(AUTH_STATE_PATH) as f:
            state = json.load(f)
        if not state.get("cookies") and not state.get("origins"):
            print("Session state is empty, proceeding with normal login...")
            context = await browser.new_context()  # New context for login
            page = await context.new_page()  # New page
            return context, page, True  # Need to login
        else:
            print("Loading existing session...")
            context = await browser.new_context(storage_state=AUTH_STATE_PATH)  # Restore session
            page = await context.new_page()  # New page
            return context, page, False  # No need to login
    else:
        context = await browser.new_context()  # New context for login
        page = await context.new_page()  # New page
        return context, page, True  # Need to login

# Main workflow
async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context, page, do_login = await create_context_and_page(browser)
            if do_login:
                try:
                    await login_and_save_state(page, context)
                except Exception as e:
                    print(f"Error during login: {e}")
                    await browser.close()
                    return
            else:
                try:
                    await page.goto(URL)
                    await page.locator('button:has-text("Inventory Section")').click()
                    await page.wait_for_load_state("networkidle")
                except Exception as e:
                    print(f"Error loading inventory section: {e}")
                    await browser.close()
                    return
            try:
                await scroll_until_at_least(page, 3605)
                products = await extract_products(page, 3605)
                save_products(products)
            except Exception as e:
                print(f"Error during product extraction or saving: {e}")
            await browser.close()
    except Exception as e:
        print(f"Fatal error: {e}")

# Run the script
asyncio.run(main())