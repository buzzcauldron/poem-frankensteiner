import random
import re
import argparse
import os
import glob
import base64

# --- Constants for Configuration ---
REFERENCE_SHORT_LENGTH = 1000
REFERENCE_LONG_LENGTH = 20000
SHORT_TEXT_MIN_KEEP = 0.24  # Minimum for short texts (3x increase: 24%)
SHORT_TEXT_MAX_KEEP = 0.30  # Maximum 30% for short texts (3x increase)
LONG_TEXT_MIN_KEEP = 0.03   # Minimum 3% for long texts (3x increase)
LONG_TEXT_MAX_KEEP = 0.06   # Maximum 6% for long texts (3x increase)

# Base syllable ranges (original: 6-12)
BASE_MIN_SYLLABLES = 6
BASE_MAX_SYLLABLES = 12
# Multiplier range for 3-5x increase, but reduced to get 3x more lines
# To get 3x more lines, we need shorter lines (divide by 3)
MULTIPLIER_MIN = 1.0  # Reduced from 3.0 to get more lines
MULTIPLIER_MAX = 1.67  # Reduced from 5.0 (approximately 5/3) to get more lines


def clean_text(text):
    """
    Converts text to lowercase and removes all special characters and numbers.
    """
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)  # Keep only letters and space
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


def encrypt_word(word):
    """
    Encrypts a word using a simple cipher (ROT13-like with base64 encoding).
    """
    if not word:
        return ""
    # Use base64 encoding for encryption effect
    encoded = base64.b64encode(word.encode()).decode()
    # Truncate to similar length for visual effect
    return encoded[:len(word) + 2] if len(encoded) > len(word) else encoded


def get_random_line_syllable_limits():
    """
    Returns random min and max syllable limits that are 3-5x the base range.
    Each call returns different values for variation.
    """
    multiplier = random.uniform(MULTIPLIER_MIN, MULTIPLIER_MAX)
    min_syllables = int(BASE_MIN_SYLLABLES * multiplier)
    max_syllables = int(BASE_MAX_SYLLABLES * multiplier)
    # Add some additional random fluctuation (±10%)
    min_fluctuation = int(min_syllables * 0.1)
    max_fluctuation = int(max_syllables * 0.1)
    min_syllables += random.randint(-min_fluctuation, min_fluctuation)
    max_syllables += random.randint(-max_fluctuation, max_fluctuation)
    # Ensure min is always less than max and both are positive
    min_syllables = max(1, min_syllables)
    max_syllables = max(min_syllables + 1, max_syllables)
    return min_syllables, max_syllables


