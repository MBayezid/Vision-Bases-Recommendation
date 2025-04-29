# app/__init__.py
import os
from flask import Flask
from flask_cors import CORS
import logging

# Import config dictionary from top-level config.py
from config import config
# Import the recommendation engine
from .ml.engine import RecommendationEngine

# Initialize Recommendation Engine Singleton (or load on demand)
# Loading globally here might still be problematic on shared hosting memory limits at startup
recommendation_engine = None

def create_app(config_name=None):
    """Application Factory Function"""
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__, instance_relative_config=False) # Static/templates relative to 'app' package
    app.config.from_object(config[config_name])

    # --- Logging ---
    logging.basicConfig(level=logging.INFO if not app.debug else logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app.logger.info(f"Starting app with '{config_name}' config.")

    # --- Initialize Extensions ---
    CORS(app) # Enable CORS

    # --- Initialize Recommendation Engine ---
    # Load it here, making it available via app context or globally
    global recommendation_engine
    try:
         # Pass the loaded app config to the engine
         recommendation_engine = RecommendationEngine(app.config)
         if not recommendation_engine.is_ready():
              app.logger.error("ML Engine failed to initialize properly!")
         else:
              app.logger.info("ML Engine initialized.")
    except Exception as e:
         app.logger.error(f"CRITICAL: Failed to initialize RecommendationEngine: {e}", exc_info=True)
         recommendation_engine = None # Ensure it's None if init fails

    # --- Register Blueprints ---
    # Using routes directly in this simple case, but Blueprints are better for larger apps
    with app.app_context():
         from . import routes # Import routes after app is created

    app.logger.info("Flask app created successfully.")
    return app