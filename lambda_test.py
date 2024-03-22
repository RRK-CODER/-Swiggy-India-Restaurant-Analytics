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


def lambda_handler(event, context):
    # Retrieve keyword and verbose flag from environment variables
    keyword = event.get('keyword', 'mumbai')  # default to 'mumbai' if keyword is not provided
    verbose = event.get('verbose', True)  # default to True if verbose is not provided
    # Create the headless Chrome/Chromium driver instance
    driver = create_driver()

    # Call the get_restaurants function
    df = get_restaurants(keyword, verbose, driver)

    s3_client = boto3.client('s3')
    bucket_name = 'S3_BUCKET_NAME'  #enter your s3 bucket
    timestamp = int(time.time())
    file_key = f'data/{keyword}/{timestamp}_restaurants.csv'
    csv_buffer = df.to_csv(None)
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer)

    # Clean up resources
    driver.quit()

    return {
        'statusCode': 200,
        'body': 'CSV file uploaded to S3 successfully.'
    }


def get_restaurants(keyword, verbose, driver):
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

    for rest_link in rest_links:
        try:
            action_chains = ActionChains(driver)
            action_chains.key_down(Keys.CONTROL).click(rest_link).key_up(Keys.CONTROL).perform()

            # Switch to the new tab (assuming it's the last tab opened)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)

            try:
                print("Progress: ( {} / {})".format(z, len(res_number)))
                z = z + 1
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
        except StaleElementReferenceException:
            time.sleep(5)
            print("StaleElementReferenceException: Element is no longer attached to the DOM. Trying again.")

    return restaurants