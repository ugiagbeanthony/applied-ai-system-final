import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hint_coach
from hint_coach import build_query, get_hint, leaks_secret, load_passages, retrieve
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    narrow_range,
    parse_guess,
    update_score,
)


def test_winning_guess():
    assert check_guess(50, 50) == "Win"


def test_guess_too_high():
    assert check_guess(60, 50) == "Too High"


def test_guess_too_low():
    assert check_guess(40, 50) == "Too Low"


def test_ranges():
    assert get_range_for_difficulty("Easy") == (1, 20)
    assert get_range_for_difficulty("Hard") == (1, 50)


def test_parse_guess():
    assert parse_guess("42") == (True, 42, None)
    assert parse_guess(" 7 ")[1] == 7
    assert parse_guess("")[0] is False
    assert parse_guess("abc")[0] is False
    assert parse_guess(None)[0] is False


def test_score():
    assert update_score(0, "Win", 1) == 90
    assert update_score(0, "Win", 20) == 10
    assert update_score(20, "Too High", 1) == 15
    assert update_score(20, "Too Low", 2) == 15


def test_narrow_range():
    assert narrow_range(1, 100, [(50, "Too High"), (25, "Too Low")]) == (26, 49)


# --- hint coach: retrieval, guardrail, fallback -------------------------------

SITUATION = {"low": 1, "high": 49, "last_outcome": "Too High", "attempts_left": 5}


def test_retrieval_matches_situation():
    passages = load_passages()
    titles = [t for t, _ in retrieve(build_query(SITUATION), passages)]
    assert "too high" in titles


def test_guardrail_detects_leak():
    assert leaks_secret("It is 37!", 37)
    assert not leaks_secret("Try 25 next.", 37)
    assert not leaks_secret("Try 137 next.", 37)


def test_local_hint_uses_range_and_never_leaks(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text, source = get_hint(SITUATION, secret=30)
    assert source == "local"
    assert "between 1 and 49" in text and "Try 25" in text


def test_leaky_model_output_is_rejected(monkeypatch, caplog):
    monkeypatch.setattr(hint_coach, "_llm_hint", lambda *a, **k: "The answer is 30.")
    with caplog.at_level(logging.WARNING, logger="hint_coach"):
        text, source = get_hint(SITUATION, secret=30)
    assert source == "local"
    assert not leaks_secret(text, 30)
    assert "leaked the secret" in caplog.text


def test_clean_model_output_is_used(monkeypatch):
    monkeypatch.setattr(hint_coach, "_llm_hint", lambda *a, **k: "Try 25.")
    assert get_hint(SITUATION, secret=30) == ("Try 25.", "ai")


def test_retry_recovers_after_leak(monkeypatch):
    replies = iter(["It is 30", "Try 25."])
    monkeypatch.setattr(hint_coach, "_llm_hint", lambda *a, **k: next(replies))
    assert get_hint(SITUATION, secret=30) == ("Try 25.", "ai-retry")


def test_model_error_falls_back(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(hint_coach, "_llm_hint", boom)
    assert get_hint(SITUATION, secret=30)[1] == "local"

