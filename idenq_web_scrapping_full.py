import asyncio
from playwright.async_api import async_playwright
import json
import os

# --- Configuration ---
URL = "https://hiring.idenhq.com/"
EMAIL = "shubhamrgalande@gmail.com"
PASSWORD = "injqH0Fm"
AUTH_STATE_PATH = "auth_state.json"

# Logs in and saves session state for future runs
async def login_and_save_state(page, context):
    print("Logging in and saving session...")
    await page.goto(URL)
    await page.fill("input[type='email']", EMAIL)
    await page.fill("input[type='password']", PASSWORD)
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")
    await page.locator('button:has-text("Launch Challenge")').click()
    await page.locator('button:has-text("Start Journey")').click()
    await page.locator('button:has-text("Continue Search")').click()
    await page.locator('button:has-text("Inventory Section")').click()
    await page.wait_for_load_state("networkidle")
    await context.storage_state(path=AUTH_STATE_PATH)
    print("Session saved.")

# Scrolls until at least target_count product cards are loaded
async def scroll_until_at_least(page, target_count=50):
    for _ in range(30):
        cards = await page.locator("div.rounded-md.border").all()
        if len(cards) >= target_count:
            break
        await page.mouse.wheel(0, 3000)
        await asyncio.sleep(0.3)

# Extracts product data from loaded cards using parallel async calls
async def extract_products(page, limit=50):
    cards = await page.locator("div.rounded-md.border").all()
    async def extract(card):
        name = await card.locator("h3.font-medium").text_content()
        id_cat = await card.locator("div.text-sm.text-muted-foreground").inner_text()
        pid, cat = id_cat.replace("ID: ", "").split("•")
        stats = await card.locator("div.flex.flex-col.items-center").all()
        # Gather all stats in parallel for speed
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
    return await asyncio.gather(*(extract(card) for card in cards[:limit]))

# Saves extracted products to a JSON file
def save_products(products, path="inventory_data.json"):
    with open(path, "w") as f:
        json.dump(products, f, indent=4)
    print(f"Scraped and saved {len(products)} products.")

# Creates a browser context, blocks images/fonts, and handles session state
async def create_context_and_page(browser):
    context = await browser.new_context()
    if os.path.exists(AUTH_STATE_PATH):
        with open(AUTH_STATE_PATH) as f:
            state = json.load(f)
        if not state.get("cookies") and not state.get("origins"):
            print("Session state is empty, proceeding with normal login...")
            page = await context.new_page()
            return context, page, True
        else:
            print("Loading existing session...")
            context2 = await browser.new_context(storage_state=AUTH_STATE_PATH)
            await context2.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font"] else route.continue_())
            page = await context2.new_page()
            return context2, page, False
    else:
        page = await context.new_page()
        return context, page, True

# Main workflow: handles login/session, navigation, extraction, and saving
async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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
                # Adjust the number below to change how many products to scrape
                await scroll_until_at_least(page, 3605)
                products = await extract_products(page, 3605)
                save_products(products)
            except Exception as e:
                print(f"Error during product extraction or saving: {e}")
            await browser.close()
    except Exception as e:
        print(f"Fatal error: {e}")

asyncio.run(main())