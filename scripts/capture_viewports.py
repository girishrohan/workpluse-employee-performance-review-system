"""Utility script to capture high-resolution screenshots across viewports."""

import time
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_screenshots():
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1080")

    driver = webdriver.Edge(options=options)
    try:
        url = "http://localhost:8501"
        print(f"Navigating to {url}...")
        driver.get(url)

        # Wait until Streamlit DOM app container is rendered
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "wp-hp-navbar"))
        )
        print("Homepage navbar detected! Waiting 3 seconds for complete font & style paint...")
        time.sleep(3)

        os.makedirs("screenshots", exist_ok=True)

        # 1. Desktop Viewport
        driver.set_window_size(1440, 1000)
        time.sleep(1)
        driver.save_screenshot("screenshots/desktop_hero.png")
        print("Captured screenshots/desktop_hero.png")

        # Scroll down to product preview
        product_el = driver.find_element(By.ID, "product")
        driver.execute_script("arguments[0].scrollIntoView();", product_el)
        time.sleep(1.5)
        driver.save_screenshot("screenshots/desktop_product.png")
        print("Captured screenshots/desktop_product.png")

        # Scroll down to features
        features_el = driver.find_element(By.ID, "features")
        driver.execute_script("arguments[0].scrollIntoView();", features_el)
        time.sleep(1.5)
        driver.save_screenshot("screenshots/desktop_features.png")
        print("Captured screenshots/desktop_features.png")

        # Scroll down to how it works
        workflow_el = driver.find_element(By.ID, "how-it-works")
        driver.execute_script("arguments[0].scrollIntoView();", workflow_el)
        time.sleep(1.5)
        driver.save_screenshot("screenshots/desktop_workflow.png")
        print("Captured screenshots/desktop_workflow.png")

        # Scroll down to analytics showcase
        analytics_el = driver.find_element(By.ID, "analytics-showcase")
        driver.execute_script("arguments[0].scrollIntoView();", analytics_el)
        time.sleep(1.5)
        driver.save_screenshot("screenshots/desktop_analytics.png")
        print("Captured screenshots/desktop_analytics.png")

        # 2. Tablet Viewport
        driver.set_window_size(768, 1024)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.5)
        driver.save_screenshot("screenshots/tablet_hero.png")
        print("Captured screenshots/tablet_hero.png")

        # 3. Mobile Viewport
        driver.set_window_size(390, 844)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.5)
        driver.save_screenshot("screenshots/mobile_hero.png")
        print("Captured screenshots/mobile_hero.png")

        # Scroll on mobile
        driver.execute_script("arguments[0].scrollIntoView();", features_el)
        time.sleep(1.5)
        driver.save_screenshot("screenshots/mobile_features.png")
        print("Captured screenshots/mobile_features.png")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_screenshots()
