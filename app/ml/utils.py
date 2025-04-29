# app/ml/utils.py
import io
import numpy as np
from PIL import Image
import logging # Add logging

logger = logging.getLogger(__name__)

# Constants should ideally come from config, but for simplicity here:
IMG_SIZE = 64 # Or get from config if passed
COLOR_MODE = 'grayscale'
NORMALIZE = True

def preprocess_image(image_bytes, target_height=IMG_SIZE, target_width=IMG_SIZE, expected_shape=None):
    """Loads, resizes (grayscale), and preprocesses image bytes for TFLite model."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('L') # Convert to Grayscale ('L')
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        img_array = np.array(img, dtype=np.float32)
        if NORMALIZE:
            img_array = img_array / 255.0

        # Add batch and channel dimensions
        input_data = np.expand_dims(img_array, axis=[0, -1]) # Shape: (1, height, width, 1)

        # Verify final shape matches model input details if provided
        if expected_shape is not None: # Check if expected_shape was successfully retrieved
            actual_shape = input_data.shape
            expected_shape_tuple = tuple(expected_shape) # Ensure comparison is tuple vs tuple
            if actual_shape != expected_shape_tuple:
                logger.warning(f"Preprocessed image shape {actual_shape} differs from model expected shape {expected_shape_tuple}")
                # Handle mismatch if necessary (e.g., raise error, return None, attempt reshape)         

        return input_data
    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}", exc_info=True)
        return None