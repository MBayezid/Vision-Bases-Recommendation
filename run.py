# run.py
import os
from app import create_app

# Get config name from environment variable or use default
config_name = os.getenv('FLASK_CONFIG') or 'production'
app = create_app(config_name)

if __name__ == '__main__':
    # Use Flask's built-in server for development
    # Host 0.0.0.0 makes it accessible on network
    # Debug=True enables auto-reload and debugger (set by DevelopmentConfig)
    app.run(host='184.94.213.165', port=5000)  # Change port as needed
    # Note: In production, use a WSGI server like Gunicorn or uWSGI
    

# import os
# import sys


# sys.path.insert(0, os.path.dirname(__file__))


# def passenger_wsgi(environ, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     message = 'It works!\n'
#     version = 'Python v' + sys.version.split()[0] + '\n'
#     response = '\n'.join([message, version])
#     return [response.encode()]