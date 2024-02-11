import swiggy_scraper as ss
import pandas as pd

# List of city names
city_names = [
"Ravulapalem",
"Sankarankoil"
]
# Iterate over the list of cities

for city_name in city_names:
    try:
        print(f"Fetching data for {city_name}")
        df = ss.get_restaurants(city_name, False)

        # Save results to a CSV file for the current city
        df.to_csv(f'swiggy_restaurant_data_{city_name.lower()}.csv', index=False)

        print(f"Data collected successfully for {city_name}")
    except Exception as e:
        print(f"Error collecting data for {city_name}: {str(e)}")
