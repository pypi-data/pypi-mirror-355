import json
import requests
import os
import sys

# Add the parent directory to the Python path to allow importing modules from the same package
# This is mainly for direct execution like `python main.py` for testing purposes.
# When installed as a package, imports like `from .content_ai import ...` will work automatically.
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

# Import functions from other modules in the qcsc_mod package
from qcsc_mod.content_ai import _call_gemini_api, generate_text, brainstorm_ideas
from qcsc_mod.image_ai import generate_image
from qcsc_mod.actions import save_text_to_file, read_text_from_file

# Define an empty API key for now. Canvas will provide it at runtime.
# In a real-world scenario outside Canvas, you'd load this from an environment variable.
API_KEY = ""

def _parse_user_intent_with_llm(user_instruction: str) -> dict:
    """
    Uses an LLM to parse a natural language instruction and determine the
    intended action and its parameters.

    Args:
        user_instruction (str): The natural language instruction from the user.

    Returns:
        dict: A dictionary containing the 'action_type' and its associated 'parameters',
              or an error dictionary if parsing fails.
    """
    prompt = f"""
    The user wants to perform an action. Analyze the following instruction and extract the intended `action_type` and its `parameters`.
    
    Instruction: "{user_instruction}"

    Possible action_types and their expected parameters:
    - "generate_text": {{ "prompt": "str" }} (e.g., "write a poem about stars")
    - "summarize": {{ "text_to_summarize": "str", "target_length": "str" }} (e.g., "summarize this long text", "make it short")
    - "brainstorm_ideas": {{ "topic": "str", "quantity": "int" }} (e.g., "give me 5 ideas for a new app")
    - "generate_image": {{ "description": "str" }} (e.g., "create an image of a red dragon")
    - "save_text": {{ "filename": "str", "content": "str", "overwrite": "bool" }} (e.g., "save 'Hello World' to my_file.txt", "overwrite existing")
    - "read_text": {{ "filename": "str" }} (e.g., "read content from notes.txt")

    If the instruction cannot be mapped to a known action, use "unknown_action" with a "reason" parameter.

    Return the output as a JSON object with the following structure:
    {{
        "action_type": "string",
        "parameters": {{ /* object based on action_type */ }}
    }}
    """

    # Define the schema for the structured response from the LLM
    generation_config = {
        "responseMimeType": "application/json",
        "responseSchema": {
            "type": "OBJECT",
            "properties": {
                "action_type": {"type": "STRING"},
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "prompt": {"type": "STRING"},
                        "text_to_summarize": {"type": "STRING"},
                        "target_length": {"type": "STRING"},
                        "topic": {"type": "STRING"},
                        "quantity": {"type": "INTEGER"},
                        "description": {"type": "STRING"},
                        "filename": {"type": "STRING"},
                        "content": {"type": "STRING"},
                        "overwrite": {"type": "BOOLEAN"},
                        "reason": {"type": "STRING"} # For unknown actions
                    },
                    "additionalProperties": False # Ensure only specified properties are returned
                }
            },
            "required": ["action_type", "parameters"]
        }
    }

    print(f"DEBUG: LLM parsing user instruction: '{user_instruction[:70]}...'")
    response_content = _call_gemini_api(prompt, model_name="gemini-2.0-flash", generation_config=generation_config)

    if isinstance(response_content, dict) and "error" in response_content:
        return {"action_type": "error", "parameters": {"reason": f"LLM parsing failed: {response_content['error']}"}}
    
    try:
        if response_content.get("parts") and response_content["parts"][0].get("text"):
            parsed_json = json.loads(response_content["parts"][0]["text"])
            if isinstance(parsed_json, dict) and "action_type" in parsed_json and "parameters" in parsed_json:
                return parsed_json
            else:
                return {"action_type": "error", "parameters": {"reason": "LLM returned invalid JSON structure for action parsing."}}
        else:
            return {"action_type": "error", "parameters": {"reason": "LLM response for action parsing had no text parts."}}
    except json.JSONDecodeError:
        return {"action_type": "error", "parameters": {"reason": "LLM response for action parsing was not valid JSON."}}
    except Exception as e:
        return {"action_type": "error", "parameters": {"reason": f"An unexpected error occurred during LLM parsing response: {e}"}}


