# IdenHQ Web Scraping Script

This script automates login and product data extraction from the IdenHQ hiring site using Playwright (Python).

## Features
- Logs in with provided credentials (or restores session if available)
- Navigates onboarding and inventory section
- Scrolls to load a specified number of products (default: 3605)
- Extracts product details in parallel for efficiency
- Saves results to `inventory_data.json`
- Handles session state in `auth_state.json`
- Blocks images and fonts for faster scraping
- Runs in headless mode for speed
- Includes basic error handling and clear print statements

## Usage
1. **Install dependencies:**
   - Install Playwright and its Python bindings:
     ```sh
     pip install playwright
     playwright install
     ```
2. **Configure credentials:**
   - Edit `EMAIL` and `PASSWORD` in the script if needed.

3. **Run the script:**
   ```sh
   python idenq_web_scrapping_full.py
   ```

4. **Output:**
   - Product data is saved in `inventory_data.json`.
   - Session state is saved in `auth_state.json` for faster future runs.

## Main Functions
- `login_and_save_state(page, context)`: Logs in and saves session state.
- `scroll_until_at_least(page, target_count)`: Scrolls to load enough products.
- `extract_products(page, limit)`: Extracts product info in parallel.
- `save_products(products, path)`: Saves products to a JSON file.
- `create_context_and_page(browser)`: Handles session state and context creation
- `main()`: Orchestrates the workflow with error handling.

---

**Notes:**
- The script uses print statements for status and error messages.
- The browser runs in headless mode by default for speed.
- Adjust the number of products to scrape by changing the value in `main()`.
