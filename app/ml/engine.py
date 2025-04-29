# app/ml/engine.py

import logging
from pathlib import Path
import json
import numpy as np # Import numpy
from sklearn.neighbors import NearestNeighbors # Import NearestNeighbors

# Choose the TFLite runtime (no changes here)
try:
    import tflite_runtime.interpreter as tflite  # type: ignore
    Interpreter = tflite.Interpreter
    tf_ok = True
except ImportError:
    try:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter
        tf_ok = True
    except ImportError:
        tf_ok = False
        logging.error("TensorFlow or TFLite Runtime not installed!")

from .utils import preprocess_image # Import from sibling utils module

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self, config):
        self.config = config
        self.interpreter = None
        # --- Removed Annoy ---
        # self.annoy_index = None
        # self.item_mapping = None
        # --- Added scikit-learn components ---
        self.nn_model = None
        self.all_embeddings = None
        self.image_filenames = None
        # --- End Added components ---
        self.input_details = None
        self.output_details = None
        self.input_shape = None
        self.input_height = None
        self.input_width = None

        self.embedding_dim = self.config['EMBEDDING_DIM']
        self.model_path = self.config["TFLITE_MODEL_PATH"]
        # --- Added scikit-learn specific config ---
        self.neighbors_metric = self.config.get('NEIGHBORS_METRIC', 'cosine') # Default to cosine
        self.num_recommendations = self.config['NUM_RECOMMENDATIONS']
        # --- End Added config ---

        self._load_components()

    def _load_components(self):
        """Loads TFLite model, embeddings, filename mapping, and fits NearestNeighbors."""
        logger.info("Loading ML components...")
        components_loaded = True
        if not tf_ok:
            logger.error("Cannot load TFLite model - TensorFlow/TFLite Runtime missing.")
            components_loaded = False
            return # Exit if TF isn't available

        # Load TFLite Model (No changes here, logic remains the same)
        try:
            model_path = self.model_path
            if not model_path.exists():
                raise FileNotFoundError(f"TFLite model not found at {model_path}")
            self.interpreter = Interpreter(model_path=str(model_path))
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_shape = self.input_details[0]['shape']
            self.input_height = self.input_shape[1]
            self.input_width = self.input_shape[2]

            model_output_dim = self.output_details[0]['shape'][-1]
            if model_output_dim != self.embedding_dim:
                logger.warning(f"Config EMBEDDING_DIM ({self.embedding_dim}) != Model output dim ({model_output_dim}). Using model dim.")
                self.embedding_dim = model_output_dim

            logger.info(f"✅ TFLite model loaded. Input: {self.input_shape}, Output: {self.output_details[0]['shape']}")
        except Exception as e:
            logger.error(f"❌ Error loading TFLite model: {e}", exc_info=True)
            self.interpreter = None
            components_loaded = False

        # --- Load Embeddings, Filenames and Fit NearestNeighbors ---
        if components_loaded:
            try:
                embeddings_path = self.config['EMBEDDINGS_PATH'] # Path to product_embeddings.npy
                filenames_path = self.config['FILENAMES_PATH'] # Path to image_filenames.json

                if not embeddings_path.exists(): raise FileNotFoundError(f"Embeddings file missing: {embeddings_path}")
                if not filenames_path.exists(): raise FileNotFoundError(f"Filenames mapping missing: {filenames_path}")

                # Load embeddings
                self.all_embeddings = np.load(embeddings_path)
                logger.info(f"✅ Embeddings loaded from {embeddings_path} with shape {self.all_embeddings.shape}.")

                # Verify embedding dimension match
                if self.all_embeddings.shape[1] != self.embedding_dim:
                    raise ValueError(f"Embedding dimension mismatch! Model expects {self.embedding_dim}, but loaded embeddings have {self.all_embeddings.shape[1]} dimensions.")

                # Load filenames
                with open(filenames_path, 'r') as f:
                    self.image_filenames = json.load(f)
                logger.info(f"✅ Image filenames loaded ({len(self.image_filenames)} items).")

                # Verify consistency between embeddings and filenames
                if len(self.image_filenames) != self.all_embeddings.shape[0]:
                    raise ValueError(f"Mismatch between number of embeddings ({self.all_embeddings.shape[0]}) and number of filenames ({len(self.image_filenames)}).")

                # --- Initialize and Fit NearestNeighbors ---
                logger.info(f"Fitting NearestNeighbors (metric='{self.neighbors_metric}', algorithm='brute')...")
                # We use 'brute' because it's guaranteed to work without complex compilation
                # issues often found with 'kd_tree' or 'ball_tree' on restricted environments.
                # It might be slower for huge datasets, but fine for a demo.
                self.nn_model = NearestNeighbors(
                    n_neighbors=self.num_recommendations + 1, # Get one extra in case the query is in the dataset
                    metric=self.neighbors_metric,
                    algorithm='brute' # Use brute-force search - simpler, CPU-bound
                )
                self.nn_model.fit(self.all_embeddings)
                logger.info("✅ NearestNeighbors model fitted.")
                # --- End NearestNeighbors Fit ---

            except Exception as e:
                logger.error(f"❌ Error loading embeddings/filenames or fitting NearestNeighbors: {e}", exc_info=True)
                self.nn_model = None
                self.all_embeddings = None
                self.image_filenames = None
                components_loaded = False
        # --- End Loading & Fitting ---

        if not components_loaded:
            logger.warning("⚠️ One or more ML components failed to load.")


    def is_ready(self):
        """Check if all necessary components are loaded."""
        # Updated check for scikit-learn components
        return all([
            self.interpreter,
            self.nn_model,          # Check for the NearestNeighbors model
            self.all_embeddings is not None, # Check if embeddings are loaded
            self.image_filenames is not None, # Check if filenames are loaded
            self.input_details,
            self.output_details
        ])

    def get_embedding(self, input_data):
        """Runs inference using the loaded TFLite model."""
        # No changes needed in this method
        if not self.is_ready():
            logger.error("Engine not ready for inference (TFLite model missing?).")
            return None
        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            return output_data # Shape: (1, embedding_dim)
        except Exception as e:
            logger.error(f"Error during TFLite inference: {e}", exc_info=True)
            return None

    def find_similar(self, query_embedding, num_results):
        """Finds similar images using the scikit-learn NearestNeighbors model."""
        if not self.is_ready() or query_embedding is None:
            logger.error("Engine not ready or query embedding missing for search.")
            return []
        if self.nn_model is None or self.image_filenames is None:
             logger.error("NearestNeighbors model or filenames not loaded.")
             return []

        try:
            # query_embedding shape is (1, embedding_dim), which is expected by kneighbors
            distances, indices = self.nn_model.kneighbors(query_embedding, n_neighbors=num_results + 1) # Request one extra

            results = []
            # indices[0] contains the list of indices of the nearest neighbors
            for i, idx in enumerate(indices[0]):
                # Optional: Skip the first result if it's extremely close (likely the query image itself if it was in the dataset)
                # A simple threshold on distance can work, especially if metric is 'euclidean'
                if i == 0 and distances[0][i] < 1e-6: # Adjust threshold as needed
                   logger.debug(f"Skipping self-match: index {idx}")
                   continue

                # Get the filename corresponding to the index
                if 0 <= idx < len(self.image_filenames):
                    filename = self.image_filenames[idx]
                    results.append(filename)
                else:
                    logger.warning(f"Neighbor index {idx} out of bounds for filenames list.")

                if len(results) >= num_results:
                    break # Stop once we have enough results

            return results

        except Exception as e:
            logger.error(f"Error during NearestNeighbors search: {e}", exc_info=True)
            return []

    def get_recommendations(self, image_bytes):
        """Processes image bytes and returns list of recommended filenames."""
        # No changes needed in the overall logic, just uses the updated methods
        if not self.is_ready():
            logger.error("Recommendation engine not ready.")
            return None # Indicate engine failure

        # 1. Preprocess
        input_data = preprocess_image(
            image_bytes,
            self.input_height,
            self.input_width,
            expected_shape=self.input_shape
        )
        if input_data is None:
            logger.error("Preprocessing failed.")
            return [] # Indicate processing failure but engine is ok

        # 2. Get Embedding
        query_embedding = self.get_embedding(input_data)
        if query_embedding is None:
            logger.error("Embedding generation failed.")
            return [] # Indicate processing failure

        # 3. Find Similar (uses the new find_similar method)
        recommended_filenames = self.find_similar(
            query_embedding,
            self.num_recommendations # Use the value from config
        )
        return recommended_filenames # Returns list of filenames or []