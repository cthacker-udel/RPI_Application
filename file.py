from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

temperature_data = []


@app.route('/')
def index():
    formatted_data = [{'timestamp': timestamp.strftime('%m-%d %H:%M:%S'),
                       'celsius': temperature,
                       'fahrenheit': celsius_to_fahrenheit(temperature)}
                      for timestamp, temperature in temperature_data]
    return render_template('index.html', data=formatted_data)


@app.route('/update_temperature', methods=['POST'])
def update_temperature():
    data = request.json
    print(data)
    if data:
        celsius = data.get('celsius')
        timestamp_ = data.get('timestamp')
        if celsius is not None:
            timestamp = datetime.fromtimestamp(timestamp_)
            temperature_data.append(
                (timestamp, float(celsius)))
            return "Temperature updated successfully"
        else:
            return "Invalid temperature data"
    else:
        return "Temperature data not received"


@app.route('/temperature_data')
def get_temperature_data():
    return jsonify({'data': list(map(lambda x: {'timestamp': x[0].strftime('%Y-%m-%d %H:%M:%S'),
                                                'celsius': x[1],
                                                'fahrenheit': celsius_to_fahrenheit(x[1])}, temperature_data))})

# Function to convert Celsius to Fahrenheit


def celsius_to_fahrenheit(celsius):
    return celsius * 9/5 + 32


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
