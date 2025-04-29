// static/js/script.js
// Get references to the HTML elements
const imageUploadInput = document.getElementById('imageUpload');
const recommendButton = document.getElementById('recommendBtn');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const imagePreview = document.getElementById('imagePreview');
const resultsPlaceholder = document.getElementById('results-placeholder');
const loader = document.getElementById('loader');

// Configuration
// IMPORTANT: Update this URL if your backend is hosted elsewhere
// For local testing, use 'http://localhost:5000' or 'http://127.0.0.1:5000'
// For deployment, use the actual URL of your deployed Flask app
const BACKEND_URL = '/recommend'; // Use relative path, assumes frontend/backend on same domain/port


// --- Event Listeners ---

// Enable button and show preview when a file is selected
imageUploadInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        recommendButton.disabled = false; // Enable the button
        statusDiv.textContent = 'Image selected. Click "Get Recommendations".';
        statusDiv.className = 'status-message info'; // Use info style
        resultsPlaceholder.style.display = 'none'; // Hide placeholder

        // --- Show Image Preview ---
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block'; // Show the preview element
        }
        reader.readAsDataURL(file); // Read the file as a data URL for preview

    } else {
        // No file selected or selection cancelled
        recommendButton.disabled = true; // Disable button
        statusDiv.textContent = 'Please select an image file.';
        statusDiv.className = 'status-message'; // Reset class
        imagePreview.style.display = 'none'; // Hide preview
        imagePreview.src = "#"; // Reset src
        resultsDiv.innerHTML = ''; // Clear results
        resultsPlaceholder.style.display = 'block'; // Show placeholder
    }
});

// Handle the recommendation button click
recommendButton.addEventListener('click', handleRecommendationRequest);

// --- Core Function ---

async function handleRecommendationRequest() {
    // 1. Get the selected file
    const file = imageUploadInput.files[0];

    // 2. Basic check (should already be handled by button disable state, but good practice)
    if (!file) {
        setStatus('Please select an image first!', 'error');
        return;
    }

    // 3. Prepare for API call - Update UI State
    setStatus('Processing...', 'loading');
    loader.style.display = 'block'; // Show loader
    resultsDiv.innerHTML = ''; // Clear previous results
    recommendButton.disabled = true; // Disable button during processing
    resultsPlaceholder.style.display = 'none'; // Hide placeholder

    // 4. Create FormData
    const formData = new FormData();
    formData.append('file', file); // Key 'file' must match Flask backend

    try {
        // 5. Fetch API call to the backend
        console.log(`Sending request to: ${BACKEND_URL}`); // Log backend URL being used
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            body: formData,
            // No headers needed for FormData generally
        });

        // 6. Process the response
        if (!response.ok) {
            // Try to get error message from backend JSON response
            let errorMsg = `Backend error: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData && errorData.error) {
                    errorMsg += ` - ${errorData.error}`;
                }
            } catch (e) {
                // Ignore if response wasn't JSON or failed to parse
                 console.warn("Could not parse error response as JSON.");
            }
             console.error('Backend Error Response:', response);
             throw new Error(errorMsg); // Throw an error to be caught below
        }

        // 7. Parse successful JSON response
        const data = await response.json();
        console.log("Received data:", data); // Log the received data

        // 8. Display results
        if (data.recommendations && data.recommendations.length > 0) {
            setStatus(`Found ${data.recommendations.length} recommendations!`, 'success');
            displayRecommendations(data.recommendations);
        } else {
            setStatus('No similar recommendations found.', 'info');
            resultsPlaceholder.textContent = 'No similar items found for the uploaded image.';
            resultsPlaceholder.style.display = 'block'; // Show placeholder message
        }

    } catch (error) {
        // 9. Handle fetch errors (network issue, CORS, or error thrown above)
        console.error('Frontend Fetch Error:', error);
        setStatus(`Error: ${error.message}`, 'error');
        resultsPlaceholder.textContent = 'An error occurred while fetching recommendations.';
        resultsPlaceholder.style.display = 'block'; // Show placeholder message
    } finally {
        // 10. Clean up UI state regardless of success or failure
        loader.style.display = 'none'; // Hide loader
        // Re-enable button only if a file is still selected
        if (imageUploadInput.files.length > 0) {
             recommendButton.disabled = false;
        }
        // Optional: Clear the file input after processing
        // imageUploadInput.value = ''; // This also triggers the 'change' event again
        // imagePreview.style.display = 'none';
        // statusDiv.textContent = 'Select a new image.';
        // statusDiv.className = 'status-message';
    }
}

// --- Helper Functions ---

function setStatus(message, type = 'info') {
    statusDiv.textContent = message;
    // Apply appropriate CSS class based on type (success, error, loading, info)
    statusDiv.className = `status-message ${type}`;
}

function displayRecommendations(imageUrlArray) {
    resultsDiv.innerHTML = ''; // Clear any previous content (like placeholders)
    resultsPlaceholder.style.display = 'none'; // Ensure placeholder is hidden

    imageUrlArray.forEach(relativeUrl => {
        const imgElement = document.createElement('img');

        // IMPORTANT: Construct the full URL based on how the Flask app serves static files
        // Since Flask returns '/static/images/filename.jpg', we just need the base origin if served separately,
        // but if served from the same origin, the relative path works directly.
        imgElement.src = relativeUrl; // Use the path returned by Flask directly

        imgElement.alt = "Recommendation";
        imgElement.onerror = () => {
            console.warn(`Could not load image: ${relativeUrl}`);
            imgElement.alt = "Recommendation (load failed)";
            // Optionally replace with a placeholder image URL
            // imgElement.src = '/static/images/placeholder.png';
        };
        resultsDiv.appendChild(imgElement);
    });
}

// --- Initial State ---
// Ensure button is disabled initially as no file is selected
recommendButton.disabled = true;
imagePreview.style.display = 'none'; // Hide preview initially