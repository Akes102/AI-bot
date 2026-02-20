# WeatherApp_Wttr
# Simple console weather app using wttr.in
# No API key required

import requests   # Used to make HTTP requests to wttr.in
import sys        # Used to read command-line arguments


def get_weather(city):
    # Build the wttr.in URL
    # format=j1 returns JSON instead of plain text
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # Send GET request with a timeout to avoid hanging forever
        r = requests.get(url, timeout=10)

        # Raise an error if HTTP status is not 200 (OK)
        r.raise_for_status()
    except Exception as e:
        # Catch network errors, timeouts, bad responses, etc.
        print(f"Network error: {e}")
        return

    # Convert JSON response into a Python dictionary
    data = r.json()

    # Extract current weather conditions safely
    # If keys are missing, fall back to empty dicts
    current = data.get("current_condition", [{}])[0]

    # If no current weather data exists
    if not current:
        print("No weather data found.")
        return

    # Display current weather info
    print(f"Location: {city}")
    print(f"Condition: {current.get('weatherDesc',[{}])[0].get('value','N/A')}")
    print(f"Temperature: {current.get('temp_C','N/A')}°C")
    print(f"Feels like: {current.get('FeelsLikeC','N/A')}°C")
    print(f"Humidity: {current.get('humidity','N/A')}%")
    print(
        f"Wind: {current.get('winddir16Point','N/A')} "
        f"at {current.get('windspeedKmph','N/A')} km/h"
    )
    print()

    # Get forecast data (usually contains multiple days)
    weather = data.get('weather', [])

    # Show up to 3 days of forecast if available
    if weather:
        print('3-day summary:')
        for day in weather[:3]:
            date = day.get('date', 'N/A')
            maxtemp = day.get('maxtempC', 'N/A')
            mintemp = day.get('mintempC', 'N/A')

            # Take description from the first hourly entry
            desc = (
                day.get('hourly', [{}])[0]
                .get('weatherDesc', [{}])[0]
                .get('value', 'N/A')
            )

            print(f"  {date}: {desc}, {mintemp}°C - {maxtemp}°C")


def main():
    # Check if city name was passed via command line
    if len(sys.argv) > 1:
        # Join all arguments after script name into one city string
        city = " ".join(sys.argv[1:])
    else:
        # Ask user for input if no arguments were provided
        city = input("Enter city (e.g. Cape Town): ").strip() or "Cape Town"

    # Replace spaces with + for URL compatibility
    get_weather(city.replace(' ', '+'))


# Entry point check
# Ensures main() runs only when script is executed directly
if __name__ == '__main__':
    main()
