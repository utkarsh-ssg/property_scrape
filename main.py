import pandas as pd
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
from datetime import datetime
import csv

# Load pincodes and clean area names
df = pd.read_csv('pincode.csv')
target_pincodes = ['560066', '560037']
filtered_df = df[df['Pincode'].astype(str).isin(target_pincodes)]

def clean_office_name(name):
    return re.sub(r'\s*(?:S\.O|SO|B\.O|BO)$', '', name).strip()

area_list = list(dict.fromkeys(filtered_df['OfficeName'].apply(clean_office_name).tolist()))

def get_nearby_places(driver):
    places = []
    try:
        place_elements = driver.find_elements(By.CSS_SELECTOR, "div._9s1txw._fc1yb4._h31y44._7l9ke2.T_placeDistanceContainerStyle")
        for elem in place_elements:
            try:
                place_name = elem.find_element(By.CSS_SELECTOR, "div.T_placeNameStyle").text.strip()
                place_type = elem.find_element(By.CSS_SELECTOR, "div.T_nameStyle").text.strip()
                duration = elem.find_element(By.CSS_SELECTOR, "div.T_durationStyle").text.strip()
                distance = elem.find_element(By.CSS_SELECTOR, "div.T_distanceStyle").text.strip()
                places.append({
                    "Place Name": place_name,
                    "Type": place_type,
                    "Distance": distance,
                    "Duration": duration
                })
            except:
                continue
    except Exception as e:
        print(f"Error getting nearby places: {e}")
    return places

def get_amenities(driver):
    amenities = []
    try:
        amenities_elements = driver.find_elements(By.CSS_SELECTOR, "div.T_cellStyle")
        for elem in amenities_elements:
            try:
                label = elem.find_element(By.CSS_SELECTOR, "div.T_amenityLabelStyle").text.strip()
                amenities.append(label)
            except:
                continue
    except Exception as e:
        print(f"Error getting amenities: {e}")
    return amenities

def get_project_specifications(driver):
    specs = defaultdict(list)
    
    try:
        # Find and expand all sections
        try:
            # Try to find "See all" buttons and click them
            see_all_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'See all')]")
            for button in see_all_buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass
        
        # Try multiple selectors for specification sections
        section_selectors = [
            "div.questions-container", 
            "div[class*='specificationSection']",
            "div.specification-section"
        ]
        
        for selector in section_selectors:
            spec_sections = driver.find_elements(By.CSS_SELECTOR, selector)
            if spec_sections:
                break
        
        # Process each specification section
        for section in spec_sections:
            section_name = "General"
            
            # Try to extract section name
            try:
                name_selectors = [
                    "h3.T_name > div",
                    "h3[class*='sectionName'] > div",
                    "div.section-title"
                ]
                
                for name_selector in name_selectors:
                    name_elems = section.find_elements(By.CSS_SELECTOR, name_selector)
                    if name_elems and name_elems[0].text.strip():
                        section_name = name_elems[0].text.strip()
                        break
            except:
                pass
            
            # Try to extract detail rows
            detail_selectors = [
                "div.T_additionalLabelStyle",
                "div[class*='specificationDetail']",
                "div.spec-row"
            ]
            
            for detail_selector in detail_selectors:
                detail_divs = section.find_elements(By.CSS_SELECTOR, detail_selector)
                if detail_divs:
                    for detail_div in detail_divs:
                        try:
                            key_selectors = [
                                "span.T_furnishingLabelKeyStyle", 
                                "span[class*='labelKey']",
                                "span.spec-key"
                            ]
                            value_selectors = [
                                "span.T_furnishingLabelValueStyle",
                                "span[class*='labelValue']",
                                "span.spec-value"
                            ]
                            
                            key = None
                            value = None
                            
                            # Get key
                            for selector in key_selectors:
                                key_elems = detail_div.find_elements(By.CSS_SELECTOR, selector)
                                if key_elems and key_elems[0].text.strip():
                                    key = key_elems[0].text.strip()
                                    break
                            
                            # Get value
                            for selector in value_selectors:
                                value_elems = detail_div.find_elements(By.CSS_SELECTOR, selector)
                                if value_elems and value_elems[0].text.strip():
                                    value = value_elems[0].text.strip()
                                    break
                            
                            if key and value:
                                specs[section_name].append(f"{key} : {value}")
                        except Exception as e:
                            print(f"Error parsing spec detail: {e}")
                    
                    # If we found details, break the selector loop
                    if specs[section_name]:
                        break
            
            # Alternative approach for table-style specifications
            if not specs[section_name]:
                try:
                    rows = section.find_elements(By.CSS_SELECTOR, "tr")
                    for row in rows:
                        cols = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(cols) >= 2:
                            key = cols[0].text.strip()
                            value = cols[1].text.strip()
                            if key and value:
                                specs[section_name].append(f"{key} : {value}")
                except:
                    pass
        
        # Remove empty sections
        return {k: v for k, v in specs.items() if v}
    
    except Exception as e:
        print(f"Error while fetching specifications: {e}")
    
    return dict(specs)

