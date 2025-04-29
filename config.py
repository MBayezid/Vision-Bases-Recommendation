# config.py
import os
from pathlib import Path

# Use pathlib for robust path handling relative to this config file
BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'must-change-this-secret-key'
    UPLOAD_FOLDER = BASE_DIR / 'app' / 'static' / 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16MB limit

    # ML Configuration
    MODEL_DIR = BASE_DIR / 'models'
    DATA_DIR = BASE_DIR / 'data'
    TFLITE_MODEL_PATH = MODEL_DIR / 'model_quantized_encoder.tflite'
    # ANNOY_INDEX_PATH = DATA_DIR / 'fashion-product-images-small-annoy-embeddings.ann'
    ITEM_MAPPING_PATH = DATA_DIR / 'item_mapping-fashion-product-images-small.json'
    EMBEDDINGS_PATH= DATA_DIR / 'product_embeddings.npy'
    FILENAMES_PATH = DATA_DIR / 'image_filenames.json'

    EMBEDDING_DIM = 2048 # Example dimension, adjust based on your model!
    # ANNOY_METRIC = 'angular' # Or 'euclidean', etc.
    # NUM_RECOMMENDATIONS = 18
    # # These need to match your model/data
    STATIC_IMAGE_FOLDER = 'images' # Subfolder within 'static' for product images


    # --- Model & Search Parameters ---
    # EMBEDDING_DIM = 128 # IMPORTANT: Set this to the actual output dimension of your TFLite model
    NUM_RECOMMENDATIONS = 10 # Number of similar images to return
    NEIGHBORS_METRIC = 'euclidean' # Metric for NearestNeighbors ('cosine', 'euclidean', 'minkowski', etc.)
                                # 'cosine' is often good for embeddings. Ensure it matches how embeddings were trained/intended.

    # Ensure necessary directories exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / 'app' / 'static' / STATIC_IMAGE_FOLDER).mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Add any production-specific settings, e.g., logging configuration

# Dictionary to access config classes easily
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}