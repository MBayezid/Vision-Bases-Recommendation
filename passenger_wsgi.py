# passenger_wsgi.py
import os
import sys

# Add the project directory to sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Import the app factory and create the app instance
# The variable MUST be named 'application' for Passenger
from app import create_app

# Use 'production' config when deployed, or let create_app use default/env var
config_name = os.getenv('FLASK_CONFIG', 'production')
application = create_app(config_name)

# Optional: Add logging configuration specifically for production if needed here
# import logging
# handler = logging.FileHandler(os.path.join(APP_DIR, 'passenger.log'))
# handler.setLevel(logging.INFO)
# application.logger.addHandler(handler)
# application.logger.info("Passenger WSGI started.")