def create_broken_sentence_text_with_flicker(text, percentage_to_keep):
    """
    Creates text with alternating original and encrypted words for flickering effect.
    Returns HTML with CSS animation. Uses line-based layout with 2-3x spacing, centered, and more lines.
    """
    words = text.split()

    if not words:
        return ""

    # Calculate how many words to keep (increase to get more lines)
    k = int(len(words) * percentage_to_keep)
    if k == 0 and len(words) > 0:
        k = 1  # Ensure we keep at least one word

    # Sample words randomly
    sampled_words = random.sample(words, k)
    
    # Group words into lines based on syllable count with random fluctuation
    # Increase line length 3x
    all_lines = []
    current_line_words = []
    current_line_syllables = 0
    # Increase syllable limits 3x (from 3-8 to 9-24)
    min_syllables, max_syllables = 9, 24  # Longer lines
    
    for word in sampled_words:
        word_syllables = estimate_syllables(word)
        
        # Check if adding this word would exceed max_syllables
        if (current_line_syllables + word_syllables > max_syllables) and (current_line_syllables >= min_syllables):
            # Current line has enough syllables, start a new line
            all_lines.append(current_line_words)
            current_line_words = [word]
            current_line_syllables = word_syllables
        else:
            # Add to current line
            current_line_words.append(word)
            current_line_syllables += word_syllables
    
    # Add the last line if it has any content
    if current_line_words:
        all_lines.append(current_line_words)
    
    # Create HTML with flickering effect, centered with 2-3x line spacing
    html_lines = []
    for line_index, line_words in enumerate(all_lines):
        word_elements = []
        # Alternate direction per line: even lines forward (1), odd lines reverse (-1)
        flicker_direction = 1 if line_index % 2 == 0 else -1
        
        for i, word in enumerate(line_words):
            encrypted = encrypt_word(word)
            # Start with original for forward, encrypted for reverse
            start_with_original = (flicker_direction == 1)
            initial_text = word if start_with_original else encrypted
            # Slower intervals: 2000-4000ms instead of 800-2000ms
            delay = i * 0.2  # Small stagger per word in line
            interval = random.uniform(2000, 4000)  # Slower interval between 2000-4000ms
            
            word_elements.append(
                f'<span class="flicker-word" data-original="{word}" data-encrypted="{encrypted}" '
                f'data-start-original="{str(start_with_original).lower()}" '
                f'data-direction="{flicker_direction}" '
                f'data-interval="{interval}" '
                f'style="animation-delay: {delay}s;">{initial_text}</span>'
            )
        html_lines.append('<div class="flicker-line">' + ' '.join(word_elements) + '</div>')
    
    # Reduced line spacing multiplier (0.3-0.5x) - significantly decreased but prevents overlap
    line_spacing_multiplier = random.uniform(0.3, 0.5)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flickering Text</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            min-height: 100vh;
        }}
        body {{
            font-family: monospace;
            background: #000;
            color: #fff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
        }}
        .content-container {{
            max-width: 80%;
            text-align: center;
        }}
        .flicker-line {{
            margin: {line_spacing_multiplier * 0.5}em 0;
            line-height: {max(1.0, line_spacing_multiplier * 0.8)};
            min-height: 1.2em; /* Ensure minimum height to prevent overlap */
        }}
        .flicker-word {{
            display: inline-block;
            animation: flicker 2s infinite;
            margin-right: 8px;
            font-size: 1.1em;
        }}
        @keyframes flicker {{
            0%, 50% {{
                opacity: 1;
            }}
            25%, 75% {{
                opacity: 0;
            }}
        }}
        .flicker-word::before {{
            content: attr(data-encrypted);
            position: absolute;
            opacity: 0;
            animation: flicker-encrypted 2s infinite;
        }}
        @keyframes flicker-encrypted {{
            0%, 50% {{
                opacity: 0;
            }}
            25%, 75% {{
                opacity: 1;
            }}
        }}
        .flicker-word {{
            position: relative;
        }}
        .flicker-word:hover {{
            animation-play-state: paused;
        }}
    </style>
    <script>
        // Enhanced flickering with randomized direction and timing
        document.addEventListener('DOMContentLoaded', function() {{
            const words = document.querySelectorAll('.flicker-word');
            words.forEach((word) => {{
                const original = word.getAttribute('data-original');
                const encrypted = word.getAttribute('data-encrypted');
                const startOriginal = word.getAttribute('data-start-original') === 'true';
                const direction = parseInt(word.getAttribute('data-direction'));
                const interval = parseInt(word.getAttribute('data-interval'));
                
                let showingOriginal = startOriginal;
                
                setInterval(() => {{
                    if (direction === 1) {{
                        // Forward direction: original -> encrypted -> original
                        word.textContent = showingOriginal ? encrypted : original;
                        showingOriginal = !showingOriginal;
                    }} else {{
                        // Reverse direction: encrypted -> original -> encrypted
                        word.textContent = showingOriginal ? original : encrypted;
                        showingOriginal = !showingOriginal;
                    }}
                }}, interval); // Randomized interval per word
            }});
        }});
    </script>
</head>
<body>
    <div class="content-container">
{''.join(html_lines)}
    </div>
</body>
</html>"""
    
    return html_content


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


def create_broken_sentence_text(text, percentage_to_keep):
    """
    Highly reduces text by sampling words and formats them into lines with 3-5x longer syllables.
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
    
    # Group words into lines based on syllable count with random fluctuation
    all_lines = []
    current_line_words = []
    current_line_syllables = 0
    min_syllables, max_syllables = get_random_line_syllable_limits()
    
    for word in sampled_words:
        word_syllables = estimate_syllables(word)
        
        # Check if adding this word would exceed max_syllables
        if (current_line_syllables + word_syllables > max_syllables) and (current_line_syllables >= min_syllables):
            # Current line has enough syllables, start a new line
            all_lines.append(' '.join(current_line_words))
            current_line_words = [word]
            current_line_syllables = word_syllables
            # Get new random limits for the next line
            min_syllables, max_syllables = get_random_line_syllable_limits()
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

    # Create the broken sentence text with flickering effect
    broken_text = create_broken_sentence_text_with_flicker(cleaned_text, percentage_to_keep)
    
    # Generate titled filename from the text
    title_base = generate_title_filename(cleaned_text, input_file).replace('.txt', '')
    title_filename = f"{title_base}.html"
    
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
        num_lines = len(broken_text.split('<div class="flicker-line">')) - 1
        print(f"Created: {output_file} ({num_lines} lines, {reduction_percentage:.0f}% reduction)")
        return output_file
    except Exception as e:
        print(f"An error occurred while writing the output file: {e}")
        return None


# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create broken-line texts with tight line spacing (0.3-0.5x), centered layout, and increased line count (24-30%% short, 3-6%% long retention)."
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
        help="Fixed percentage of words to keep (0.01-0.10). If not specified, uses biased random retention (30%%-3%%) based on text length."
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
        print(f"Processing {len(files_to_process)} file(s) with biased random retention (30%%-3%%)...")
    print("-" * 50)
    
    for file_path in files_to_process:
        process_file(file_path, args.output_dir, args.keep)
    
    print("-" * 50)
    print("Done!")

