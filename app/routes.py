# app/routes.py
from flask import (
    render_template, request, jsonify, current_app, url_for, flash, redirect
)
from werkzeug.utils import secure_filename
import os
from pathlib import Path

# Import the app instance created by the factory
# Access engine via the global variable set in __init__
from . import recommendation_engine
from .utils import allowed_file # Import general utils


# This assumes you have a Flask 'app' instance already created via factory pattern
# We are essentially adding routes to the app created in __init__.py

@current_app.route('/', methods=['GET'])
def index():
    """Serves the main HTML page."""
    # Check engine status for display (optional)
    engine_status = "Ready" if recommendation_engine and recommendation_engine.is_ready() else "Not Ready"
    current_app.logger.info(f"Serving index page. Engine status: {engine_status}")
    return render_template('index.html', engine_status=engine_status)


@current_app.route('/recommend', methods=['POST'])
def recommend_api():
    """API endpoint for image recommendation."""
    current_app.logger.debug("Received request for /recommend")

    # Check if engine is ready
    if not recommendation_engine or not recommendation_engine.is_ready():
         current_app.logger.error("Recommendation engine not ready.")
         return jsonify({"error": "Recommendation engine is not available"}), 503 # Service Unavailable

    # Check file part
    if 'file' not in request.files:
        current_app.logger.warning("No 'file' part in request.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        current_app.logger.warning("No file selected.")
        return jsonify({"error": "No selected file"}), 400

    # Check file type and save (optional saving)
    if file and allowed_file(file.filename):
        try:
            image_bytes = file.read()
            current_app.logger.info(f"Processing uploaded file: {secure_filename(file.filename)}")

            # Get recommendations from the engine
            recommended_filenames = recommendation_engine.get_recommendations(image_bytes)

            if recommended_filenames is None:
                # Indicates an engine failure during processing
                return jsonify({"error": "Internal server error in recommendation engine"}), 500
            elif not recommended_filenames:
                # Engine worked but found no similar items
                 return jsonify({"recommendations": [], "message": "No similar items found."}), 200 # OK response
            else:
                # Generate full static URLs for the frontend
                image_folder = current_app.config['STATIC_IMAGE_FOLDER']
                recommendation_urls = [
                    url_for('static', filename=f'{image_folder}/{filename}', _external=False)
                    for filename in recommended_filenames
                ]
                return jsonify({"recommendations": recommendation_urls})

        except Exception as e:
            current_app.logger.error(f"Error processing recommendation request: {e}", exc_info=True)
            return jsonify({"error": "Internal server error processing the request"}), 500
    else:
        current_app.logger.warning(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type"}), 400