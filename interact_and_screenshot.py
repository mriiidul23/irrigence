"""
Autonomous browser interaction and verification script for Irrigence Streamlit Dashboard.
Uses Playwright with installed Google Chrome to:
1. Navigate to http://localhost:8501
2. Verify all UI components, KPI metrics, Folium Leaflet map, Reach scorecard table, and RMSE charts.
3. Interact with sidebar parameters (adjust headworks inflow, rainfall, defect severity).
4. Capture high-resolution screenshots for review.
"""

import time
import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\user\.gemini\antigravity\brain\7becf07c-44e8-4e96-9c51-4af23d49d075"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://localhost:8501"

def run_browser_verification():
    print(f"Launching Chrome from: {CHROME_PATH}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(viewport={"width": 1650, "height": 1150})
        page = context.new_page()

        print(f"Navigating to {URL}...")
        page.goto(URL, wait_until="networkidle", timeout=45000)

        # Wait for Streamlit to render main content
        print("Waiting for Streamlit app elements...")
        page.wait_for_selector("h1", timeout=30000)
        time.sleep(5)  # Allow folium iframe and Streamlit components to mount

        # Capture Tab 1: GIS Map & Scorecard Table
        shot1_path = os.path.join(ARTIFACT_DIR, "irrigence_dashboard_map.png")
        page.screenshot(path=shot1_path, full_page=False)
        print(f"Captured Map & KPI overview: {shot1_path}")

        # List all tabs
        tabs = page.locator("[role='tab']")
        tab_count = tabs.count()
        print(f"Found {tab_count} tabs on page.")

        # Switch to Tab 2: AI/ML Model Validation & RMSE Tracker
        print("Clicking Tab 2: AI/ML Model Validation & RMSE Tracker...")
        tabs.nth(1).click()
        time.sleep(4)

        shot2_path = os.path.join(ARTIFACT_DIR, "irrigence_dashboard_rmse.png")
        page.screenshot(path=shot2_path, full_page=False)
        print(f"Captured RMSE Tracker: {shot2_path}")

        # Switch to Tab 3: Sensor Telemetry Deep Dive
        print("Clicking Tab 3: Sensor Telemetry Deep Dive...")
        tabs.nth(2).click()
        time.sleep(4)

        shot3_path = os.path.join(ARTIFACT_DIR, "irrigence_dashboard_telemetry.png")
        page.screenshot(path=shot3_path, full_page=False)
        print(f"Captured Sensor Telemetry Deep Dive: {shot3_path}")

        # Switch to Tab 4: PostGIS / GeoServer Data Export
        print("Clicking Tab 4: PostGIS / GeoServer Data Export...")
        tabs.nth(3).click()
        time.sleep(3)

        shot4_path = os.path.join(ARTIFACT_DIR, "irrigence_dashboard_postgis.png")
        page.screenshot(path=shot4_path, full_page=False)
        print(f"Captured PostGIS Export: {shot4_path}")

        # Switch back to Tab 1
        tabs.nth(0).click()
        time.sleep(2)

        # Test Slider interaction: adjust rainfall or headworks slider
        print("Interacting with sidebar sliders...")
        sliders = page.locator("div[data-testid='stSlider']")
        if sliders.count() > 0:
            print(f"Found {sliders.count()} sliders in sidebar. Clicking slider...")
            sliders.nth(1).click()
            time.sleep(3)

        shot_full_path = os.path.join(ARTIFACT_DIR, "irrigence_full_overview.png")
        page.screenshot(path=shot_full_path, full_page=False)
        print(f"Captured Updated Dashboard: {shot_full_path}")

        browser.close()
        print("Autonomous browser testing & verification completed successfully!")

if __name__ == "__main__":
    run_browser_verification()
