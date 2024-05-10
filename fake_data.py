import sys
from sqlalchemy import create_engine, Column, Float, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import random
import time
import os
from dotenv import load_dotenv
import shortuuid

load_dotenv()

DB_USERNAME_ENV = "LOCAL_DB_USERNAME"  # "PAVER_WRITE_USERNAME"
DB_PASSWORD_ENV = "LOCAL_DB_PASSWORD"  # "PAVER_WRITE_PASSWORDS"
DB_HOST_ENV = "LOCAL_DB_HOST"  # "PAVER_DB_HOST"
DB_TABLE_ENV = "LOCAL_DB_TABLE"  # "PAVER_DB_TABLE"

WRITE_USER = os.getenv(DB_USERNAME_ENV)
WRITE_PASS = os.getenv(DB_PASSWORD_ENV)
DB_HOST = os.getenv(DB_HOST_ENV)
DB_TABLE = os.getenv(DB_TABLE_ENV)

# Create SQLAlchemy engine and session
url = f"mariadb+mariadbconnector://{WRITE_USER}:{
    WRITE_PASS}@{DB_HOST}:3306/{DB_TABLE}"
engine = create_engine(url)
Base = declarative_base()
Session = sessionmaker(bind=engine)
pi_id = shortuuid.ShortUUID().random(length=6)

# Define Pi and Temperature models


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
    temperature_timestamp = Column(Integer(), nullable=False)
    pi_id = Column(String(6), ForeignKey("ids.pi_id"))
    pi = relationship("Id", back_populates="temperatures")


# Create tables in the database
Base.metadata.create_all(engine)

# Function to generate temperature data


def generate_temperature():
    celsius = round(random.uniform(0, 40), 2)
    fahrenheit = round((celsius * 9/5) + 32, 2)
    temp_k = celsius + 273.15
    return celsius, fahrenheit, temp_k

# Function to send temperature data using SQLAlchemy


def send_temperature_data(pi_name):
    pi = get_or_create_pi(pi_name)
    while True:
        # Generate random temperature data
        celsius, fahrenheit, kelvin = generate_temperature()
        timestamp = datetime.now()

        # Create new Temperature object
        temperature = Temperature(
            celsius=celsius, fahrenheit=fahrenheit, kelvin=kelvin, temperature_timestamp=timestamp, pi=pi)

        # Add temperature data to the database
        with Session() as session:
            session.add(temperature)
            session.commit()
            print(f"Temperature data sent successfully: celsius={celsius}, fahrenheit={
                  fahrenheit}, timestamp={timestamp}, pi_id={pi.pi_id}")

        # Wait for a random duration between 30 to 90 seconds before sending the next temperature reading
        delay_seconds = round(random.uniform(30, 90), 2)
        print(f"Waiting for {
              delay_seconds} seconds before sending the next temperature reading...")
        time.sleep(delay_seconds)


def get_or_create_pi(pi_name):
    with Session() as session:
        pi = session.query(Id).filter_by(name=pi_name).first()
        print('pi = ', pi)
        if not pi:
            # Replace with your actual Pi ID
            pi = Id(pi_id=pi_id, name=pi_name)
            session.add(pi)
            session.commit()
        return pi


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py [Pi Name]")
        sys.exit(1)
    pi_name = sys.argv[1]
    send_temperature_data(pi_name)
