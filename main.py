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
import json



# Load pincodes and clean area names
df = pd.read_csv('pincode.csv')
target_pincodes = ['560066', '560037']
filtered_df = df[df['Pincode'].astype(str).isin(target_pincodes)]

def clean_office_name(name):
    return re.sub(r'\s*(?:S\.O|SO|B\.O|BO)$', '', name).strip()

# area_list = list(dict.fromkeys(filtered_df['OfficeName'].apply(clean_office_name).tolist()))
area_list = ["Powai", "Kandivali", "Goregaon", "Prabhadevi", "Whitefield", "Hebbal"]


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

def get_location_data(driver):
    
    location_data = {
        "Latitude": None,
        "Longitude": None,
        "Address": None
    }
    
    try:
        # Method 1: Extract from JSON-LD in page source (most reliable)
        page_source = driver.page_source
        json_ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page_source, re.DOTALL)
        
        if json_ld_match:
            try:
                json_data = json.loads(json_ld_match.group(1))
                
                # Look for geo information in all objects
                for item in json_data:
                    if isinstance(item, dict) and "geo" in item:
                        geo = item["geo"]
                        location_data["Address"] = geo.get("address", None)
                        location_data["Latitude"] = geo.get("latitude", None)
                        location_data["Longitude"] = geo.get("longitude", None)
                        break
            except Exception as e:
                print(f"Error parsing JSON-LD: {e}")
        
        # Method 2: If JSON-LD failed, try extracting from DOM elements
        if not location_data["Address"] or not location_data["Latitude"] or not location_data["Longitude"]:
            # Try to find address in DOM
            address_selectors = [
                "div.T_addressTextBlockStyle", 
                "div[class*='addressText']",
                "div[data-q='address']",
                "div.property-address",
                "span.address"
            ]
            
            for selector in address_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].text.strip():
                    location_data["Address"] = elements[0].text.strip()
                    break
            
            # Try to find map element with coordinates
            map_selectors = [
                "div[class*='mapContainer']",
                "div.map-container",
                "div[data-id='map']"
            ]
            
            for selector in map_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Look for coordinates in various attributes
                    for lat_attr in ["data-latitude", "data-lat", "lat"]:
                        lat = elements[0].get_attribute(lat_attr)
                        if lat:
                            location_data["Latitude"] = lat
                            break
                    
                    for lng_attr in ["data-longitude", "data-lng", "lng"]:
                        lng = elements[0].get_attribute(lng_attr)
                        if lng:
                            location_data["Longitude"] = lng
                            break
                    
                    # If we found the map but no coordinates in attributes, check for iframe
                    if not location_data["Latitude"] or not location_data["Longitude"]:
                        iframe = elements[0].find_elements(By.TAG_NAME, "iframe")
                        if iframe:
                            src = iframe[0].get_attribute("src")
                            if src:
                                # Extract coordinates from Google Maps iframe URL
                                lat_match = re.search(r'q=(-?\d+\.\d+)', src)
                                lng_match = re.search(r'q=-?\d+\.\d+,(-?\d+\.\d+)', src)
                                if lat_match:
                                    location_data["Latitude"] = lat_match.group(1)
                                if lng_match:
                                    location_data["Longitude"] = lng_match.group(1)
    
    except Exception as e:
        print(f"Error extracting location data: {e}")
    
    return location_data

def get_project_details(project_url, driver):
    driver.get(project_url)
    time.sleep(5)  # Wait for page to load
    data = {}
    
    location_data = get_location_data(driver)
    data.update(location_data)
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

def parse_feet_inches(dim_str):
            dim_str = dim_str.replace("''", '').replace('"', '').strip()
            feet, inches = 0, 0
            if "'" in dim_str:
                parts = dim_str.split("'")
                feet = int(parts[0].strip())
                if len(parts) > 1 and parts[1].strip().isdigit():
                    inches = int(parts[1].strip())
            return feet + inches / 12.0

