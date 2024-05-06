import json
import os
from datetime import datetime
from typing import Any, Dict, List

import nh3
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from jsonschema import ValidationError, validate
from temp_json_payload import TemperaturePayload

load_dotenv()

app = Flask(__name__)

schema = {
    'type': 'object',
    'properties': {
        'celsius': {'type': 'number'},
        'fahrenheit': {'type': 'number'},
        'kelvin': {'type': 'number'},
        'pi_id': {'type': 'string'},
        'timestamp': {'type': 'number'}
    },
    'required': ['celsius', 'fahrenheit', 'kelvin', 'pi_id', 'timestamp']
}

READ_USER = os.getenv("PAVER_READ_ACCOUNT_NAME")
READ_PASS = os.getenv("PAVER_READ_ACCOUNT_PASSWORD")
DB_HOST = os.getenv("PAVER_DB_HOST")

engine = sqlalchemy.create_engine(
    f"mariadb+mariadbconnector://{READ_USER}:{READ_PASS}@{DB_HOST}/company")
Base = declarative_base()


class Temperature(Base):
    __tablename__ = "temperature"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    celsius = sqlalchemy.Column(sqlalchemy.Float(5), nullable=False)
    fahrenheit = sqlalchemy.Column(sqlalchemy.Float(5), nullable=False)
    kelvin = sqlalchemy.Column(sqlalchemy.Float(5), nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    pi_id = sqlalchemy.Column(sqlalchemy.ForeignKey("ids.pi_id"))


Base.metadata.create_all(engine)


@app.route('/')
def index() -> str:
    """
    The base file, displays the temperature data

    Returns:
        HTML: The index.html with the template data injected
    """
    return render_template('index.html')


@app.route('/pi-ids', methods=['GET'])
def get_pi_ids_route() -> str:
    response = [x.decode('utf-8') for x in list(get_pi_ids_from_set())]
    return jsonify(response)


@app.route('/update_temperature', methods=['POST'])
def update_temperature() -> str:
    """
    Update temperature data received from a POST request.

    Returns:
        str: Response indicating the success or failure of the update operation.
    """
    data: Dict[str, Any] = request.json

    if data:
        fahrenheit: float = data.get('fahrenheit')
        celsius: float = data.get('celsius')
        kelvin: float = data.get('kelvin')
        pi_id: str = nh3.clean(data.get('pi_id'))
        timestamp: datetime = data.get('timestamp')

        try:
            validate(instance=data, schema=schema)
        except ValidationError as error:
            return jsonify({'error': error.message}), 400

        if celsius is not None:
            timestamp_datetime: datetime = datetime.fromtimestamp(timestamp)
            temperature_payload: Dict[str, Any] = {
                'celsius': celsius,
                'fahrenheit': fahrenheit,
                'kelvin': kelvin,
                'pi_id': pi_id,
                'timestamp': timestamp_datetime.strftime('%Y-%m-%d %H:%M:%S')
            }
            store_temperature_data_to_redis(temperature_payload)
            if not is_pi_id_in_set(pi_id):
                add_pi_id_to_set(pi_id)
            return "Temperature updated successfully"

        return "Invalid temperature data"
    return "Temperature data not received"


@app.route('/temperature_data')
def get_temperature_data():
    """
    Retrieve temperature data from Redis.

    Returns:
        str: JSON response containing the temperature data.
    """
    pi_id = nh3.clean(request.args.get('pi_id'))

    if not pi_id:
        return jsonify({'error': 'Pi ID is required'})

    temperature_data: List[Dict[str, Any]
                           ] = get_temperature_data_from_redis(pi_id)
    formatted_data: List[Dict[str, Any]] = [{
        'timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
        'celsius': data['celsius'],
        'kelvin': data['kelvin'],
        'pi_id': data['pi_id'],
        'fahrenheit': celsius_to_fahrenheit(data['celsius'])}
        for data in temperature_data]

    return jsonify({'data': formatted_data})


def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit.

    Args:
        celsius (float): Temperature in Celsius.

    Returns:
        float: Temperature in Fahrenheit.
    """
    return celsius * 9/5 + 32


def store_temperature_data_to_redis(data: TemperaturePayload):
    """
    Store temperature data to Redis.

    Args:
        data (Dict[str, Any]): Temperature data to store.
    """
    classed_data = TemperaturePayload(**data)
    collection_str = f'temperature_data_{classed_data.pi_id}'
    if not redis_conn.exists(collection_str):
        redis_conn.expire(collection_str, 3600)
    redis_conn.lpush(collection_str, json.dumps(data))


def get_temperature_data_from_redis(pi_id):
    """
    Retrieve temperature data from Redis.

    Returns:
        List[Dict[str, Any]]: List of temperature data.
    """
    temperature_data: List[Dict[str, Any]] = []
    temperature_data_strings: List[str] = redis_conn.lrange(
        f'temperature_data_{pi_id}', 0, -1)
    for data_str in temperature_data_strings:
        data: Dict[str, Any] = json.loads(data_str)
        data['timestamp'] = datetime.strptime(
            data['timestamp'], '%Y-%m-%d %H:%M:%S')
        temperature_data.append(data)
    return temperature_data


def add_pi_id_to_set(pi_id):
    # Add the Pi ID to the Redis Set
    redis_conn.sadd('pi_ids', pi_id)


def get_pi_ids_from_set():
    # Retrieve all Pi IDs from the Redis Set
    return redis_conn.smembers('pi_ids')


def remove_pi_id_from_set(pi_id):
    # Remove the Pi ID from the Redis Set
    redis_conn.srem('pi_ids', pi_id)


def is_pi_id_in_set(pi_id):
    """
    Check if a Pi ID is already in the set.

    Args:
        pi_id (str): The Pi ID to check.

    Returns:
        bool: True if the Pi ID is in the set, False otherwise.
    """
    return redis_conn.sismember('pi_ids', pi_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
