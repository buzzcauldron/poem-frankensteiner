import random
import re
import argparse
import os
import glob

# --- Constants for Configuration ---
REFERENCE_SHORT_LENGTH = 1000
REFERENCE_LONG_LENGTH = 20000
SHORT_TEXT_MIN_KEEP = 0.08  # Minimum for short texts (allows variation up to 10%)
SHORT_TEXT_MAX_KEEP = 0.10  # Maximum 10% for short texts
LONG_TEXT_MIN_KEEP = 0.01   # Minimum 1% for long texts
LONG_TEXT_MAX_KEEP = 0.02   # Maximum for long texts (biased toward lower retention)


def clean_text(text):
    """
    Converts text to lowercase and removes all special characters.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Keep only letters, numbers, space
    text = re.sub(r'\s+', ' ', text).strip()  # Collapse multiple spaces
    return text


def estimate_syllables(word):
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


def generate_title_filename(cleaned_text, input_filename):
    """
    Generates a titled filename from the input text or filename.
    """
    words = cleaned_text.split()
    if words:
        # Use 2-4 random words from the text for the title
        num_words = min(random.randint(2, 4), len(words))
        title_words = random.sample(words, num_words)
        title = '_'.join(title_words)
    else:
        # Fallback to input filename base
        base_name = os.path.splitext(os.path.basename(input_filename))[0]
        title = base_name
    
    return f"{title}.txt"


def create_broken_sentence_text(text, percentage_to_keep, min_syllables=6, max_syllables=12):
    """
    Highly reduces text by sampling words and formats them into lines with 6-12 syllables.
    Words remain lowercase with no punctuation.
    """
    words = text.split()

    if not words:
        return ""

    # Calculate how many words to keep
    k = int(len(words) * percentage_to_keep)
    if k == 0 and len(words) > 0:
        k = 1  # Ensure we keep at least one word

    # Sample words randomly
    sampled_words = random.sample(words, k)
    
    # Group words into lines based on syllable count (6-12 syllables per line)
    all_lines = []
    current_line_words = []
    current_line_syllables = 0
    
    for word in sampled_words:
        word_syllables = estimate_syllables(word)
        
        # Check if adding this word would exceed max_syllables
        if (current_line_syllables + word_syllables > max_syllables) and (current_line_syllables >= min_syllables):
            # Current line has enough syllables, start a new line
            all_lines.append(' '.join(current_line_words))
            current_line_words = [word]
            current_line_syllables = word_syllables
        else:
            # Add to current line
            current_line_words.append(word)
            current_line_syllables += word_syllables
    
    # Add the last line if it has any content
    if current_line_words:
        all_lines.append(' '.join(current_line_words))
    
    return '\n'.join(all_lines)


def calculate_biased_retention(text_length, fixed_retention=None):
    """
    Calculates biased retention percentage based on text length.
    High volume texts get lower retention (closer to 1%), 
    shorter texts get higher retention (closer to 10%).
    
    If fixed_retention is provided, returns that value instead.
    """
    if fixed_retention is not None:
        return fixed_retention
    
    # Normalize text length between reference points
    normalized_length = (text_length - REFERENCE_SHORT_LENGTH) / \
                        (REFERENCE_LONG_LENGTH - REFERENCE_SHORT_LENGTH)
    length_factor = max(0.0, min(1.0, normalized_length))  # Clamp between 0.0 and 1.0
    
    # Interpolate between short and long text retention ranges
    current_min_keep = (SHORT_TEXT_MIN_KEEP * (1 - length_factor)) + \
                       (LONG_TEXT_MIN_KEEP * length_factor)
    current_max_keep = (SHORT_TEXT_MAX_KEEP * (1 - length_factor)) + \
                       (LONG_TEXT_MAX_KEEP * length_factor)
    
    # Pick a random percentage from within the biased range
    random_keep_percentage = random.uniform(current_min_keep, current_max_keep)
    return random_keep_percentage


def process_file(input_file, output_dir=None, fixed_retention=None):
    """
    Process a single text file and create broken-line sentence output.
    If fixed_retention is None, calculates biased retention based on text length.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

    # Clean the text
    cleaned_text = clean_text(original_text)
    
    if not cleaned_text.strip():
        print(f"Warning: '{input_file}' had no words after cleaning.")
        return None

    # Calculate biased retention based on text length
    text_length = len(cleaned_text)
    percentage_to_keep = calculate_biased_retention(text_length, fixed_retention)
    reduction_percentage = (1 - percentage_to_keep) * 100

    # Create the broken sentence text
    broken_text = create_broken_sentence_text(cleaned_text, percentage_to_keep)
    
    # Generate titled filename from the text
    title_filename = generate_title_filename(cleaned_text, input_file)
    
    # Determine output filename
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, title_filename)
    else:
        output_file = title_filename
    
    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(broken_text)
        num_lines = len(broken_text.splitlines())
        print(f"Created: {output_file} ({num_lines} lines, {reduction_percentage:.0f}% reduction)")
        return output_file
    except Exception as e:
        print(f"An error occurred while writing the output file: {e}")
        return None


# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create highly reduced broken-line texts grouped into lines with 6-12 syllables."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input .txt file or directory containing .txt files"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Directory to save output files (default: same as input)"
    )
    parser.add_argument(
        "--keep",
        "-k",
        type=float,
        default=None,
        help="Fixed percentage of words to keep (0.01-0.10). If not specified, uses biased random retention (10%%-1%%) based on text length."
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Process all .txt files in the current directory"
    )
    
    args = parser.parse_args()

    # Determine what to process
    files_to_process = []
    
    if args.all:
        # Process all .txt files in current directory
        files_to_process = glob.glob("*.txt")
        if not files_to_process:
            print("No .txt files found in current directory.")
            exit(1)
    elif args.input:
        if os.path.isfile(args.input):
            if not args.input.endswith('.txt'):
                print(f"Warning: '{args.input}' is not a .txt file. Processing anyway...")
            files_to_process = [args.input]
        elif os.path.isdir(args.input):
            files_to_process = glob.glob(os.path.join(args.input, "*.txt"))
            if not files_to_process:
                print(f"No .txt files found in directory '{args.input}'.")
                exit(1)
        else:
            print(f"Error: '{args.input}' is not a valid file or directory.")
            exit(1)
    else:
        # No input specified and --all not used
        parser.print_help()
        print("\nError: You must specify an input file/directory or use --all to process all .txt files in the current directory.")
        exit(1)
    
    if args.keep is not None:
        print(f"Processing {len(files_to_process)} file(s) with fixed {args.keep*100:.1f}% word retention...")
    else:
        print(f"Processing {len(files_to_process)} file(s) with biased random retention (10%%-1%%)...")
    print("-" * 50)
    
    for file_path in files_to_process:
        process_file(file_path, args.output_dir, args.keep)
    
    print("-" * 50)
    print("Done!")

