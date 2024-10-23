import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def scrape_goat_and_compare_with_ebay(shoe_name):
    shoe_name_formatted = shoe_name.replace(' ', '+')
    url = f"https://www.goat.com/search?web_groups=sneakers&gender=men&size_converted=us_sneakers_men_10.5&product_condition=used"

    # Start the Selenium WebDriver
    driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
    driver.get(url)
    time.sleep(3)  # URL LOAD TIME
                   # THIS IS RELATIVE TO SYSTEM SPECS AND INTERNET SPEEDS

    # Scroll to load more items
    SCROLL_PAUSE_TIME = 2
    MAX_SCROLLS = 10  # Limit the number of scrolls to avoid running indefinitely
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    found_shoe = False
    shoe_name_found = None
    shoe_price_found = None

    for i in range(MAX_SCROLLS):
        # Find the listings on the current loaded page
        listings = driver.find_elements(By.XPATH, "//div[@data-qa='grid_cell_product']")
        
        # Process each listing
        for listing in listings:
            img_tag = listing.find_element(By.TAG_NAME, 'img')
            price_element = listing.find_element(By.XPATH, ".//span[contains(@class, 'LocalizedCurrency__Amount')]")

            if img_tag and price_element:
                shoe_alt = img_tag.get_attribute('alt').strip()
                price_text = price_element.text.strip()
                try:
                    price = float(price_text.replace('$', '').replace(',', ''))
                except ValueError:
                    continue  # Skip listings with invalid prices

                # Check if the shoe matches the input
                if shoe_name.lower() in shoe_alt.lower():
                    print(f"Found: {shoe_alt}  =>  Price: ${price}")
                    shoe_name_found = shoe_alt
                    shoe_price_found = price
                    found_shoe = True  # Set a flag that the shoe is found
                    break  # Break out of the inner loop
        
        if found_shoe:
            break  # Break out of the outer scrolling loop

        # Scroll down to load more items if the shoe is not found yet
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with the last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break  # Exit if no new content is loaded
        last_height = new_height

    driver.quit()
    
    if not found_shoe:
        print("No matches found")
        return None

    # If shoe is found, compare with eBay prices
    ebay_avg_price = get_ebay_average_price(shoe_name_found)
    
    if ebay_avg_price:
        print(f"GOAT Price: ${shoe_price_found} | eBay Avg: ${ebay_avg_price}")
        if shoe_price_found < ebay_avg_price:
            print(f"Deal found for {shoe_name_found}!")
            return {
                'name': shoe_name_found,
                'goat_price': shoe_price_found,
                'ebay_avg_price': ebay_avg_price
            }
        else:
            print(f"No deal found for {shoe_name_found}.")
            return None
    else:
        print("Could not find eBay price data.")
        return None


def get_ebay_average_price(shoe_name, sizes):
    # Format the sizes into the correct query format for eBay
    size_query = "%7C".join(sizes)  # Join sizes with "%7C" (URL encoding for "|")
    
    query = f"{shoe_name}"
    # eBay URL with the shoe size included dynamically
    url = f"https://www.ebay.com/sch/i.html?_fsrp=1&_from=R40&_nkw={query.replace(' ', '+')}&_sacat=0&LH_Sold=1&rt=nc&US%2520Shoe%2520Size={size_query}&_dcat=15709"

    response = requests.get(url)
    time.sleep(2)  # Delay to avoid rate-limiting
    soup = BeautifulSoup(response.text, 'html.parser')

    listings = soup.find_all('li', class_='s-item')
    prices = []

    for listing in listings:
        price_element = listing.find('span', class_='s-item__price')
        if price_element:
            price_text = price_element.text.strip()
            try:
                price = float(price_text.replace('$', '').replace(',', ''))
                prices.append(price)
            except ValueError:
                continue  # Skip invalid price entries
        
        time.sleep(1)  # Delay to avoid rate-limiting

    if prices:
        average_price = sum(prices) / len(prices)
        return average_price
    else:
        return None


# Main Execution
shoe_name_input = input("Enter the shoe name you want to search for: ")
deal = scrape_goat_and_compare_with_ebay(shoe_name_input)

if deal:
    print(f"\nDeal found for {deal['name']}: GOAT Price - ${deal['goat_price']} | eBay Avg - ${deal['ebay_avg_price']}")
else:
    print(f"No deals found for '{shoe_name_input}'.")
