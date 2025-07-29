import os

def save_text_to_file(filename: str, content: str, overwrite: bool = False) -> str:
    """
    Saves the given text content to a specified file.

    Args:
        filename (str): The name of the file to save the content to.
        content (str): The text content to write into the file.
        overwrite (bool): If True, overwrite the file if it already exists.
                          If False and the file exists, it will return an error.

    Returns:
        str: A success message, or an error message if the operation fails.
    """
    if os.path.exists(filename) and not overwrite:
        return f"Error: File '{filename}' already exists. Set overwrite=True to force overwrite."
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Content successfully saved to '{filename}'."
    except IOError as e:
        return f"Error saving file '{filename}': {e}"
    except Exception as e:
        return f"An unexpected error occurred while saving file '{filename}': {e}"

def read_text_from_file(filename: str) -> str:
    """
    Reads text content from a specified file.

    Args:
        filename (str): The name of the file to read content from.

    Returns:
        str: The content of the file, or an error message if reading fails.
    """
    if not os.path.exists(filename):
        return f"Error: File '{filename}' not found."
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except IOError as e:
        return f"Error reading file '{filename}': {e}"
    except Exception as e:
        return f"An unexpected error occurred while reading file '{filename}': {e}"

# You can add more actions here as the library evolves, for example:
# - def create_directory(path: str) -> str:
# - def list_directory_contents(path: str) -> list[str]:
# - def send_email(to_address: str, subject: str, body: str) -> str: (would require external configuration)

# Example usage for testing this module directly.
# This block runs only when the script is executed directly (e.g., `python actions.py`)
# and not when it's imported as a module into another script.
if __name__ == "__main__":
    print("--- Testing qcsc_mod.actions ---")

    test_filename = "test_output.txt"
    test_content = "This is a test content that will be saved to a file by qcsc_mod.actions."

    # Test saving text to a new file
    print(f"\n--- Saving content to '{test_filename}' (first attempt) ---")
    save_result_1 = save_text_to_file(test_filename, test_content)
    print(save_result_1)

    # Test attempting to save to an existing file without overwrite
    print(f"\n--- Saving content to '{test_filename}' (second attempt, no overwrite) ---")
    save_result_2 = save_text_to_file(test_filename, "New content.")
    print(save_result_2)

    # Test saving to an existing file with overwrite
    print(f"\n--- Saving content to '{test_filename}' (third attempt, with overwrite) ---")
    save_result_3 = save_text_to_file(test_filename, "This content overwrites the old one.", overwrite=True)
    print(save_result_3)

    # Test reading content from the file
    print(f"\n--- Reading content from '{test_filename}' ---")
    read_result = read_text_from_file(test_filename)
    print(f"Read content: {read_result}")

    # Clean up the test file
    if os.path.exists(test_filename):
        os.remove(test_filename)
        print(f"\nCleaned up test file: '{test_filename}'.")

    # Test reading from a non-existent file
    print(f"\n--- Reading from a non-existent file ('non_existent.txt') ---")
    non_existent_read = read_text_from_file("non_existent.txt")
    print(non_existent_read)
