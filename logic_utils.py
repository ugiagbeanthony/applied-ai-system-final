"""Core game logic for the number guessing game (no Streamlit imports)."""

ATTEMPT_LIMITS = {"Easy": 6, "Normal": 8, "Hard": 5}


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    raw = raw.strip()
    try:
        value = int(float(raw)) if "." in raw else int(raw)
    except ValueError:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """Compare guess to secret and return the outcome: "Win", "Too High" or "Too Low"."""
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def hint_message(outcome: str):
    """Short static hint for an outcome."""
    return {
        "Win": "🎉 Correct!",
        "Too High": "📉 Go LOWER!",
        "Too Low": "📈 Go HIGHER!",
    }.get(outcome, "")


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number (1-based)."""
    if outcome == "Win":
        points = max(100 - 10 * attempt_number, 10)
        return current_score + points
    if outcome in ("Too High", "Too Low"):
        return current_score - 5
    return current_score


def narrow_range(low: int, high: int, guesses):
    """
    Shrink (low, high) using past guesses.

    guesses: iterable of (guess_int, outcome) pairs.
    Returns the tightest (low, high) the secret can still be in.
    """
    for guess, outcome in guesses:
        if outcome == "Too High":
            high = min(high, guess - 1)
        elif outcome == "Too Low":
            low = max(low, guess + 1)
    return low, high
