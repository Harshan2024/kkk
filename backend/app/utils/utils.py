def calculate_levenshtein(s1: str, s2: str) -> int:
    """
    Computes the edit distance between two strings s1 and s2.
    """
    if len(s1) < len(s2):
        return calculate_levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def get_spelling_suggestions(word: str, choices: list[str], max_suggestions: int = 3, threshold: int = 3) -> list[str]:
    """
    Scans a list of choices and returns candidates within an edit distance threshold.
    """
    word_clean = word.lower().strip()
    suggestions = []
    
    for choice in choices:
        choice_clean = choice.lower().strip()
        
        # Substring or contains
        if choice_clean in word_clean or word_clean in choice_clean:
            suggestions.append((0, choice))
            continue
            
        dist = calculate_levenshtein(word_clean, choice_clean)
        if dist <= threshold:
            suggestions.append((dist, choice))
            
    # Sort suggestions by distance (closest first)
    suggestions.sort(key=lambda x: x[0])
    
    # Return raw strings of top choices
    return [s[1] for s in suggestions[:max_suggestions]]
