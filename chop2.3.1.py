import random
import time
import sys
import argparse
import re
import uuid
import os  # <-- Added for API key
import google.generativeai as genai  # <-- Added for API

# --- Constants for Configuration ---
TARGET_SYLLABLES_PER_LINE = 10
PRINT_DELAY = 0.02
REFERENCE_SHORT_LENGTH = 1000
REFERENCE_LONG_LENGTH = 20000
SHORT_TEXT_MIN_KEEP = 0.15
SHORT_TEXT_MAX_KEEP = 0.30
LONG_TEXT_MIN_KEEP = 0.01
LONG_TEXT_MAX_KEEP = 0.10


def autocorrect_text_api(text_to_correct, api_model):
    """
    Uses the Gemini API to correct spelling and grammar.
    """
    print("...Sending text to API for spellchecking (this may take a moment)...")
    
    # This is the prompt we send to the AI
    prompt = f"""
    Please correct the spelling and grammar of the following text.
    Only return the corrected text. Do not add any commentary, preamble, or explanations.
    Just return the corrected text.

    ---
    {text_to_correct}
    ---
    """
    
    try:
        response = api_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"\n--- API Error ---\n{e}\n---")
        print("Returning original text due to API error.")
        return text_to_correct


def clean_text(text):
    """
    Converts text to lowercase and removes all special characters.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text) # Keep only letters, numbers, space
    text = re.sub(r'\s+', ' ', text).strip() # Collapse multiple spaces
    return text


def print_slowly(text, delay=PRINT_DELAY):
    """Prints text one character at a time to be human-readable."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def estimate_syllABLES(word):
    """
    Estimates the number of syllables in a single word.
    """
    word = word.lower().strip()
    
    if not word or not re.search(r'[a-z]', word):
        return 0
    if len(word) <= 3:
        return 1
        
    if word.endswith('e'):
        if not (word.endswith('le') and re.search(r'[^aeiouy]le$', word)):
            word = word[:-1]

    vowel_groups = re.findall(r'[aeiouy]+', word)
    count = len(vowel_groups)
    
    if count == 0:
        return 1
    return count


def randomly_reduce_and_lineate_text(text, percentage_to_keep):
    """
    Reduces text by sampling words and formats them into
    lines based on a target syllable count.
    """
    words = text.split()

    if not words:
        return "(The source file was empty or had no words after cleaning.)"

    k = int(len(words) * percentage_to_keep)
    if k == 0 and len(words) > 0:
        k = 1  # Ensure we keep at least one word

    sampled_words = random.sample(words, k)
    
    all_lines = []
    current_line_words = []
    current_line_syllables = 0
    
    for word in sampled_words:
        word_syllables = estimate_syllABLES(word)
    
        if (current_line_syllables + word_syllables > TARGET_SYLLABLES_PER_LINE) and (current_line_syllables > 0):
            all_lines.append(' '.join(current_line_words))
            current_line_words = [word]
            current_line_syllables = word_syllables
        else:
            current_line_words.append(word)
            current_line_syllables += word_syllables
    
    if current_line_words:
         all_lines.append(' '.join(current_line_words))
    
    return '\n'.join(all_lines)


# --- Main execution ---
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Create a 'cut-up' poem from a source text file."
    )
    parser.add_argument(
        "filename", help="The path to the source .txt file"
    )
    parser.add_argument(
        "--spellcheck",
        action="store_true",
        help="Run the API-based spellchecker on the source text."
    )
    
    args = parser.parse_args()

    try:
        with open(args.filename, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

    text_to_clean = original_text
    
    # --- MODIFIED API LOGIC ---
    if args.spellcheck:
        # 1. Get the API key from your environment
        api_key = os.getenv("AIzaSyBg5DbNaZ1SGNcoWGtSLuA-lBJgB1dEhag")
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set.")
            print("Please set it to use the --spellcheck feature.")
            sys.exit(1)
        
        # 2. Configure the API
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # 3. Call the API function
            text_to_clean = autocorrect_text_api(original_text, model)
            
        except Exception as e:
            print(f"Failed to initialize Gemini API: {e}")
            sys.exit(1)
    
    # --- END MODIFICATION ---
    
    cleaned_text = clean_text(text_to_clean)
    text_length = len(cleaned_text)

    # Print the (un-cleaned) original text
    print("--- Original Text ---")
    print(original_text)
    print("\n" + "=" * 30 + "\n")
    time.sleep(1)

    # Calculate biased reduction
    normalized_length = (text_length - REFERENCE_SHORT_LENGTH) / \
                        (REFERENCE_LONG_LENGTH - REFERENCE_SHORT_LENGTH)
    length_factor = max(0.0, min(1.0, normalized_length))
    current_min_keep = (SHORT_TEXT_MIN_KEEP * (1 - length_factor)) + \
                       (LONG_TEXT_MIN_KEEP * length_factor)
    current_max_keep = (SHORT_TEXT_MAX_KEEP * (1 - length_factor)) + \
                       (LONG_TEXT_MAX_KEEP * length_factor)
    
    random_keep_percentage = random.uniform(current_min_keep, current_max_keep)
    reduction_percentage = (1 - random_keep_percentage) * 100

    # Create the reduced text
    reduced_text = randomly_reduce_and_lineate_text(
        cleaned_text,
        percentage_to_keep=random_keep_percentage,
    )

    # PRINT SLOWLY
    print(f"--- Reduced & Cleaned Text ({reduction_percentage:.0f}% reduction) ---")
    print_slowly(reduced_text)

    # FILE OUTPUT LOGIC
    source_words_list = cleaned_text.split()
    output_filename = "poem_output.txt" 
    if source_words_list:
        num_words = random.randint(1, 4)
        num_words = min(num_words, len(source_words_list)) 
        title_words = random.sample(source_words_list, num_words)
        output_filename = '_'.join(title_words) + ".txt"

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(reduced_text)
        print(f"\nSuccessfully saved poem to: {output_filename}")
    except Exception as e:
        print(f"\nAn error occurred while writing the output file: {e}")