def get_project_specifications(driver):
    specs = defaultdict(list)
    
    try:
        # Find and expand all sections
        try:
            # Try to find "See all" buttons and click them
            see_all_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'See all')]")
            for button in see_all_buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass
        
        # Try multiple selectors for specification sections
        section_selectors = [
            "div.questions-container", 
            "div[class*='specificationSection']",
            "div.specification-section"
        ]
        
        for selector in section_selectors:
            spec_sections = driver.find_elements(By.CSS_SELECTOR, selector)
            if spec_sections:
                break
        
        # Process each specification section
        for section in spec_sections:
            section_name = "General"
            
            # Try to extract section name
            try:
                name_selectors = [
                    "h3.T_name > div",
                    "h3[class*='sectionName'] > div",
                    "div.section-title"
                ]
                
                for name_selector in name_selectors:
                    name_elems = section.find_elements(By.CSS_SELECTOR, name_selector)
                    if name_elems and name_elems[0].text.strip():
                        section_name = name_elems[0].text.strip()
                        break
            except:
                pass
            
            # Try to extract detail rows
            detail_selectors = [
                "div.T_additionalLabelStyle",
                "div[class*='specificationDetail']",
                "div.spec-row"
            ]
            
            for detail_selector in detail_selectors:
                detail_divs = section.find_elements(By.CSS_SELECTOR, detail_selector)
                if detail_divs:
                    for detail_div in detail_divs:
                        try:
                            key_selectors = [
                                "span.T_furnishingLabelKeyStyle", 
                                "span[class*='labelKey']",
                                "span.spec-key"
                            ]
                            value_selectors = [
                                "span.T_furnishingLabelValueStyle",
                                "span[class*='labelValue']",
                                "span.spec-value"
                            ]
                            
                            key = None
                            value = None
                            
                            # Get key
                            for selector in key_selectors:
                                key_elems = detail_div.find_elements(By.CSS_SELECTOR, selector)
                                if key_elems and key_elems[0].text.strip():
                                    key = key_elems[0].text.strip()
                                    break
                            
                            # Get value
                            for selector in value_selectors:
                                value_elems = detail_div.find_elements(By.CSS_SELECTOR, selector)
                                if value_elems and value_elems[0].text.strip():
                                    value = value_elems[0].text.strip()
                                    break
                            
                            if key and value:
                                specs[section_name].append(f"{key} : {value}")
                        except Exception as e:
                            print(f"Error parsing spec detail: {e}")
                    
                    # If we found details, break the selector loop
                    if specs[section_name]:
                        break
            
            # Alternative approach for table-style specifications
            if not specs[section_name]:
                try:
                    rows = section.find_elements(By.CSS_SELECTOR, "tr")
                    for row in rows:
                        cols = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(cols) >= 2:
                            key = cols[0].text.strip()
                            value = cols[1].text.strip()
                            if key and value:
                                specs[section_name].append(f"{key} : {value}")
                except:
                    pass
        
        # Remove empty sections
        return {k: v for k, v in specs.items() if v}
    
    except Exception as e:
        print(f"Error while fetching specifications: {e}")
    
    return dict(specs)


