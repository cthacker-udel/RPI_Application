from dataclasses import dataclass


@dataclass
class TemperaturePayload:
    """
    Represents the payload being sent to the server
    """
    celsius: float  # the celsius reading
    fahrenheit: float  # the fahrenheit reading
    kelvin: float  # the kelvin reading
    pi_id: str  # the id of the raspberry pi sending the info
    timestamp: float  # the timestamp of when the data was collected
