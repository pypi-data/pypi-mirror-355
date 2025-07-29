import json
import requests

# Define an empty API key for now. Canvas will provide it at runtime.
# In a real-world scenario outside Canvas, you'd load this from an environment variable.
API_KEY = ""

def generate_image(description: str) -> str:
    """
    Generates an image based on a text description using imagen-3.0-generate-002.
    It calls the Gemini API (Imagen model) and returns a base64 encoded image URL.

    Args:
        description (str): A detailed text description of the image to generate.
                           This prompt is sent directly to the image generation model.

    Returns:
        str: A base64 encoded image URL (e.g., "data:image/png;base64,...")
             that can be used directly in web contexts (like HTML <img> tags),
             or an error message string if image generation fails.
    """
    # The API endpoint for the Imagen 3.0 model's predict method.
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={API_KEY}"
    
    # The payload structure required by the Imagen API.
    # 'instances' contains the prompt, and 'parameters' specifies generation options.
    payload = {
        "instances": {"prompt": description},
        "parameters": {"sampleCount": 1} # Requesting one image. Can be increased if desired.
    }
    
    # Headers for the API request, specifying JSON content type.
    headers = {
        "Content-Type": "application/json"
    }

    print(f"DEBUG: Calling Imagen for image generation with description: '{description[:50]}...'")

    try:
        # Send the POST request to the Imagen API.
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json() # Parse the JSON response

        # Check for the expected structure of a successful response:
        # It should contain 'predictions' and the base64 encoded bytes.
        if result.get("predictions") and len(result["predictions"]) > 0 and result["predictions"][0].get("bytesBase64Encoded"):
            # Construct a data URL. This format allows embedding the image directly in HTML or other contexts.
            image_url = f"data:image/png;base64,{result['predictions'][0]['bytesBase64Encoded']}"
            return image_url
        else:
            # Return an error if the response structure is unexpected or missing data.
            return f"Error: Unexpected image API response structure or missing base64 data: {result}"
            
    except requests.exceptions.RequestException as e:
        # Catch network-related errors or bad HTTP responses from the API.
        return f"Error: Image API request failed: {e}"
    except json.JSONDecodeError as e:
        # Catch errors if the API response is not valid JSON.
        return f"Error: Failed to decode JSON response from image API: {e}"
    except Exception as e:
        # Catch any other unexpected errors during the process.
        return f"Error: An unexpected error occurred during image generation: {e}"

# Example usage for testing this module directly.
# This block runs only when the script is executed directly (e.g., `python image_ai.py`)
# and not when it's imported as a module into another script.
if __name__ == "__main__":
    print("--- Testing qcsc_mod.image_ai ---")
    
    # Example 1: Generate an image of a futuristic car.
    print("\n--- Generating an image of a sleek, futuristic car ---")
    image_description_1 = "A sleek, futuristic electric car, concept art, high detail, vibrant colors, cyberpunk city background."
    image_data_url_1 = generate_image(image_description_1)
    
    if image_data_url_1.startswith("data:image"):
        print("Image generated successfully! (Base64 data URL below)")
        # In a real application, you would typically embed this URL in a web page
        # or save it to a file. For terminal, we just show a snippet.
        print(f"Image Data URL (first 100 chars): {image_data_url_1[:100]}...")
        # To actually view the image, you'd need to put this data URL into an HTML <img> tag
        # or save it to a file and open it.
    else:
        print(image_data_url_1) # Print the error message

    # Example 2: Generate an image of a abstract concept.
    print("\n--- Generating an image of abstract coding concepts ---")
    image_description_2 = "An abstract digital art piece representing data flow and machine learning algorithms, blue and green hues, geometric shapes, glowing lines."
    image_data_url_2 = generate_image(image_description_2)
    
    if image_data_url_2.startswith("data:image"):
        print("Image generated successfully! (Base64 data URL below)")
        print(f"Image Data URL (first 100 chars): {image_data_url_2[:100]}...")
    else:
        print(image_data_url_2) # Print the error message
