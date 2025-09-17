import re
from typing import Tuple, List


def prompt_determine_fences(prompt: str) -> Tuple[str, str]:
    """
    Determines a suitable fence and its description for a given prompt string.

    The function identifies a fence pattern that is not present in the prompt_string
    to avoid conflicts. A fence pattern is a sequence of N identical delimiter
    symbols.

    The logic is as follows:
    1. Define a set of delimiter symbols and their English descriptions.
    2. For each symbol, find the longest consecutive sequence of that symbol in the prompt string.
    3. The new fence for that symbol will be one character longer than the longest sequence found.
    4. This guarantees the fence does not exist in the prompt string.
    5. Out of the potential fences for each delimiter symbol, we choose the shortest one.
       This is typically a 3-character fence if the delimiter symbol is not used
       consecutively in the prompt.

    Args:
        prompt_string: The string which may contain complex combinations of symbols for fencing.

    Returns:
        A tuple containing:
        - fence (str): The fence string, e.g., "---", "#####".
        - fence_description (str): A description of the fence, e.g., "delimited by 3 hyphens".
    """
    delimiter_map = {"#": "sharps", "`": "backticks", "~": "tildes", "-": "hyphens"}

    candidate_fences = []

    for symbol, description in delimiter_map.items():
        # Find all occurrences of one or more consecutive symbols
        sequences = re.findall(f"({re.escape(symbol)}+)", prompt)
        if sequences:
            max_len = max(len(seq) for seq in sequences)
            fence_len = max_len + 3
        else:
            fence_len = 3

        fence = symbol * fence_len
        fence_description = f"delimited by {fence_len} {description}"
        candidate_fences.append((fence, fence_description, fence_len))

    # Return the shortest valid fence
    best_fence = min(candidate_fences, key=lambda x: x[2])

    return best_fence[0], best_fence[1]



def prompt_join_with_and(items: List[str], default: str = "") -> str:
    """
    Join a list of items using proper English grammar with commas and "and".
    
    This function handles the standard English pattern:
    - 1 item: "A"
    - 2 items: "A and B" 
    - 3+ items: "A, B, and C"

    Args:
        items: List of strings to join
        default: Default value to return if the list is empty

    Returns:
        Properly formatted string with items joined by commas and "and",
        or the default value if the list is empty
    """
    if not items:
        return default

    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", and {items[-1]}"


def prompt_tones(tones: List[str]) -> str:
    """
    Get formatted tone string from a list of tones.
    
    This is a convenience function that uses join_with_and with "neutral" as default.

    Args:
        tones: List of tone strings

    Returns:
        Properly formatted tone string, or "neutral" if no tones provided
    """
    return prompt_join_with_and(tones, default="neutral")
