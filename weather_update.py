# WeatherApp_Wttr v2
# Console weather app using wttr.in with colored output

import requests
import sys
from colorama import Fore, Style, init

# Initialize colorama so colors work on Windows
init(autoreset=True)


def get_weather(city):
    # Build API URL (JSON format)
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # Send request with timeout
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"Network error: {e}")
        return

    # Parse JSON response
    data = r.json()

    # Extract current conditions safely
    current = data.get("current_condition", [{}])[0]

    if not current:
        print(Fore.RED + "No weather data found.")
        return

    # Header
    print(Fore.CYAN + Style.BRIGHT + f"\nWeather for {city.replace('+', ' ')}")
    print(Fore.CYAN + "-" * 30)

    # Current weather
    print(
        Fore.YELLOW + "Condition: " +
        Fore.WHITE + current.get('weatherDesc', [{}])[0].get('value', 'N/A')
    )
    print(
        Fore.YELLOW + "Temperature: " +
        Fore.WHITE + f"{current.get('temp_C', 'N/A')}°C"
    )
    print(
        Fore.YELLOW + "Feels like: " +
        Fore.WHITE + f"{current.get('FeelsLikeC', 'N/A')}°C"
    )
    print(
        Fore.YELLOW + "Humidity: " +
        Fore.WHITE + f"{current.get('humidity', 'N/A')}%"
    )
    print(
        Fore.YELLOW + "Wind: " +
        Fore.WHITE +
        f"{current.get('winddir16Point','N/A')} "
        f"at {current.get('windspeedKmph','N/A')} km/h"
    )

    # Forecast section
    weather = data.get("weather", [])

    if weather:
        print(Fore.CYAN + "\n3-Day Forecast")
        print(Fore.CYAN + "-" * 30)

        for day in weather[:3]:
            date = day.get("date", "N/A")
            max_temp = day.get("maxtempC", "N/A")
            min_temp = day.get("mintempC", "N/A")
            desc = (
                day.get("hourly", [{}])[0]
                .get("weatherDesc", [{}])[0]
                .get("value", "N/A")
            )

            print(
                Fore.GREEN + f"{date}: " +
                Fore.WHITE + f"{desc}, {min_temp}°C - {max_temp}°C"
            )


def main():
    # Read city from command line if provided
    if len(sys.argv) > 1:
        city = " ".join(sys.argv[1:])
    else:
        city = input("Enter city (e.g. Cape Town): ").strip() or "Cape Town"

    # Replace spaces for URL safety
    get_weather(city.replace(" ", "+"))


# Script entry point
if __name__ == "__main__":
    main()
