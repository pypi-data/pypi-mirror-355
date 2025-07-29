import json
import requests

# Define an empty API key for now. Canvas will provide it at runtime.
# In a real-world scenario outside Canvas, you'd load this from an environment variable.
API_KEY = "" 

def _call_gemini_api(prompt, model_name="gemini-2.0-flash", generation_config=None):
    """
    Internal function to make a generic call to the Gemini API.
    Handles the HTTP request, JSON serialization/deserialization, and basic error checking.

    Args:
        prompt (str): The text prompt for the LLM.
        model_name (str): The name of the Gemini model to use (default: "gemini-2.0-flash").
                          For text generation, "gemini-2.0-flash" is typically used.
        generation_config (dict, optional): Configuration for structured responses, etc.
                                            If provided, this is passed directly to the API.

    Returns:
        dict: The content part of the successful JSON response from the API,
              or an error dictionary if an issue occurred.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    
    # Structure the chat history for the API request.
    # The 'user' role sends the prompt to the model.
    chat_history = []
    chat_history.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Prepare the main payload for the API request.
    payload = {"contents": chat_history}
    if generation_config:
        payload["generationConfig"] = generation_config # Add generation config if provided

    # Set the content type header for the API request.
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Send the POST request to the Gemini API.
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx status codes)
        result = response.json() # Parse the JSON response from the API
        
        # Check if the response contains valid candidates and content.
        # This is the expected structure for successful text generation.
        if result.get("candidates") and result["candidates"][0].get("content"):
            return result["candidates"][0]["content"]
        else:
            # If the structure is not as expected, return an error.
            return {"error": "Unexpected API response structure", "details": result}
            
    except requests.exceptions.RequestException as e:
        # Catch network-related errors or bad HTTP responses.
        return {"error": f"API request failed: {e}"}
    except json.JSONDecodeError as e:
        # Catch errors if the response is not valid JSON.
        return {"error": f"Failed to decode JSON response from LLM: {e}"}
    except Exception as e:
        # Catch any other unexpected errors.
        return {"error": f"An unexpected error occurred during API call: {e}"}

def generate_text(user_prompt: str) -> str:
    """
    Generates free-form text based on a user prompt using the Gemini LLM.

    Args:
        user_prompt (str): The prompt provided by the user. This is sent to the LLM
                           to guide the text generation.

    Returns:
        str: The generated text from the LLM, or an error message if generation fails.
    """
    # Craft a clear prompt for the LLM based on the user's request.
    prompt = f"Generate text based on the following request: {user_prompt}"
    
    print(f"DEBUG: Calling Gemini for text generation with prompt: '{prompt[:50]}...'") # Debugging print
    
    # Call the internal Gemini API function.
    response_content = _call_gemini_api(prompt, model_name="gemini-2.0-flash")

    # Check if the API call returned an error.
    if isinstance(response_content, dict) and "error" in response_content:
        return f"Error: {response_content['error']}"
    
    # Extract the generated text from the successful response.
    if response_content.get("parts") and response_content["parts"][0].get("text"):
        return response_content["parts"][0]["text"]
    else:
        # If text is not found in the expected format, return a generic error.
        return "Could not generate text. Unexpected response format from LLM."

def brainstorm_ideas(topic: str, quantity: int = 3) -> list[str]:
    """
    Brainstorms a list of ideas for a given topic using the Gemini LLM.
    It requests the LLM to return ideas in a structured JSON array.

    Args:
        topic (str): The topic for which to brainstorm ideas.
        quantity (int): The number of ideas to generate. Defaults to 3.

    Returns:
        list[str]: A list of generated ideas (strings), or a list containing
                   an error message if generation or parsing fails.
    """
    # Prompt the LLM to generate a specific quantity of ideas in JSON array format.
    prompt = f"Generate exactly {quantity} distinct ideas for the topic '{topic}'. Provide them as a JSON array of strings, like [\"idea1\", \"idea2\"]."
    
    # Define the generation configuration to request a structured JSON response.
    generation_config = {
        "responseMimeType": "application/json",
        "responseSchema": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        }
    }

    print(f"DEBUG: Calling Gemini for brainstorming ideas with topic: '{topic}' (expecting JSON output)") # Debugging print
    
    # Call the internal Gemini API function with the structured generation config.
    response_content = _call_gemini_api(prompt, model_name="gemini-2.0-flash", generation_config=generation_config)

    # Check if the API call returned an error.
    if isinstance(response_content, dict) and "error" in response_content:
        return [f"Error: {response_content['error']}"]
    
    try:
        # The LLM's response for structured output comes as a JSON string
        # within the 'text' part. We need to parse this JSON string.
        if response_content.get("parts") and response_content["parts"][0].get("text"):
            json_string = response_content["parts"][0]["text"]
            ideas = json.loads(json_string) # Parse the JSON string into a Python object (list).
            
            # Validate that the parsed result is indeed a list of strings.
            if isinstance(ideas, list) and all(isinstance(item, str) for item in ideas):
                return ideas
            else:
                return ["Error: LLM did not return ideas in the expected list of strings format (parsed but incorrect type)."]
        else:
            return ["Error: No text parts found in LLM response for ideas (expected JSON string)."]
    except json.JSONDecodeError:
        # Catch errors if the LLM's response text is not valid JSON.
        return ["Error: LLM response was not valid JSON for ideas."]
    except Exception as e:
        # Catch any other unexpected errors during processing.
        return [f"An unexpected error occurred while processing ideas: {e}"]

# Example usage for testing this module directly.
# This block runs only when the script is executed directly (e.g., `python content_ai.py`)
# and not when it's imported as a module into another script.
if __name__ == "__main__":
    print("--- Testing qcsc_mod.content_ai ---")

    # Test free-form text generation
    print("\n--- Generating a short story about a heroic coding adventure ---")
    story_prompt = "a short story about a brave space pilot exploring a new planet, encountering friendly aliens who love coding."
    story = generate_text(story_prompt)
    print(story)

    # Test brainstorming ideas for a practical topic
    print("\n--- Brainstorming marketing slogans for a new eco-friendly coffee shop ---")
    slogans = brainstorm_ideas("marketing slogans for a new eco-friendly coffee shop", quantity=5)
    if isinstance(slogans, list) and not slogans[0].startswith("Error"):
        for i, slogan in enumerate(slogans):
            print(f"{i+1}. {slogan}")
    else:
        print(slogans[0]) # Print the error message

    # Test brainstorming with a different quantity
    print("\n--- Brainstorming unusual pet ideas (2 ideas) ---")
    pets = brainstorm_ideas("unusual pet ideas", quantity=2)
    if isinstance(pets, list) and not pets[0].startswith("Error"):
        for i, pet in enumerate(pets):
            print(f"{i+1}. {pet}")
    else:
        print(pets[0]) # Print the error message