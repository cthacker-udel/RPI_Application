import requests
import random
import time
from datetime import datetime

# Flask server URL
SERVER_URL = 'http://localhost:8000/update_temperature'


def generate_temperature():
    # Generate random temperature in Celsius
    celsius = round(random.uniform(0, 40), 2)
    # Convert Celsius to Fahrenheit
    fahrenheit = round((celsius * 9/5) + 32, 2)
    return celsius, fahrenheit


def send_temperature_data():
    while True:
        # Generate random temperature data
        celsius, fahrenheit = generate_temperature()
        timestamp = datetime.now().timestamp()
        payload = {'celsius': celsius,
                   'fahrenheit': fahrenheit, 'timestamp': timestamp}

        try:
            # Send POST request to Flask server
            response = requests.post(SERVER_URL, json=payload)
            if response.status_code == 200:
                print(f"Temperature data sent successfully: {payload}")
            else:
                print(f"Failed to send temperature data: {
                      response.status_code}")
        except Exception as e:
            print(f"Error sending temperature data: {e}")

        # Wait for a random duration between 30 to 90 seconds before sending the next temperature reading
        delay_seconds = round(random.uniform(0.3, 1), 2)
        print(f"Waiting for {
              delay_seconds} seconds before sending the next temperature reading...")
        time.sleep(delay_seconds)


if __name__ == "__main__":
    send_temperature_data()