def perform_action(user_instruction: str) -> str:
    """
    The main entry point for the qcsc_mod orchestrator.
    It takes a natural language instruction, uses an LLM to parse intent,
    and executes the corresponding action.

    Args:
        user_instruction (str): A natural language instruction from the user.

    Returns:
        str: A message indicating the result of the action, or an error message.
    """
    parsed_intent = _parse_user_intent_with_llm(user_instruction)
    
    action_type = parsed_intent.get("action_type")
    parameters = parsed_intent.get("parameters", {})

    if action_type == "error":
        return f"Orchestration Error: {parameters.get('reason', 'Unknown parsing error.')}"
    elif action_type == "generate_text":
        prompt = parameters.get("prompt")
        if not prompt:
            return "Error: 'generate_text' action requires a 'prompt' parameter."
        return generate_text(prompt)
    elif action_type == "summarize":
        text_to_summarize = parameters.get("text_to_summarize")
        target_length = parameters.get("target_length", "medium")
        if not text_to_summarize:
            return "Error: 'summarize' action requires 'text_to_summarize' parameter."
        
        # For simplicity, let's make a generic summarize call via generate_text
        # In a more advanced version, you'd have a dedicated summarize function
        summary_prompt = f"Summarize the following text, aiming for a {target_length} length: {text_to_summarize}"
        return generate_text(summary_prompt)
    elif action_type == "brainstorm_ideas":
        topic = parameters.get("topic")
        quantity = parameters.get("quantity", 3)
        if not topic:
            return "Error: 'brainstorm_ideas' action requires a 'topic' parameter."
        ideas = brainstorm_ideas(topic, quantity)
        if isinstance(ideas, list):
            if ideas and ideas[0].startswith("Error"): # Check if brainstorm_ideas returned an error list
                return ideas[0]
            return "Ideas:\n" + "\n".join([f"- {idea}" for idea in ideas])
        return "Error: Unexpected return from brainstorm_ideas."
    elif action_type == "generate_image":
        description = parameters.get("description")
        if not description:
            return "Error: 'generate_image' action requires a 'description' parameter."
        # Call the image_ai module's function
        image_url = generate_image(description)
        if image_url.startswith("data:image"):
            return f"Image generated successfully. You can view it using this data URL: {image_url[:100]}..." # Truncate for display
        return image_url # Will be an error message if generation failed
    elif action_type == "save_text":
        filename = parameters.get("filename")
        content = parameters.get("content")
        overwrite = parameters.get("overwrite", False)
        if not filename or content is None:
            return "Error: 'save_text' action requires 'filename' and 'content' parameters."
        return save_text_to_file(filename, content, overwrite)
    elif action_type == "read_text":
        filename = parameters.get("filename")
        if not filename:
            return "Error: 'read_text' action requires a 'filename' parameter."
        return read_text_from_file(filename)
    elif action_type == "unknown_action":
        reason = parameters.get("reason", "The instruction could not be understood.")
        return f"Could not perform action: {reason}"
    else:
        return f"Error: Unrecognized action type '{action_type}' from LLM. Please refine your instruction."


# Example usage for testing this module directly.
# This block runs only when the script is executed directly (e.g., `python main.py`)
# and not when it's imported as a module into another script.
if __name__ == "__main__":
    print("--- Testing qcsc_mod.main (Universal Content & Action Orchestrator) ---")
    print("Type your instruction (e.g., 'write a short poem about coding', 'summarize this text: ...', 'generate 3 ideas for a sci-fi novel'):")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nYour instruction: ").strip()
        if user_input.lower() == 'quit':
            print("Exiting qcsc_mod orchestrator.")
            break
        if not user_input:
            print("Please enter an instruction.")
            continue

        print(f"\nProcessing instruction: '{user_input}'...")
        result = perform_action(user_input)
        print("\n--- Result ---")
        print(result)
        print("--------------")
