#from telnetlib import EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_restaurants(keyword, verbose):
    options = webdriver.ChromeOptions()
    driver = webdriver.Edge()
    driver.set_window_size(1120, 1000)

    url = 'https://www.swiggy.com/city/' + keyword
    driver.get(url)
    rest = []
    collected_successfully = False
    time.sleep(3)

    max_attempts = 5  # Set the maximum number of attempts
    attempt_count = 0
    z=1
    while attempt_count < max_attempts:
        try:
            # Wait for the button to be present on the page
            button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='RestaurantList__ShowMoreContainer-sc-1d3nl43-0 brTFTS']//child::div[1]"))
            )

            # Click the button
            button.click()
            time.sleep(2)
            #print("Button clicked successfully.")

        except StaleElementReferenceException:
            print("StaleElementReferenceException: Button is no longer attached to the DOM.")

        except TimeoutException:
            print("Timeout: Button not found within the specified time.")
            break  # Exit the loop if the button is not found within the timeout
            # Increment the attempt count
            attempt_count += 1

    res_number = driver.find_elements(By.XPATH, '//div[@class="sc-gLLvby jXGZuP"]//child::div//child::a')
    print(len(res_number))

    # for i in range(10):


    rest_links = driver.find_elements(By.XPATH, './/div[@class="sc-gLLvby jXGZuP"]//child::div//child::a')

    #rest_link = rest_link_ele[i].click()
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

                        # ... (rest of the code to extract information)

                    except StaleElementReferenceException:
                        time.sleep(5)
                        print("StaleElementReferenceException: Element is no longer attached to the DOM. Trying again.")
                    cuisine_ele = driver.find_element(By.XPATH, "//p[@class='RestaurantNameAddress_cuisines__mBHr2']")
                    area_ele = driver.find_element(By.XPATH, "//div[@class='RestaurantNameAddress_areaWrapper__3HIxj']")
                    rating_ele = driver.find_element(By.XPATH,"//span[@class='RestaurantRatings_avgRating__1TOWY']//child::span[2]")
                    number_rating_ele = driver.find_element(By.XPATH, "//span[@class='RestaurantRatings_totalRatings__3d6Zc']")
                    avg_price_ele = driver.find_element(By.XPATH,"(//li[@class='RestaurantTimeCost_item__2HCUz']//child::span)[2]")
                    offer_number_ele = driver.find_elements(By.XPATH, "//button[@class='RestaurantOffer_wrapper__2ihLc']")
                    #print(len(offer_number_ele))
                    offer_name_ele = driver.find_elements(By.XPATH, "//button[@class='RestaurantOffer_wrapper__2ihLc']")
                    try:
                        pure_veg_ele = driver.find_element(By.XPATH, "//div[@class='styles_pureVeg__hu43p']")
                        pure_veg = 'Yes'
                    except NoSuchElementException:
                        pure_veg = 'No'
                except StaleElementReferenceException:
                    print("StaleElementReferenceException: Button is no longer attached to the DOM.")

                try:
                    try:
                        rest_name = rest_name_ele.text
                    except NoSuchElementException:
                        rest_name = -1
                    try:
                        cuisine = cuisine_ele.text
                    except NoSuchElementException:
                        cuisine = -1
                    try:
                        area = area_ele.text
                    except NoSuchElementException:
                        area = -1
                    try:
                        rating = rating_ele.text
                    except NoSuchElementException:
                        rating = -1
                    try:
                        number_rating = number_rating_ele.text
                    except NoSuchElementException:
                        number_rating = -1
                    try:
                        avg_price = avg_price_ele.text
                    except NoSuchElementException:
                        avg_price = -1
                    try:
                        offer_number = len(offer_number_ele)
                    except NoSuchElementException:
                        offer_number = -1

                    # ... (previous code)

                    offer_name = ""  # Initialize offer_name before the loop

                    try:
                        for i in range(offer_number):
                            temp = offer_name_ele[i].text
                            #print(temp)
                            offer_name += temp + ", "
                            #print(offer_name)
                            # Concatenate offer names with a comma and space
                    except NoSuchElementException:
                        offer_name = -1

                    # Remove the trailing comma and space if offer_name is not -1
                    offer_name = offer_name[:-2] if offer_name != -1 else -1


                    location = keyword
                    collected_successfully = True
                except:
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

                rest.append({
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
                })
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)

                try:
                    driver.close()
                except Exception as e:
                    print(f"Error during window close: {str(e)}")

                #time.sleep(2)
                driver.switch_to.window(driver.window_handles[0])
            except StaleElementReferenceException:
                time.sleep(5)
                print("StaleElementReferenceException: Element is no longer attached to the DOM. Trying again.")

    return pd.DataFrame(rest)