def get_floor_plan_details(driver):
    floor_plan_data = []
    
    try:
        # Try multiple selectors for floor plan elements
        room_selectors = [
            "div.T_roomDetails", 
            "div[class*='roomDetail']",
            "div.floor-plan-room"
        ]
        
        for selector in room_selectors:
            room_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if room_elements:
                break
        
        for room in room_elements:
            room_data = {}
            
            # Get room name
            try:
                name_selectors = [
                    "div.T_nameStyle", 
                    "div[class*='roomName']",
                    "div.room-name"
                ]
                
                for selector in name_selectors:
                    name_elems = room.find_elements(By.CSS_SELECTOR, selector)
                    if name_elems and name_elems[0].text.strip():
                        room_data["room"] = name_elems[0].text.strip()
                        break
            except Exception as e:
                room_data["room"] = "Unknown Room"
            
            # Get room size
            try:
                size_selectors = [
                    "div.T_sizeStyle", 
                    "div[class*='roomSize']",
                    "div.room-size"
                ]
                
                for selector in size_selectors:
                    size_elems = room.find_elements(By.CSS_SELECTOR, selector)
                    if size_elems and size_elems[0].text.strip():
                        room_data["size"] = size_elems[0].text.strip()
                        break
            except Exception as e:
                room_data["size"] = "Unknown Size"
            
            if "room" in room_data and room_data["room"] != "Unknown Room":
                floor_plan_data.append(room_data)
    
    except Exception as e:
        print(f"Error extracting floor plan: {e}")
    
    return floor_plan_data


def get_last_updated_date(driver):
    try:
        # Try multiple ways to find the last updated date
        selectors = [
            "//div[contains(text(),'Last updated:')]",
            "//div[contains(text(),'Updated on:')]",
            "//span[contains(text(),'Last updated')]"
        ]
        
        for selector in selectors:
            try:
                last_updated_elem = driver.find_element(By.XPATH, selector)
                text = last_updated_elem.text.strip()
                # Extract the date portion with regex
                date_match = re.search(r'(?:Last updated:|Updated on:)\s*(.+)', text)
                if date_match:
                    return date_match.group(1).strip()
                return text  # Return the full text if regex doesn't match
            except:
                continue
                
        return "N/A"
    except Exception as e:
        print(f"Error while fetching last updated date: {e}")
        return "N/A"


def get_project_details(project_url, driver):
    driver.get(project_url)
    time.sleep(5)  # Wait for page to load
    data = {}
    
    print(f"Getting data for: {project_url}")
    
    # Scroll to ensure dynamic content loads
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 500)")
        time.sleep(1)
    
    # Get basic overview info from table
    try:
        table_selectors = [
            "tbody.T_overviewStyle tr.data-point",
            "tr[class*='dataPoint']",
            "div.overview-table tr"
        ]
        
        for selector in table_selectors:
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
            if rows:
                for row in rows:
                    try:
                        label_selectors = [".T_labelStyle", "[class*='labelStyle']", "td.label"]
                        value_selectors = [".T_valueStyle", "[class*='valueStyle']", "td.value"] 
                        
                        label = None
                        value = None
                        
                        # Try to find label
                        for label_selector in label_selectors:
                            label_elems = row.find_elements(By.CSS_SELECTOR, label_selector)
                            if label_elems and label_elems[0].text.strip():
                                label = label_elems[0].text.strip()
                                break
                        
                        # Try to find value
                        for value_selector in value_selectors:
                            value_elems = row.find_elements(By.CSS_SELECTOR, value_selector)
                            if value_elems and value_elems[0].text.strip():
                                value = value_elems[0].text.strip()
                                break
                        
                        if label and value:
                            data[label] = value
                    except Exception as e:
                        print(f"Error extracting row data: {e}")
                break  # Break if we found and processed rows
    except Exception as e:
        print(f"Error extracting overview: {e}")
    
    # Get developer name
    try:
        developer_selectors = [
            "[data-q='dev-name']",
            "div[class*='developerName']", 
            "div.developer-name"
        ]
        
        for selector in developer_selectors:
            developer_elems = driver.find_elements(By.CSS_SELECTOR, selector)
            if developer_elems and developer_elems[0].text.strip():
                data["Developer"] = developer_elems[0].text.strip()
                break
    except Exception as e:
        print("Developer name not found:", e)
    
    # Get additional data
    last_updated_date = get_last_updated_date(driver)
    nearby_places = get_nearby_places(driver)
    amenities = get_amenities(driver)
    specs = get_project_specifications(driver)
    floor_details = get_floor_plan_details(driver)
    
    # Get price information
    try:
        price_selectors = [
            "span[data-q='price']",
            "div[class*='priceValue']",
            "div.property-price"
        ]
        
        for selector in price_selectors:
            price_elems = driver.find_elements(By.CSS_SELECTOR, selector)
            if price_elems and price_elems[0].text.strip():
                data["Price"] = price_elems[0].text.strip()
                break
    except Exception as e:
        print(f"Error extracting price: {e}")
    
    # Add to data dictionary
    data["Last Updated"] = last_updated_date
    data["Nearby Places"] = nearby_places
    data["Amenities"] = amenities
    data["Project Specifications"] = specs
    data["Floor Details"] = floor_details
    
    # Take a screenshot for debugging
    try:
        screenshot_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        # driver.save_screenshot(screenshot_name)
        print(f"Screenshot saved as {screenshot_name}")
    except:
        pass
    
    return data


