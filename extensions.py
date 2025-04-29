# import numpy as np
# import json
# from joblib import load
# # Load the KNN model
# knn_model = load('data/knn_model.joblib')
# # Initialize empty lists to store embeddings and filenames
# all_embeddings_list = []
# all_filenames_list = []

# # --- Create product_embeddings.npy ---
# embeddings_array = np.array(knn_model).astype(np.float32) # Ensure float32 for consistency
# # Load embeddings from .npy file
# embeddings_array = np.load('data/product_embeddings.npy')
# print(f"Saved embeddings with shape: {embeddings_array.shape}")

# # --- Create image_filenames.json ---
# with open('data/image_filenames.json', 'w') as f:
#     json.dump(all_filenames_list, f)
# print(f"Saved {len(all_filenames_list)} filenames.")