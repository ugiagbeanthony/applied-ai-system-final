# 🎮 Game Glitch Investigator: AI Hint Coach

**Original project:** *Game Glitch Investigator: The Impossible Guesser* (Modules 1-3). The original was a Streamlit number-guessing game that shipped with deliberate bugs: backwards hints, a secret number that changed on every click, and broken scoring. Its goal was to find those bugs, fix them, move the logic into `logic_utils.py`, and cover it with `pytest`.

## Summary

This project extends the repaired game with an **AI hint coach**. After each wrong guess, the coach looks up relevant strategy notes (retrieval), uses them to write advice for the next guess, and checks that advice before showing it, so it never reveals the secret number. It matters because it shows a pattern that applies well beyond games: ground an AI's output in retrieved information, then verify it before a user sees it. It also keeps working when the AI is unavailable.

## Architecture Overview

The full diagram is in [`diagrams/architecture.mmd`](diagrams/architecture.mmd) (image in [`assets/`](assets/)).

1. **Input:** the player types a guess into the Streamlit app (`app.py`).
2. **Game logic** (`logic_utils.py`): the guess is parsed, checked against the secret, and scored. The range of numbers still possible is narrowed.
3. **Retriever** (`hint_coach.py`): the situation (last result, remaining range, attempts left) becomes a query that is matched against passages in `knowledge/strategy.md`.
4. **Generator:** the top passages and the live range go into a model prompt (Claude). With no API key, the hint is built offline from the same passages.
5. **Evaluator / guardrail:** a hint that contains the secret number or is too long is rejected. The coach retries once, then falls back to a safe offline hint.
6. **Output:** the approved hint is displayed with the result.
7. **Checks:** `pytest` verifies the logic, retrieval, guardrail, retry and fallback. `game.log` records every guess, retrieval, rejection and error. The player is the human check on whether hints are useful.

## Setup Instructions

```
git clone https://github.com/ugiagbeanthony/applied-ai-system-final.git
cd applied-ai-system-final
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS / Linux / Git Bash: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

- **Optional model hints:** set `ANTHROPIC_API_KEY` before launching (PowerShell: `$env:ANTHROPIC_API_KEY="..."`). Without it the app runs fully offline. Override the model with `HINT_MODEL`.
- **Run tests:** `python -m pytest`
- **Logs:** written to `game.log` in the project folder.

## Sample Interactions

These are real outputs from the offline coach (secret = 37).

| Situation | Coach output |
|-----------|--------------|
| First turn, range 1-100 | *The secret is between 1 and 100. Try 50. Tip: Always guess the midpoint of the range that is still possible.* |
| Guessed 50 → Too High, range now 1-49 | *The secret is between 1 and 49. Try 25. Tip: When a guess is too high, the secret is lower.* |
| Guessed 25 → Too Low, range now 26-49, 2 attempts left | *The secret is between 26 and 49. Try 38. Tip: With one or two attempts left, pick the number that splits the remaining range most evenly...* |

Notice how the retrieved tip changes with the situation, and how the last row suggests 38 instead of the exact midpoint, 37, because 37 is the secret and suggesting it would give the game away. With an API key, the model writes this advice in its own words from the same passages and the guardrail checks it.

## Design Decisions

- **Retrieval over a plain prompt:** hints come from a small notes file, so the advice is grounded and the file can be edited without touching code.
- **Simple keyword retrieval, not embeddings:** the corpus has seven short passages. Word-overlap ranking is transparent, needs no extra dependency, and is easy to test. The trade-off is that it won't scale to a large or loosely worded corpus.
- **Offline fallback:** the app must run for anyone who clones it, with no key and no network. The trade-off is that offline hints are more templated than model hints.
- **Guardrail after generation:** the model is told not to reveal the secret, but the code enforces it. A prompt is a request, a check is a guarantee. The trade-off is a possible extra API call on a retry.
- **Logic separated from the UI:** `logic_utils.py` has no Streamlit imports so it can be unit tested directly.

## Testing Summary

- **What worked:** 15 `pytest` tests pass. They cover the game rules and the coach, including a leaking model reply being rejected, a retry that recovers, and a model error falling back safely.
- **What didn't, at first:** writing sample outputs showed that the offline hint could recommend the exact secret whenever the midpoint of the range equalled it. The guardrail only covered model output, so I fixed the offline path and added a test.
- **Not verified:** the real model call has only been tested with mocks. The Streamlit UI also hasn't been exercised in an automated test on this machine.
- **Learned:** checking every output path, not just the obvious one, finds real bugs. The offline path was a second place the secret could leak.

## Reflection

Building this showed me that an AI feature is mostly the engineering around the model: deciding what it sees, checking what it says, and defining what happens when it fails. The model call is a few lines, while retrieval, validation, logging and fallbacks are most of the work. The responsible-AI reflection is in `model_card.md`.
