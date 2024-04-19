# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
# RUN ON PI
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            relationship)
from sqlalchemy import Float, ForeignKey, Integer, String, create_engine
import shortuuid
import argparse
import glob
import time
from datetime import datetime
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()


parser = argparse.ArgumentParser(
    description='Run the temperature script, sending data to be displayed on the research website.')
parser.add_argument('name', metavar='N', type=str, help='The name of the PI')

engine = create_engine(
    os.getenv('MY_SQL_CONNECTION_STRING'), echo=True)


class Base(DeclarativeBase):
    pass


class Temperature(Base):
    __tablename__ = 'temperature'

    # PK
    id: Mapped[int] = mapped_column(primary_key=True)

    # celsius of the temperature
    celsius: Mapped[float] = mapped_column(Float(5))

    # fahrenheit of the temperature
    fahrenheit: Mapped[float] = mapped_column(Float(5))

    # kelvin of the temperature
    kelvin: Mapped[float] = mapped_column(Float(5))

    # the timestamp of when the temperature was added
    timestamp: Mapped[Integer] = mapped_column(Integer())

    # id of the pi adding the temperature
    pi_id: Mapped[String] = mapped_column(ForeignKey('ids.pi_id'))


class Ids(Base):
    __tablename__ = 'ids'

    # PK
    id: Mapped[int] = mapped_column(primary_key=True)

    # the id of the pi
    pi_id: Mapped[String] = mapped_column(String(10), unique=True)

    # the name of the pi
    name: Mapped[String] = mapped_column(String(10))

    # all of the temperatures belonging to the pi with the id
    temperatures: Mapped[List["Temperature"]] = relationship()


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


def send_temp(temperature_data):
    [celsius, fahrenheit, kelvin] = temperature_data
    with Session(engine) as session:
        temp_record = Temperature(
            celsius=celsius, fahrenheit=fahrenheit, kelvin=kelvin, timestamp=datetime.now())


while True:
    args = parser.parse_args()
    args.accumulate(args.name)
    # send_temp(read_temp())
