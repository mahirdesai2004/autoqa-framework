from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
from datetime import datetime


# Configuration
TIMEOUT = 10  # seconds to wait for elements
SCREENSHOTS_DIR = "screenshots"

# Selector type mapping
SELECTOR_MAP = {
    "id": By.ID,
    "name": By.NAME,
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "tag": By.TAG_NAME,
    "class": By.CLASS_NAME,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT
}


def ensure_screenshots_dir(subfolder=None):
    """Create screenshots directory (and subfolder) if it doesn't exist."""
    path = SCREENSHOTS_DIR
    if subfolder:
        path = os.path.join(SCREENSHOTS_DIR, subfolder)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def take_screenshot(driver, result="fail"):
    """
    Capture a screenshot and save it to the appropriate subfolder.
    Args:
        driver: Selenium WebDriver instance
        result: "pass" or "fail" - determines subfolder
    Returns the path to the saved screenshot.
    """
    subfolder = "pass" if result == "pass" else "fail"
    folder_path = ensure_screenshots_dir(subfolder)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}.png"
    filepath = os.path.join(folder_path, filename)
    
    try:
        driver.save_screenshot(filepath)
        print(f"[SCREENSHOT] Saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"[SCREENSHOT] Failed to save: {e}")
        return None


def get_driver():
    """
    Initialize and return a Chrome WebDriver with optimized settings.
    """
    options = webdriver.ChromeOptions()
    
    # Useful options for stability
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    
    # Uncomment for headless mode (no browser window)
    # options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    return driver


def get_by_type(selector_type: str):
    """
    Convert selector type string to Selenium By constant.
    Defaults to ID if not specified or unknown.
    """
    return SELECTOR_MAP.get(selector_type.lower(), By.ID)


def wait_for_element(driver, selector, selector_type="id", timeout=TIMEOUT):
    """
    Wait for an element to be present and visible.
    Returns the element if found, raises TimeoutException otherwise.
    """
    by = get_by_type(selector_type)
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.presence_of_element_located((by, selector)))


def find_element_smart(driver, selector, selector_type="id", timeout=TIMEOUT):
    """
    Try to find element with the given selector.
    Falls back to other selector types if primary fails.
    """
    by = get_by_type(selector_type)
    
    try:
        return wait_for_element(driver, selector, selector_type, timeout)
    except TimeoutException:
        # Fallback: try other common selectors
        fallbacks = [
            (By.ID, selector),
            (By.NAME, selector),
            (By.CSS_SELECTOR, f"#{selector}"),
            (By.CSS_SELECTOR, f".{selector}"),
            (By.CSS_SELECTOR, f"[name='{selector}']"),
            (By.TAG_NAME, selector)
        ]
        
        for fb_by, fb_selector in fallbacks:
            try:
                wait = WebDriverWait(driver, 2)
                return wait.until(EC.presence_of_element_located((fb_by, fb_selector)))
            except:
                continue
        
        raise TimeoutException(f"Could not find element: {selector} (type: {selector_type})")


def run_test(steps, url):
    """
    Execute test steps using Selenium with explicit waits.
    
    Args:
        steps: List of test step dictionaries from AI agent
        url: Target website URL
        
    Returns:
        tuple: (result, reason, screenshot_path)
            - result: "PASS" or "FAIL"
            - reason: Explanation of result
            - screenshot_path: Path to screenshot
    """
    driver = None
    result = "PASS"
    reason = ""
    screenshot_path = None
    
    try:
        # Initialize driver
        driver = get_driver()
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Execute each step
        for i, step in enumerate(steps):
            action = step.get("action", "")
            selector = step.get("selector", "")
            selector_type = step.get("selectorType", "id")
            value = step.get("value", "")
            
            print(f"[STEP {i+1}] {action} | selector: {selector} ({selector_type}) | value: {value}")
            
            if action == "navigate":
                # Already navigated above, skip
                continue
            
            elif action == "wait":
                # Wait for specified milliseconds
                wait_ms = int(value) if value else 1000
                time.sleep(wait_ms / 1000)
                
            elif action == "input":
                element = find_element_smart(driver, selector, selector_type)
                element.clear()
                element.send_keys(value)
                
            elif action == "click":
                element = find_element_smart(driver, selector, selector_type)
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.3)  # Brief pause after scroll
                element.click()
                
            elif action == "check":
                # Wait a moment for any async updates
                time.sleep(0.5)
                
                # Wait for element
                element = find_element_smart(driver, selector, selector_type)
                
                # Wait for text to appear (handles async updates)
                try:
                    WebDriverWait(driver, TIMEOUT).until(
                        lambda d: find_element_smart(d, selector, selector_type).text != ""
                    )
                except:
                    pass  # Continue even if text doesn't appear
                
                actual_text = element.text
                
                # Case-insensitive partial match
                if value.lower() not in actual_text.lower():
                    result = "FAIL"
                    reason = f"Expected text containing '{value}', but got '{actual_text}'"
                else:
                    print(f"[CHECK] ✓ Found expected text: '{value}' in '{actual_text}'")
                    
            else:
                print(f"[WARNING] Unknown action: {action}, skipping...")
                
        # Small pause to observe final state
        time.sleep(1)
                
    except TimeoutException as e:
        result = "FAIL"
        reason = f"Timeout waiting for element: {str(e)}"
        
    except NoSuchElementException as e:
        result = "FAIL"
        reason = f"Element not found: {str(e)}"
        
    except Exception as e:
        result = "FAIL"
        reason = f"Unexpected error: {str(e)}"
        
    finally:
        # Take screenshot for both PASS and FAIL (useful for demos)
        if driver:
            screenshot_result = "pass" if result == "PASS" else "fail"
            screenshot_path = take_screenshot(driver, screenshot_result)
            
        # Always close browser cleanly
        if driver:
            try:
                driver.quit()
                print("[BROWSER] Closed cleanly")
            except Exception as e:
                print(f"[BROWSER] Error closing: {e}")
    
    return result, reason, screenshot_path