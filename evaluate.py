"""Reliability evaluation for the hint coach.

Plays every possible secret on every difficulty, always following the coach's
suggested number, and reports measurable results as a markdown table.
Runs offline (no API key) so results are reproducible:

    python evaluate.py
"""
import os
import re

os.environ.pop("ANTHROPIC_API_KEY", None)

from hint_coach import get_hint, load_passages  # noqa: E402
from logic_utils import (  # noqa: E402
    ATTEMPT_LIMITS,
    check_guess,
    get_range_for_difficulty,
    narrow_range,
)


def play(secret, difficulty, passages):
    """Follow the coach until win or out of attempts. Returns a result dict."""
    low, high = get_range_for_difficulty(difficulty)
    limit = ATTEMPT_LIMITS[difficulty]
    history, last = [], None
    for attempt in range(1, limit + 1):
        nlow, nhigh = narrow_range(low, high, history)
        situation = {
            "low": nlow,
            "high": nhigh,
            "last_outcome": last,
            "attempts_left": limit - attempt + 1,
        }
        text, _ = get_hint(situation, secret, passages)
        guess = int(re.search(r"Try (\d+)", text).group(1))
        last = check_guess(guess, secret)
        history.append((guess, last))
        if last == "Win":
            return {"won": True, "attempts": attempt}
    return {"won": False, "attempts": limit}


def main():
    passages = load_passages()
    print("| Difficulty | Attempts allowed | Games | Win rate | Avg guesses (wins) | Max guesses (wins) |")
    print("|------------|------------------|-------|----------|--------------------|--------------------|")
    for difficulty in ("Easy", "Normal", "Hard"):
        low, high = get_range_for_difficulty(difficulty)
        results = [play(s, difficulty, passages) for s in range(low, high + 1)]
        wins = [r for r in results if r["won"]]
        avg = sum(r["attempts"] for r in wins) / len(wins) if wins else 0
        worst = max((r["attempts"] for r in wins), default=0)
        print(
            f"| {difficulty} | {ATTEMPT_LIMITS[difficulty]} | {len(results)} "
            f"| {len(wins) / len(results):.0%} | {avg:.2f} | {worst} |"
        )


if __name__ == "__main__":
    main()