def compute_area(size_str):
    try:
        size_str = size_str.strip()
        parts = size_str.split('X')
        if len(parts) != 2:
            return None
        length = parse_feet_inches(parts[0])
        width = parse_feet_inches(parts[1])
        return round(length * width, 2)
    except Exception:
        return None

def process_housing_data(projects, filename="processed_projects_data.xlsx"):
    processed_projects = []
    
    for proj in projects:
        processed_proj = proj.copy()
        
        if 'Configuration' in proj and proj.get('Configuration'):
            processed_proj['Configurations'] = proj['Configuration']
        elif 'Configurations' in proj and proj.get('Configurations'):
            processed_proj['Configurations'] = proj['Configurations']
        
        if 'Configuration' in processed_proj:
            del processed_proj['Configuration']
        
        if 'Avg. Price' in proj and proj.get('Avg. Price'):
            processed_proj['Avg. Price'] = proj['Avg. Price']
        elif 'Price' in proj and proj.get('Price'):
            processed_proj['Avg. Price'] = proj['Price']
        
        if 'Price' in processed_proj:
            del processed_proj['Price']
        
        if 'Sizes' in proj and proj.get('Sizes'):
            processed_proj['Sizes'] = proj['Sizes']
        elif 'Size' in proj and proj.get('Size'):
            processed_proj['Sizes'] = proj['Size']
            
        
        if 'Size' in processed_proj:
            del processed_proj['Size']
        
        
        if 'Avg. Price' in processed_proj and processed_proj['Avg. Price']:
            price_str = str(processed_proj['Avg. Price']).strip()
            def parse_price(p):
                p = p.strip()
                if 'K' in p:
                    return float(p.replace('K', '')) * 1000
                else:
                    return float(p)
            
            price_str = re.sub(r'/sq\.ft|₹|,|\s', '', price_str)
            
            if '-' in price_str:
                lower_price, higher_price = price_str.split('-')
                try:
                    processed_proj['Lower Price'] = parse_price(lower_price)
                    processed_proj['Higher Price'] = parse_price(higher_price)
                except ValueError:
                    processed_proj['Lower Price'] = None
                    processed_proj['Higher Price'] = None
            else:
                try:
                    price_value = parse_price(price_str)
                    processed_proj['Lower Price'] = price_value
                    processed_proj['Higher Price'] = price_value
                except ValueError:
                    processed_proj['Lower Price'] = None
                    processed_proj['Higher Price'] = None
        
        
        if 'Configurations' in processed_proj and processed_proj['Configurations']:
            config_str = str(processed_proj['Configurations']).strip()
            
            
            if 'Apartment' in config_str and 'Villa' in config_str:
                processed_proj['Product Type'] = 'Apartment, Villa'
            elif 'Apartment' in config_str:
                processed_proj['Product Type'] = 'Apartment'
            elif 'Villa' in config_str:
                processed_proj['Product Type'] = 'Villa'
            else:
                processed_proj['Product Type'] = ''
            
            

            # Example: "2, 3, 4 BHK Apartments"
            config_str = config_str.strip()

            # Match patterns like "1, 2, 3.5 BHK" or "4 BHK", etc.
            matches = re.findall(r'((?:\d(?:\.5)?(?:,\s*)?)+)\s*BHK', config_str)

            bhk_numbers = []
            for match in matches:
                # Split by comma and strip
                bhk_numbers.extend([x.strip() for x in match.split(',') if x.strip()])

            # Remove duplicates
            bhk_numbers = set(bhk_numbers)

            # Initialize all as 'No'
            bhk_types = ['1BHK', '1.5BHK', '2BHK', '2.5BHK', '3BHK', '3.5BHK', '4BHK', '4.5BHK', '5BHK']
            for bhk in bhk_types:
                processed_proj[bhk] = 'Yes' if bhk.replace('BHK', '') in bhk_numbers else 'No'
        
        
        if 'Project Size' in processed_proj and processed_proj['Project Size']:
            project_size = str(processed_proj['Project Size']).strip()
            buildings_match = re.search(r'(\d+)\s*Buildings', project_size)
            units_match = re.search(r'(\d+)\s*units', project_size)
            
            if buildings_match:
                processed_proj['Buildings'] = int(buildings_match.group(1))
            else:
                processed_proj['Buildings'] = None
                
            if units_match:
                processed_proj['Units'] = int(units_match.group(1))
            else:
                processed_proj['Units'] = None
        
        
        if 'Sizes' in processed_proj and processed_proj['Sizes']:
            sizes_str = str(processed_proj['Sizes']).strip()
            sizes_str = re.sub(r'sq\.ft\.|,|\s', '', sizes_str)
            
            if '-' in sizes_str:
                lower_size, upper_size = sizes_str.split('-')
                processed_proj['Lower Size Range'] = float(lower_size.strip())
                processed_proj['Upper Size Range'] = float(upper_size.strip())
            else:
                try:
                    processed_proj['Lower Size Range'] = float(sizes_str)
                    processed_proj['Upper Size Range'] = float(sizes_str)
                except ValueError:
                    processed_proj['Lower Size Range'] = None
                    processed_proj['Upper Size Range'] = None

        if 'Parking' in processed_proj and processed_proj['Parking']:
            parking_str = str(processed_proj['Parking']).lower()
            if 'open' in parking_str:
                processed_proj['Parking Type'] = 'Open'
            elif 'covered' in parking_str:
                processed_proj['Parking Type'] = 'Covered'
            else:
                processed_proj['Parking Type'] = 'Unknown'

            num_match = re.search(r'(\d+)', parking_str)
            processed_proj['Number of Parking'] = int(num_match.group(1)) if num_match else 0

        
        if 'Project Area' in processed_proj and processed_proj['Project Area']:
            area_str = str(processed_proj['Project Area']).strip()
            area_match = re.search(r'([\d.]+)\s*Acres', area_str)
            open_match = re.search(r'\(([\d.]+)%\s*open\)', area_str, re.IGNORECASE)

            if area_match:
                total_area = float(area_match.group(1))
                processed_proj['Total Project Area (Acres)'] = total_area

                if open_match:
                    open_pct = float(open_match.group(1))
                    open_area = round((open_pct / 100.0) * total_area, 2)
                    closed_area = round(total_area - open_area, 2)
                    processed_proj['Open Area (Acres)'] = open_area
                    processed_proj['Closed Area (Acres)'] = closed_area
                else:
                    processed_proj['Open Area (Acres)'] = ''
                    processed_proj['Closed Area (Acres)'] = ''
        
        
        if ('Lower Price' in processed_proj and processed_proj['Lower Price'] is not None and
            'Lower Size Range' in processed_proj and processed_proj['Lower Size Range'] is not None):
            processed_proj['Total Cost Lower Range'] = processed_proj['Lower Price'] * processed_proj['Lower Size Range']
        else:
            processed_proj['Total Cost Lower Range'] = None
            
        if ('Higher Price' in processed_proj and processed_proj['Higher Price'] is not None and
            'Upper Size Range' in processed_proj and processed_proj['Upper Size Range'] is not None):
            processed_proj['Total Cost Upper Range'] = processed_proj['Higher Price'] * processed_proj['Upper Size Range']
        else:
            processed_proj['Total Cost Upper Range'] = None
        
        if 'Floor Details' in processed_proj and processed_proj['Floor Details']:
            floor_details = processed_proj['Floor Details']
            if isinstance(floor_details, str):
                try:
                    floor_details = floor_details.replace("'", '"')
                    if not floor_details.startswith('['):
                        floor_details = '[' + floor_details + ']'
                    floor_details = json.loads(floor_details)
                except json.JSONDecodeError:
                    room_details = []
                    
                    
                    pattern1 = r"{'room': '([^']+)', 'size': '([^']+)'}"
                    matches = re.findall(pattern1, floor_details)
                    for room, size in matches:
                        room_details.append({"room": room, "size": size})
                    
                    
                    if not room_details and ';' in floor_details:
                        parts = floor_details.split(';')
                        for part in parts:
                            part = part.strip()
                            if not part:
                                continue
                            room_match = re.search(r"'room': '([^']+)'", part)
                            size_match = re.search(r"'size': '([^']+)'", part)
                            if room_match and size_match:
                                room = room_match.group(1)
                                size = size_match.group(1)
                                room_details.append({"room": room, "size": size})
                    
                    floor_details = room_details
            
            
            room_count = 1
            for room_info in floor_details:
                if isinstance(room_info, dict) and 'room' in room_info and 'size' in room_info:
                    room_name = f"Room{room_count}"
                    processed_proj[room_name] = room_info['room']
                    processed_proj[f"{room_name} Size"] = room_info['size']
                    room_count += 1

        for key in list(processed_proj.keys()):
            if key.startswith('Room') and key.endswith('Size'):
                room_number = key.split(' ')[0]
                size_str = processed_proj[key]
                area = compute_area(size_str)
                processed_proj[f"{room_number} Area"] = area
        
        
        if 'Project Specifications' in processed_proj and processed_proj['Project Specifications']:
            spec_str = str(processed_proj['Project Specifications']).strip()
            
            
            living_dining_match = re.search(r'Living/Dining\s*:\s*([^,]+)', spec_str)
            if living_dining_match:
                processed_proj['Living/Dining Floor'] = living_dining_match.group(1).strip()
                
            master_bedroom_match = re.search(r'Master Bedroom\s*:\s*([^,]+)', spec_str)
            if master_bedroom_match:
                processed_proj['Master Bedroom Floor'] = master_bedroom_match.group(1).strip()
                
            other_bedroom_match = re.search(r'Other Bedroom\s*:\s*([^,]+)', spec_str)
            if other_bedroom_match:
                processed_proj['Other Bedroom Floor'] = other_bedroom_match.group(1).strip()
                
            kitchen_match = re.search(r'Kitchen\s*:\s*([^,]+)', spec_str)
            if kitchen_match:
                processed_proj['Kitchen Floor'] = kitchen_match.group(1).strip()
                
            toilets_match = re.search(r'Toilets\s*:\s*([^,]+)', spec_str)
            if toilets_match:
                processed_proj['Toilets Floor'] = toilets_match.group(1).strip()
                
            balcony_match = re.search(r'Balcony\s*:\s*([^,]+)', spec_str)
            if balcony_match:
                processed_proj['Balcony Floor'] = balcony_match.group(1).strip()
        
        processed_projects.append(processed_proj)
    
    df = pd.DataFrame(processed_projects)
    df.to_excel(filename, index=False)
    print(f"Saved {len(processed_projects)} processed projects to {filename}")
    return processed_projects


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
                print(f"{area}: {len(data['Top Projects'])} projects, {len(data['Nearby Places'])} places, {len(data['Amenities'])} amenities")
            else:
                print(f"Failed to scrape {area}")
            
            # Go back to homepage
            driver.get("https://housing.com/")
            time.sleep(5)

        # Display summary
        print("\n--- Final Results ---")

        all_project_details = []
        for result in results:
            area_name = result['Area']
            for title, link in result['Top Projects']:
                data2 = get_project_details(link, driver)
                data2['Area'] = area_name
                data2['Title'] = title
                data2['Link'] = link
                all_project_details.append(data2)

        # Save to CSV
        # save_projects_to_csv(all_project_details, "projects_data.csv")
        process_housing_data(all_project_details, "processed_projects_data.xlsx")
            

            

    finally:
        driver.quit()

if __name__ == "__main__":
    main()