def search_and_scrape_area(area_name, driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # Close any popups if present
        try:
            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class*='popup-close']"))
            )
            close_btn.click()
            time.sleep(1)
        except:
            pass

        # Search box
        search_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Search for']"))
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(f"{area_name}, Bangalore")
        time.sleep(2)
        search_input.send_keys(Keys.RETURN)
        time.sleep(6)

        # Scroll down to load all listings
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        # Extract info
        nearby_places = get_nearby_places(driver)
        amenities = get_amenities(driver)

        # Get top 5 projects
        project_links = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.infoTopContainer")
        for card in cards[:5]:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "[data-q='title']")
                title = title_elem.text.strip()
                link = title_elem.get_attribute("href")
                project_links.append((title, link))
            except:
                continue

        return {
            "Area": area_name,
            "Nearby Places": nearby_places,
            "Amenities": amenities,
            "Top Projects": project_links
        }

    except Exception as e:
        print(f"Error scraping {area_name}: {e}")
        # driver.save_screenshot(f"error_{area_name}.png")
        return None
    

def save_projects_to_csv(projects, filename="projects_data.csv"):
    """
    Save a list of project data dictionaries to a CSV file.
    Handles nested lists/dicts by converting them to strings.
    """
    # Flatten all keys that might appear
    all_keys = set()
    for proj in projects:
        all_keys.update(proj.keys())
    all_keys = list(all_keys)

    # Prepare rows for CSV
    rows = []
    for proj in projects:
        row = {}
        for key in all_keys:
            value = proj.get(key, "")
            # Convert lists/dicts to string
            if isinstance(value, list):
                # For list of dicts (e.g., Nearby Places), join as string
                if value and isinstance(value[0], dict):
                    value = "; ".join([str(item) for item in value])
                else:
                    value = "; ".join(map(str, value))
            elif isinstance(value, dict):
                value = "; ".join([f"{k}: {', '.join(map(str, v))}" for k, v in value.items()])
            row[key] = value
        rows.append(row)

    # Write to CSV
    df = pd.DataFrame(rows, columns=all_keys)
    df.to_csv(filename, index=False)
    print(f"Saved {len(rows)} projects to {filename}")


def main():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://housing.com/")
        time.sleep(5)

        results = []

        for area in area_list:
            print(f"\nScraping {area}...")
            data = search_and_scrape_area(area, driver)
            if data:
                results.append(data)
                print(f"✅ {area}: {len(data['Top Projects'])} projects, {len(data['Nearby Places'])} places, {len(data['Amenities'])} amenities")
            else:
                print(f"❌ Failed to scrape {area}")
            
            # Go back to homepage
            driver.get("https://housing.com/")
            time.sleep(5)

        # Display summary
        print("\n--- Final Results ---")
        for result in results:
            print(f"\n=== {result['Area']} ===")
            print("Top Projects:")
            for title, link in result['Top Projects']:
                print(f"- {title}: {link}")
                data2 = get_project_details(link,driver)
                print(data2)
            print("Nearby Places:")
            for place in result['Nearby Places'][:5]:
                print(f"- {place['Place Name']} ({place['Type']}) - {place['Distance']}")
            print("Amenities:")
            for amenity in result['Amenities'][:10]:
                print(f"- {amenity}")

            all_project_details = []
            for result in results:
                area_name = result['Area']
                for title, link in result['Top Projects']:
                    data2 = get_project_details(link, driver)
                    data2['Area'] = area_name
                    all_project_details.append(data2)

            # Save to CSV
            save_projects_to_csv(all_project_details, "projects_data.csv")

            

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
