# app/ml/engine.py
import logging
from pathlib import Path
import json
from annoy import AnnoyIndex
# Choose the TFLite runtime
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
        self.annoy_index = None
        self.item_mapping = None
        self.input_details = None
        self.output_details = None
        self.input_shape = None
        self.input_height = None
        self.input_width = None

        # self.embedding_dim = config.EMBEDDING_DIM # Get dim from config
        self.embedding_dim = self.config['EMBEDDING_DIM'] # NEW WAY (Correct for Flask app.config)
        self.model_path = self.config["TFLITE_MODEL_PATH"]

        self._load_components()

    def _load_components(self):
        """Loads TFLite model, Annoy index, and item mapping."""
        logger.info("Loading ML components...")
        components_loaded = True
        if not tf_ok:
            logger.error("Cannot load TFLite model - TensorFlow/TFLite Runtime missing.")
            components_loaded = False
            return # Exit if TF isn't available

        # Load TFLite Model
        try:
            # model_path = self.config.TFLITE_MODEL_PATH
            model_path = self.model_path 
            # model_path = config['TFLITE_MODEL_PATH'] # NEW WAY (Correct for Flask app.config)
            
            if not model_path.exists():
                raise FileNotFoundError(f"TFLite model not found at {model_path}")
            self.interpreter = Interpreter(model_path=str(model_path))
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_shape = self.input_details[0]['shape']
            self.input_height = self.input_shape[1]
            self.input_width = self.input_shape[2]
            # Verify embedding dim matches model output
            model_output_dim = self.output_details[0]['shape'][-1]
            if model_output_dim != self.embedding_dim:
                 logger.warning(f"Config EMBEDDING_DIM ({self.embedding_dim}) != Model output dim ({model_output_dim}). Using model dim.")
                 self.embedding_dim = model_output_dim # Use actual model dim

            logger.info(f"✅ TFLite model loaded. Input: {self.input_shape}, Output: {self.output_details[0]['shape']}")
        except Exception as e:
            logger.error(f"❌ Error loading TFLite model: {e}", exc_info=True)
            self.interpreter = None # Ensure it's None if failed
            components_loaded = False

        # Load Annoy Index & Mapping (only if model loaded successfully)
        if components_loaded:
            try:
                # index_path = self.config.ANNOY_INDEX_PATH
                index_path = self.config['ANNOY_INDEX_PATH'] # NEW WAY (Correct for Flask app.config)
                # map_path = self.config.ITEM_MAPPING_PATH
                map_path = self.config['ITEM_MAPPING_PATH'] # NEW WAY (Correct for Flask app.config)
                if not index_path.exists(): raise FileNotFoundError(f"Annoy index missing: {index_path}")
                if not map_path.exists(): raise FileNotFoundError(f"Item mapping missing: {map_path}")

                self.annoy_index = AnnoyIndex(self.embedding_dim, self.config["ANNOY_METRIC"])
                self.annoy_index.load(str(index_path))
                logger.info(f"✅ Annoy index loaded ({self.annoy_index.get_n_items()} items).")

                with open(map_path, 'r') as f:
                    self.item_mapping = json.load(f)
                logger.info(f"✅ Item mapping loaded ({len(self.item_mapping)} items).")
            except Exception as e:
                logger.error(f"❌ Error loading Annoy/Mapping: {e}", exc_info=True)
                self.annoy_index = None
                self.item_mapping = None
                components_loaded = False

        if not components_loaded:
             logger.warning("⚠️ One or more ML components failed to load.")


    def is_ready(self):
        """Check if all necessary components are loaded."""
        return all([self.interpreter, self.annoy_index, self.item_mapping, self.input_details, self.output_details])

    def get_embedding(self, input_data):
        """Runs inference using the loaded TFLite model."""
        if not self.is_ready():
             logger.error("Engine not ready for inference.")
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
        """Finds similar images using the Annoy index."""
        if not self.is_ready() or query_embedding is None:
            logger.error("Engine not ready or query embedding missing for search.")
            return []
        try:
            query_vector = query_embedding.flatten()
            neighbor_ids = self.annoy_index.get_nns_by_vector(query_vector, num_results + 1, search_k=-1)

            results = []
            for annoy_id in neighbor_ids:
                annoy_id_str = str(annoy_id)
                if annoy_id_str in self.item_mapping:
                    filename = self.item_mapping[annoy_id_str]
                    # Return only the filename, let the route handle URL generation
                    results.append(filename)

                if len(results) >= num_results:
                    break
            return results[:num_results] # Return list of filenames
        except Exception as e:
            logger.error(f"Error during Annoy search: {e}", exc_info=True)
            return []

    def get_recommendations(self, image_bytes):
         """Processes image bytes and returns list of recommended filenames."""
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

         # 3. Find Similar
         recommended_filenames = self.find_similar(
             query_embedding,
             self.config["NUM_RECOMMENDATIONS"]
         )
         return recommended_filenames # Returns list of filenames or []
    