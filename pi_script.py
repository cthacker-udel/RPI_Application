# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
# RUN ON PI
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Session, relationship
from sqlalchemy import create_engine, make_url, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import shortuuid
import argparse
import glob
import time
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DB_USERNAME_ENV = "LOCAL_DB_USERNAME"  # "PAVER_WRITE_USERNAME"
DB_PASSWORD_ENV = "LOCAL_DB_PASSWORD"  # "PAVER_WRITE_PASSWORDS"
DB_HOST_ENV = "LOCAL_DB_HOST"  # "PAVER_DB_HOST"
DB_TABLE_ENV = "LOCAL_DB_TABLE"  # "PAVER_DB_TABLE"

WRITE_USER = os.getenv(DB_USERNAME_ENV)
WRITE_PASS = os.getenv(DB_PASSWORD_ENV)
DB_HOST = os.getenv(DB_HOST_ENV)
DB_TABLE = os.getenv(DB_TABLE_ENV)

parser = argparse.ArgumentParser(
    description='Run the temperature script, sending data to be displayed on the research website.')
parser.add_argument('name', metavar='N', type=str, help='The name of the PI')

url = make_url(
    f"mariadb+mariadbconnector://{WRITE_USER}:{WRITE_PASS}@{DB_HOST}:3306/{DB_TABLE}")
engine = create_engine(
    os.getenv('MY_SQL_CONNECTION_STRING'), echo=True)

Base = declarative_base()


class Id(Base):
    __tablename__ = 'ids'
    id = Column(Integer, primary_key=True)
    pi_id = Column(String(6), unique=True)
    name = Column(String(10))
    temperatures = relationship('Temperature', back_populates='pi')


class Temperature(Base):
    __tablename__ = "temperatures"
    id = Column(Integer, primary_key=True)
    celsius = Column(Float(5), nullable=False)
    fahrenheit = Column(Float(5), nullable=False)
    kelvin = Column(Float(5), nullable=False)
    timestamp = Column(Integer(), nullable=False)
    pi_id = Column(String(6), ForeignKey("ids.pi_id"))
    pi = relationship("Id", back_populates="temperatures")


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


def add_temp(temperature_data):
    [celsius, fahrenheit, kelvin] = temperature_data
    with Session() as session:
        temp_record = Temperature(
            celsius=celsius, fahrenheit=fahrenheit, kelvin=kelvin, timestamp=datetime.now())
        session.add(temp_record)


while True:
    args = parser.parse_args()
    args.accumulate(args.name)
    # send_temp(read_temp())
