from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import pandas as pd
import time
from webdriver_manager.chrome import ChromeDriverManager
import logging
import sys
from urllib3.exceptions import MaxRetryError
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraping.log')
    ]
)

def setup_driver():
    """Set up Chrome WebDriver with proper options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Chrome driver: {str(e)}")
        raise

def wait_for_element(driver, by, selector, timeout=20, retries=3):
    """Wait for element with retry mechanism"""
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            if attempt == retries - 1:
                raise
            logging.warning(f"Timeout waiting for element {selector}. Attempt {attempt + 1} of {retries}")
            time.sleep(2)

def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    cleaned = " ".join(text.strip().split())
    # Convert to title case for consistency
    return cleaned

def get_yes_no_status(row, position) -> bool:
    """Check status in specific table column and return boolean"""
    try:
        row.find_element(By.CSS_SELECTOR, 
            f"td.custom__table-heading__general:nth-of-type({position}) .catalogue__circle.-yes")
        return True
    except NoSuchElementException:
        return False

def get_test_codes(row) -> str:
    """Extract and format test type codes"""
    try:
        codes = [clean_text(key.text) for key in row.find_elements(
            By.CSS_SELECTOR, "td.product-catalogue__keys .product-catalogue__key")]
        # Remove any empty codes and standardize
        valid_codes = [code for code in codes if code]
        return ", ".join(sorted(set(valid_codes))) if valid_codes else "N/A"
    except Exception as e:
        logging.warning(f"Error getting test codes: {str(e)}")
        return "N/A"

def standardize_url(url: str) -> str:
    """Standardize URL format"""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = f"https://www.shl.com{url}"
    return url

def clean_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and standardize product data"""
    return {
        "page": int(data["Page"]),  # Convert to integer
        "assessment_name": clean_text(data["Assessment Name"]),
        "url": standardize_url(data["URL"]),
        "remote_testing": bool(data["Remote Testing"]),  # Convert to boolean
        "adaptive_irt_support": bool(data["Adaptive/IRT Support"]),  # Convert to boolean
        "test_type": data["Test Type"],
        "id": data["ID"]
    }

def scrape_page(driver, url, page_num):
    """Scrape a single page with error handling"""
    products = []
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            driver.get(url)
            # Wait for either table format to appear
            wait_for_element(driver, By.CSS_SELECTOR, "div.custom__table-responsive table")
            
            # Try both table formats
            rows = driver.find_elements(By.CSS_SELECTOR, 
                "div.custom__table-responsive table tr[data-course-id], div.custom__table-responsive table tr[data-entity-id]")
            
            for row in rows:
                try:
                    name_element = row.find_element(By.CSS_SELECTOR, "td.custom__table-heading__title a")
                    product_data = {
                        "Page": page_num,
                        "Assessment Name": clean_text(name_element.text),
                        "URL": name_element.get_attribute('href'),
                        "Remote Testing": get_yes_no_status(row, 1),
                        "Adaptive/IRT Support": get_yes_no_status(row, 2),
                        "Test Type": get_test_codes(row),
                        "ID": row.get_attribute("data-course-id") or row.get_attribute("data-entity-id")
                    }
                    # Clean and standardize the data
                    cleaned_data = clean_product_data(product_data)
                    products.append(cleaned_data)
                except Exception as e:
                    logging.warning(f"Error processing row on page {page_num}: {str(e)}")
                    continue
            
            return products
            
        except (TimeoutException, WebDriverException) as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to scrape page {page_num} after {max_retries} attempts: {str(e)}")
                return []
            logging.warning(f"Retrying page {page_num}. Attempt {attempt + 1} of {max_retries}")
            time.sleep(5)  # Wait before retry

def scrape_all_shl_products():
    """Main scraping function with improved error handling"""
    driver = None
    products = []
    base_url = "https://www.shl.com/products/product-catalog/"
    
    try:
        driver = setup_driver()
        page = 1
        
        while True:
            logging.info(f"Scraping page {page}...")
            url = f"{base_url}?start={(page-1)*12}" if page > 1 else base_url
            
            page_products = scrape_page(driver, url, page)
            
            if not page_products:
                logging.info(f"No products found on page {page}. Assuming end of catalog.")
                break
                
            products.extend(page_products)
            
            # Check for next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "li.pagination__item.-arrow.-next a")
                if not next_button.is_displayed() or not next_button.is_enabled():
                    break
                page += 1
                time.sleep(2)  # Polite delay between pages
            except NoSuchElementException:
                break
        
        # Create and clean DataFrame
        df = pd.DataFrame(products)
        if not df.empty:
            # Ensure proper data types
            df = df.astype({
                'page': 'int32',
                'assessment_name': 'string',
                'url': 'string',
                'remote_testing': 'bool',
                'adaptive_irt_support': 'bool',
                'test_type': 'string',
                'id': 'string'
            })
            
            df = df.drop_duplicates(subset=["id"], keep='first')
            df = df.sort_values(by=["page", "assessment_name"]).reset_index(drop=True)
            
            # Remove 'page' column and reorder columns before saving
            df = df.drop(columns=['page'])
            df = df[['id', 'assessment_name', 'url', 'remote_testing', 'adaptive_irt_support', 'test_type']]
            # Save to CSV in the data directory
            output_file = "app/data/product_catalog.csv"
            df.to_csv(output_file, index=False)
            logging.info(f"Successfully extracted {len(df)} products from {page-1} pages")
            logging.info(f"Data saved to {output_file}")
            return df
        else:
            logging.error("No products were scraped")
            return None

    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        raise
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    try:
        product_data = scrape_all_shl_products()
        if product_data is not None:
            print("\nFirst few products:")
            print(product_data.head())
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        sys.exit(1)