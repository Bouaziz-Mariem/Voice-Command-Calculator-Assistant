"""
NLP Parser Module
Converts natural language math phrases into evaluable expression strings.

Pipeline:  raw text → strip fillers → replace operations → convert word-numbers → expression string

Example:   "what is twenty three times forty seven"  →  "23 * 47"
"""

# ---------------------------------------------------------------------------
# Filler phrases to strip (matched longest-first to avoid partial hits)
# ---------------------------------------------------------------------------
FILLER_PATTERNS = [
    "what is the", "what's the", "how much is",
    "what is", "what's", "calculate", "compute",
    "tell me", "solve", "evaluate",
]

# ---------------------------------------------------------------------------
# Operation word → symbol mapping
# Multi-word entries MUST come before single-word ones so they match first.
# ---------------------------------------------------------------------------
OPERATIONS = {
    # multi-word (order matters — longest first)
    "multiplied by": " * ",
    "divided by":    " / ",
    "added to":      " + ",
    "to the power of": " ** ",
    "square root of": " sqrt ",
    "open parenthesis":  " ( ",
    "close parenthesis": " ) ",
    # single-word
    "plus":     " + ",
    "add":      " + ",
    "minus":    " - ",
    "subtract": " - ",
    "less":     " - ",
    "times":    " * ",
    "over":     " / ",
    "power":    " ** ",
    "squared":  " **2 ",
    "cubed":    " **3 ",
    "percent":  " percent ",
    "negative": " negative ",
    "point":    " point ",
}

# ---------------------------------------------------------------------------
# Number-word dictionaries
# ---------------------------------------------------------------------------
ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}

TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

MAGNITUDES = {"hundred": 100, "thousand": 1000, "million": 1_000_000}

# All words that are part of a number (used to detect number-group boundaries)
NUMBER_WORDS = set(ONES) | set(TENS) | set(MAGNITUDES)


# ---------------------------------------------------------------------------
# Step 1: Strip filler / trigger phrases
# ---------------------------------------------------------------------------
def strip_fillers(text: str) -> str:
    for filler in FILLER_PATTERNS:
        text = text.replace(filler, "")
    # collapse whitespace
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Step 2: Replace operation words with symbols
# Multi-word replacements happen first (dict is ordered in Python 3.7+).
# ---------------------------------------------------------------------------
def replace_operations(text: str) -> str:
    for word, symbol in OPERATIONS.items():
        text = text.replace(word, symbol)
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Step 3: Convert a sequence of number-words into a single integer/float
#
#   "two thousand three hundred forty five"  →  2345
#
# Algorithm:
#   Walk tokens left-to-right, accumulating into `group`.
#   - ONES/TENS  → group += value
#   - "hundred"  → group *= 100
#   - "thousand"/"million" → total += group * magnitude, group resets to 0
#   At the end: total += group
# ---------------------------------------------------------------------------
def words_to_number(words: list[str]) -> int | float:
    total = 0
    group = 0

    i = 0
    while i < len(words):
        w = words[i]

        if w in ONES:
            group += ONES[w]
        elif w in TENS:
            group += TENS[w]
        elif w == "hundred":
            group = (group if group else 1) * 100
        elif w in ("thousand", "million"):
            group = (group if group else 1) * MAGNITUDES[w]
            total += group
            group = 0
        elif w == "point":
            # Decimal: collect digits after "point"
            # e.g. ["five", "point", "three"] → 5.3
            decimal_str = ""
            i += 1
            while i < len(words) and words[i] in ONES:
                decimal_str += str(ONES[words[i]])
                i += 1
            result = total + group
            if decimal_str:
                result = float(f"{result}.{decimal_str}")
            return result
        i += 1

    return total + group


# ---------------------------------------------------------------------------
# Step 4: Walk all tokens, group consecutive number-words, convert them,
#          and pass non-number tokens (operators, functions) through.
# ---------------------------------------------------------------------------
def words_to_expression(tokens: list[str]) -> str:
    parts = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Handle "negative" → prepend minus to the next number
        if token == "negative":
            # Collect the number words that follow
            i += 1
            num_words = []
            while i < len(tokens) and (tokens[i] in NUMBER_WORDS or tokens[i] == "point"):
                num_words.append(tokens[i])
                i += 1
            if num_words:
                parts.append(str(-words_to_number(num_words)))
            else:
                parts.append("-")
            continue

        # Handle "sqrt" → sqrt( number )
        if token == "sqrt":
            i += 1
            num_words = []
            while i < len(tokens) and (tokens[i] in NUMBER_WORDS or tokens[i] == "point"):
                num_words.append(tokens[i])
                i += 1
            if num_words:
                parts.append(f"sqrt({words_to_number(num_words)})")
            else:
                parts.append("sqrt(")
            continue

        # Handle "percent" + "of"  →  e.g. "5 percent of 200" → "0.05 * 200"
        if token == "percent":
            # The number before "percent" is already in parts
            if parts:
                prev_num = float(parts.pop())
                parts.append(str(prev_num / 100))
            # skip optional "of"
            if i + 1 < len(tokens) and tokens[i + 1] == "of":
                i += 1
            parts.append("*")
            i += 1
            continue

        # Collect a group of consecutive number-words
        if token in NUMBER_WORDS or token == "point":
            num_words = []
            while i < len(tokens) and (tokens[i] in NUMBER_WORDS or tokens[i] == "point"):
                num_words.append(tokens[i])
                i += 1
            number = words_to_number(num_words)
            # Format: int if whole, otherwise float
            if isinstance(number, float):
                parts.append(str(number))
            else:
                parts.append(str(int(number)))
            continue

        # Everything else passes through (operators: +, -, *, /, **, (, ), **2, **3)
        parts.append(token)
        i += 1

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def parse(text: str) -> str:
    """
    Convert a spoken math phrase into an evaluable expression string.

    Examples:
        "what is twenty three times forty seven"  →  "23 * 47"
        "square root of one forty four"           →  "sqrt(144)"
        "negative five plus three"                →  "-5 + 3"
    """
    text = text.lower().strip()
    text = strip_fillers(text)
    text = replace_operations(text)
    tokens = text.split()
    expression = words_to_expression(tokens)
    return expression
