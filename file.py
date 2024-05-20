import os

import nh3
from flask import Flask, jsonify, render_template, request
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, make_url
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
# CORS(app, resources={r'/api/*': {'origins': 'rgca.engr.udel.edu'}})

DB_USERNAME_ENV = "LOCAL_DB_USERNAME"  # "PAVER_READ_USERNAME"
DB_PASSWORD_ENV = "LOCAL_DB_PASSWORD"  # "PAVER_READ_PASSWORD"
DB_HOST_ENV = "LOCAL_DB_HOST"  # "PAVER_DB_HOST"
DB_TABLE_ENV = "LOCAL_DB_TABLE"  # "PAVER_DB_TABLE"

READ_USER = os.getenv(DB_USERNAME_ENV)
READ_PASS = os.getenv(DB_PASSWORD_ENV)
DB_HOST = os.getenv(DB_HOST_ENV)
DB_TABLE = os.getenv(DB_TABLE_ENV)

url = make_url(
    f"mariadb+mariadbconnector://{READ_USER}:{READ_PASS}@{DB_HOST}:3306/{DB_TABLE}")
engine = create_engine(url)
Base = declarative_base()

Session = sessionmaker(bind=engine)


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


Base.metadata.create_all(engine)


@app.route('/')
def index() -> str:
    return render_template('index.html')


@app.route("/details")
def background() -> str:
    return render_template("details.html")


@app.route('/api/pi-ids', methods=['GET'])
def get_pi_ids_route() -> str:
    session = Session()
    pi_ids = [id.pi_id for id in session.query(Id).all()]
    session.close()
    return jsonify(pi_ids)


@app.route('/api/temperature_data', methods=['GET'])
def get_temperature_data():
    pi_id = nh3.clean(request.args.get('pi_id'))

    if not pi_id:
        return jsonify({'error': 'Pi ID is required'})

    session = Session()
    temperatures = session.query(Temperature).filter(
        Temperature.pi_id == pi_id).all()
    session.close()

    formatted_data = [{
        'timestamp': temp.temperature_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'celsius': temp.celsius,
        'kelvin': temp.kelvin,
        'pi_id': temp.pi_id,
        'fahrenheit': celsius_to_fahrenheit(temp.celsius)
    } for temp in temperatures]

    return jsonify({'data': formatted_data})


def celsius_to_fahrenheit(celsius):
    return celsius * 9/5 + 32


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
