import datetime
import os  # Added os import
import pytz

# Define necessary path constants locally within this module
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPT_FILENAME = "System Prompt.md"
SYSTEM_PROMPT_PATH = os.path.join(SCRIPT_DIR, SYSTEM_PROMPT_FILENAME)

def get_contextual_system_prompt() -> str:
    """
    Constructs the system prompt by prepending the current date and time
    to the content of the System Prompt.md file.
    """
    # Get current time in UK timezone
    # 'Europe/London' timezone correctly handles BST (British Summer Time) and GMT (Greenwich Mean Time)
    uk_timezone = pytz.timezone('Europe/London')
    now = datetime.datetime.now(uk_timezone)
    # Format for easy readability, e.g., "Monday, 26 May 2025 at 07:00 PM BST"
    date_time_str = now.strftime("%A, %d %B %Y at %I:%M %p %Z")

    prompt_header = f"Current UK date and time: {date_time_str}\n\n"

    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            base_prompt = f.read()
        return prompt_header + base_prompt
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {SYSTEM_PROMPT_PATH}")
        # Fallback if System Prompt.md is missing
        return prompt_header + "You are a helpful assistant."

if __name__ == '__main__':
    # For testing the script directly
    print(get_contextual_system_prompt())
