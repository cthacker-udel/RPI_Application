# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
# RUN ON PI
# SPDX-License-Identifier: MIT

import glob
import time
from datetime import datetime

import requests
import shortuuid


# Accessing temperature device, from website
temperature_device_base_dir = '/sys/bus/w1/devices/'
temperature_device_folder = glob.glob(temperature_device_base_dir + '28*')[0]
temperature_device_file = temperature_device_folder + '/w1_slave'
pi_id = shortuuid.ShortUUID().random(length=6)


def read_temp_raw() -> list[str]:
    """
    Reads the raw temperature from the sensor

    Returns:
        list[str]: [Status of reading, reading data]
    """

    lines = []
    # opens the device file (starts up temperature reader)
    with open(temperature_device_file, 'r', encoding='utf-8') as f:
        # reads lines from the temperature reader
        lines = f.readlines()
    return lines


def read_temp():
    """
    Reads the temperature from the output

    Returns:
        tuple[int, int]: Tuple of celsius temperature, and fahrenheit temperature
    """

    # reads the temperature data
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':  # while temperature data reading is not successful
        time.sleep(0.2)  # wait until re-reading
        lines = read_temp_raw()  # read again

    # Reads the data portion of the temperature data
    equals_pos = lines[1].find('t=')

    # if the equal sign is present in the string
    if equals_pos != -1:

        # Reads the temp from the temperature string
        temp_string = lines[1][equals_pos+2:]

        # converst to celsius
        temp_c = float(temp_string) / 1000.0

        # converts to fahrenheit
        temp_f = temp_c * 9.0 / 5.0 + 32.0

        # converts to kelvin
        temp_k = temp_c + 273.15
        return temp_c, temp_f, temp_k


while True:
    [celsius, fahrenheit, kelvin] = read_temp()
    requests.post('http://192.168.1.151:8000/update_temperature', json={
                  'celsius': celsius, 'farenheit': fahrenheit, 'kelvin': kelvin, 'pi_id': id, 'timestamp': datetime.now().timestamp()}, timeout=10)
    time.sleep(1)
