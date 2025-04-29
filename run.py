# run.py
import os
from app import create_app

# Get config name from environment variable or use default
config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name)

if __name__ == '__main__':
    # Use Flask's built-in server for development
    # Host 0.0.0.0 makes it accessible on network
    # Debug=True enables auto-reload and debugger (set by DevelopmentConfig)
    app.run(host='0.0.0.0', port=5000)  # Change port as needed
    # Note: In production, use a WSGI server like Gunicorn or uWSGI
    