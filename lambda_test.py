import os
import time
import boto3
import json
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from headless_chrome import create_driver


def convert_to_csv(data):
    csv_string = ''
    header = ','.join(data[0].keys())
    csv_string += header + '\\n'
    for entry in data:
        row = ','.join(str(entry[key]) for key in entry)
        csv_string += row + '\\n'
    return csv_string


def lambda_handler(event, context):
    keyword = event.get('keyword')
    verbose = event.get('verbose', False)
    max_restaurants = event.get('max_restaurants', 0)
    offset = event.get('offset', 0)
    
    driver = create_driver()

    restaurants_data, next_offset = get_restaurants(keyword, verbose, max_restaurants, offset, driver)
    if restaurants_data:
        # Create the CSV buffer
        aws_access_key_id = 'ACCESS_KEY_ID'
        aws_secret_access_key = 'SECRET_ACCESS_KEY'
        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        bucket_name = 'kelly-test-video'
        timestamp = int(time.time())
        file_key = f'data/{keyword}/{timestamp}_restaurants.csv'
        csv_buffer = convert_to_csv(restaurants_data)
        s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer)
    else:
        print("No restaurant data collected.")
    driver.quit()

    if next_offset is not None and next_offset == max_restaurants:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'{max_restaurants} restaurants data uploaded to S3 successfully.'})
        }
    elif next_offset is not None:
        return {
            'statusCode': 200,
            'body': json.dumps({'next_offset': next_offset})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Restaurant data uploaded to S3 successfully.'})
        }


def get_restaurants(keyword, verbose, max_restaurants, offset, driver):
    url = 'https://www.swiggy.com/city/' + keyword
    driver.get(url)
    restaurants = []
    collected_successfully = False
    time.sleep(3)

    max_attempts = 5  # Set the maximum number of attempts
    attempt_count = 0
    z = 1
    while attempt_count < max_attempts:
        try:
            # Wait for the button to be present on the page
            button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='RestaurantList__ShowMoreContainer-sc-1d3nl43-0 brTFTS']//child::div[1]"))
            )

            # Click the button
            button.click()
            time.sleep(2)

        except StaleElementReferenceException:
            print("StaleElementReferenceException: Button is no longer attached to the DOM.")

        except TimeoutException:
            print("Timeout: Button not found within the specified time.")
            break  # Exit the loop if the button is not found within the timeout

        # Increment the attempt count
        attempt_count += 1

    res_number = driver.find_elements(By.XPATH, '//div[@class="sc-gLLvby jXGZuP"]//child::div//child::a')
    print(len(res_number))

    rest_links = driver.find_elements(By.XPATH, './/div[@class="sc-gLLvby jXGZuP"]//child::div//child::a')

    # Modify the loop to start from the specified offset
    for idx, rest_link in enumerate(rest_links[offset:], start=offset):
        try:
            action_chains = ActionChains(driver)
            action_chains.key_down(Keys.CONTROL).click(rest_link).key_up(Keys.CONTROL).perform()

            # Switch to the new tab (assuming it's the last tab opened)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)

            try:
                print("Progress: ( {} / {})".format(idx + 1, min(len(res_number), offset + max_restaurants)))
                try:
                    rest_name_ele = driver.find_element(By.XPATH, ".//p[@class='RestaurantNameAddress_name__2IaTv']")
                except NoSuchElementException:
                    print("Element not found. Skipping to the next restaurant.")
                    try:
                        driver.close()
                    except Exception as e:
                        print(f"Error during window close: {str(e)}")  # Close the current tab
                    driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab
                    continue  # Skip to the next iteration of the loop

                except StaleElementReferenceException:
                    time.sleep(5)
                    print("StaleElementReferenceException: Element is no longer attached to the DOM. Trying again.")
                cuisine_ele = driver.find_element(By.XPATH, "//p[@class='RestaurantNameAddress_cuisines__mBHr2']")
                area_ele = driver.find_element(By.XPATH, "//div[@class='RestaurantNameAddress_areaWrapper__3HIxj']")
                rating_ele = driver.find_element(By.XPATH, "//span[@class='RestaurantRatings_avgRating__1TOWY']//child::span[2]")
                number_rating_ele = driver.find_element(By.XPATH, "//span[@class='RestaurantRatings_totalRatings__3d6Zc']")
                avg_price_ele = driver.find_element(By.XPATH, "(//li[@class='RestaurantTimeCost_item__2HCUz']//child::span)[2]")
                offer_number_ele = driver.find_elements(By.XPATH, "//button[@class='RestaurantOffer_wrapper__2ihLc']")
                offer_name_ele = driver.find_elements(By.XPATH, "//button[@class='RestaurantOffer_wrapper__2ihLc']")
                try:
                    pure_veg_ele = driver.find_element(By.XPATH, "//div[@class='styles_pureVeg__hu43p']")
                    pure_veg = 'Yes'
                except NoSuchElementException:
                    pure_veg = 'No'
            except StaleElementReferenceException:
                print("StaleElementReferenceException: Button is no longer attached to the DOM.")

            try:
                rest_name = rest_name_ele.text if rest_name_ele else -1
                cuisine = cuisine_ele.text if cuisine_ele else -1
                area = area_ele.text if area_ele else -1
                rating = rating_ele.text if rating_ele else -1
                number_rating = number_rating_ele.text if number_rating_ele else -1
                avg_price = avg_price_ele.text if avg_price_ele else -1
                offer_number = len(offer_number_ele) if offer_number_ele else -1

                offer_name = ""  # Initialize offer_name before the loop

                if offer_number_ele:
                    for i in range(offer_number):
                        temp = offer_name_ele[i].text
                        offer_name += temp + ", "
                    # Remove the trailing comma and space if offer_name is not -1
                    offer_name = offer_name[:-2] if offer_name else -1

                location = keyword
                collected_successfully = True
            except Exception as e:
                time.sleep(5)
                collected_successfully = True

            if verbose:
                print("Restaurant Name: {}".format(rest_name))
                print("Cuisine : {}".format(cuisine))
                print("Rating: {}".format(rating))
                print("Number of Ratings: {}".format(number_rating))
                print("Average Price : {}".format(avg_price))
                print("Number of Offers: {}".format(offer_number))
                print("Offer Name: {}".format(offer_name))
                print("Area : {}".format(area))
                print("Pure Veg: {}".format(pure_veg))
                print("Location: {}".format(location))

            restaurant_data = {
                "Restaurant Name": rest_name,
                "Cuisine": cuisine,
                "Rating": rating,
                "Number of Ratings": number_rating,
                "Average Price": avg_price,
                "Number of Offers": offer_number,
                "Offer Name": offer_name,
                "Area": area,
                "Pure Veg": pure_veg,
                "Location": location
            }
            restaurants.append(restaurant_data)

            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)

            try:
                driver.close()
            except Exception as e:
                print(f"Error during window close: {str(e)}")

            driver.switch_to.window(driver.window_handles[0])

            # Break the loop if the desired number of restaurants have been scraped
            if len(restaurants) >= offset + max_restaurants:
                next_offset = offset + len(restaurants)
                return restaurants, next_offset

        except StaleElementReferenceException:
            time.sleep(5)
            print("StaleElementReferenceException: Element is no longer attached to the DOM. Trying again.")

    # If the loop completes without reaching the desired number of restaurants
    return restaurants, None