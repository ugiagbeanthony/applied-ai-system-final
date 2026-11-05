"""Reliability evaluation for the hint coach.

Three parts, all offline (no API key) so results are reproducible:
  1. Predefined cases (pass/fail), including injected model failures
  2. Style comparison: plain baseline vs the constrained "coach" style
  3. Full-game simulation on every difficulty

    python evaluate.py
"""
import os
import re

os.environ.pop("ANTHROPIC_API_KEY", None)

import hint_coach  # noqa: E402
from hint_coach import get_hint, load_passages  # noqa: E402
from logic_utils import (  # noqa: E402
    ATTEMPT_LIMITS,
    check_guess,
    get_range_for_difficulty,
    narrow_range,
    parse_guess,
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


def run_cases():
    """Predefined inputs with expected behavior. Returns (passed, total)."""
    sit = {"low": 1, "high": 49, "last_outcome": "Too High", "attempts_left": 5}

    def with_model(reply):
        old = hint_coach._llm_hint

        def fake(*a, **k):
            if isinstance(reply, Exception):
                raise reply
            return reply

        hint_coach._llm_hint = fake
        try:
            return get_hint(sit, secret=30)
        finally:
            hint_coach._llm_hint = old

    cases = [
        ("parse '42'", lambda: parse_guess("42") == (True, 42, None)),
        ("parse empty input", lambda: parse_guess("")[0] is False),
        ("parse 'abc'", lambda: parse_guess("abc")[0] is False),
        ("check_guess too high", lambda: check_guess(60, 50) == "Too High"),
        ("check_guess too low", lambda: check_guess(40, 50) == "Too Low"),
        ("offline hint is the midpoint", lambda: "Try 25" in get_hint(sit, 30)[0]),
        ("clean model reply is used", lambda: with_model("Too high! Try 25.") == ("Too high! Try 25.", "ai")),
        ("model reply leaking secret is rejected", lambda: with_model("It is 30!")[1] == "local"),
        ("wordy model reply is rejected", lambda: with_model("Try 25 " + "so " * 60)[1] == "local"),
        ("model API error falls back", lambda: with_model(RuntimeError("down"))[1] == "local"),
        ("empty model reply falls back safely", lambda: with_model("")[1] == "local"),
    ]
    print("| Case | Result |")
    print("|------|--------|")
    passed = 0
    for name, fn in cases:
        try:
            ok = bool(fn())
        except Exception as exc:  # a crash is a failure, and we say so
            print(f"| {name} | Fail (crashed: {type(exc).__name__}) |")
            continue
        passed += ok
        print(f"| {name} | {'Pass' if ok else 'Fail'} |")
    print(f"\n{passed}/{len(cases)} cases passed")
    return passed, len(cases)


def style_comparison(passages):
    """Baseline (plain) vs constrained coach style over many situations."""
    sits = []
    for low, high in [(1, 100), (1, 49), (26, 49), (26, 37), (38, 49), (36, 38), (1, 20), (1, 11)]:
        for last in (None, "Too High", "Too Low"):
            for left in (1, 4, 8):
                sits.append({"low": low, "high": high, "last_outcome": last, "attempts_left": left})

    def metrics(style):
        texts = [get_hint(s, secret=s["low"], passages=passages, style=style)[0] for s in sits]
        words = [len(t.split()) for t in texts]
        short = sum(w <= 25 for w in words) / len(words)
        opener = sum(t.split("!")[0] != t and t.index("!") < 40 for t in texts) / len(texts)
        number = sum(bool(re.search(r"Try \d+", t)) for t in texts) / len(texts)
        return sum(words) / len(words), short, opener, number

    print("| Style | Avg words | Within 25 words | Encouraging opener | Names a number |")
    print("|-------|-----------|-----------------|--------------------|----------------|")
    for style, label in (("plain", "Baseline (plain)"), ("coach", "Specialized (coach)")):
        w, sh, op, nm = metrics(style)
        print(f"| {label} | {w:.1f} | {sh:.0%} | {op:.0%} | {nm:.0%} |")


def main():
    passages = load_passages()
    print("### Predefined cases\n")
    passed, total = run_cases()
    print("\n### Style comparison (offline, 72 situations)\n")
    style_comparison(passages)
    print("\n### Full-game simulation (follows the coach's suggestion)\n")
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


    return passed == total


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
