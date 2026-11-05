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
5. **Evaluator / guardrail:** a model hint that contains the secret number or is too long is rejected. The coach retries once, then falls back to a safe offline hint.
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

Real outputs from the offline coach (secret = 37). Each row shows the plain baseline and the specialized coach style the app uses.

| Situation | Baseline (plain) | Specialized (coach) |
|-----------|------------------|---------------------|
| First turn, range 1-100 | The secret is between 1 and 100. Try 50. Tip: Always guess the midpoint of the range that is still possible. | Great start! Try 50: it splits 1-100 in half. |
| Guessed 50, Too High, range 1-49 | The secret is between 1 and 49. Try 25. Tip: When a guess is too high, the secret is lower. | Too high, but you're closing in! Try 25: it splits 1-49 in half. |
| Guessed 25, Too Low, range 26-49, 2 attempts left | The secret is between 26 and 49. Try 37. Tip: With one or two attempts left, pick the number that splits the remaining range most evenly... | Too low, keep climbing! Try 37: it splits 26-49 in half. |

The secret is never passed to the model or the offline coach, so a suggestion that happens to equal it (as in the last row) is a lucky midpoint, not a leak. With an API key, the model writes the advice in its own words from the retrieved notes, and the guardrail checks it.

**Specialized style:** the coach style constrains tone and format (at most 25 words, an encouraging opener, one concrete number and a reason). With an API key, the prompt teaches this with three few-shot examples (`FEW_SHOT` in `hint_coach.py`) plus style rules, and the guardrail rejects replies over 30 words. Offline, the same style is produced by a template. Results against the baseline are in the Testing Summary.

## Design Decisions

- **Retrieval over a plain prompt:** hints come from a small notes file, so the advice is grounded and the file can be edited without touching code.
- **Simple keyword retrieval, not embeddings:** the corpus has seven short passages. Word-overlap ranking is transparent, needs no extra dependency, and is easy to test. The trade-off is that it won't scale to a large or loosely worded corpus.
- **Offline fallback:** the app must run for anyone who clones it, with no key and no network. The trade-off is that offline hints are more templated than model hints.
- **Guardrail after generation:** the model is told not to reveal the secret, but the code enforces it. A prompt is a request, a check is a guarantee. The trade-off is a possible extra API call on a retry.
- **Logic separated from the UI:** `logic_utils.py` has no Streamlit imports so it can be unit tested directly.

## Testing Summary

**Automated tests:** 17 of 17 `pytest` tests pass (`python -m pytest`). They cover the game rules and the coach, including a leaking, wordy or empty model reply being rejected, a retry that recovers, and a model error falling back safely.

**Test harness:** `python evaluate.py` runs the system on predefined inputs and prints three tables, then exits non-zero if any case fails. It runs offline, so results are reproducible.

Predefined cases: **11/11 passed**, including injected model failures (leaking reply, wordy reply, API error, empty reply).

**Specialized style vs baseline** (72 situations, offline):

| Style | Avg words | Within 25 words | Encouraging opener | Names a number |
|-------|-----------|-----------------|--------------------|----------------|
| Baseline (plain) | 25.6 | 67% | 0% | 100% |
| Specialized (coach) | 11.0 | 100% | 100% | 100% |

These measure compliance with the style rules I defined, so they show the style is applied consistently, not that players prefer it. The harness also found two bugs while I built it: a one-number-left hint that gave no number to try, and an empty model reply that would have been shown as a blank hint. Both are fixed and tested.

**Full-game simulation** (follows the coach's suggested number):

**Reliability evaluation:** `python evaluate.py` plays every possible secret on every difficulty, always following the coach's suggested number, offline so it is reproducible.

| Difficulty | Attempts allowed | Games | Win rate | Avg guesses (wins) | Max guesses (wins) |
|------------|------------------|-------|----------|--------------------|--------------------|
| Easy | 6 | 20 | 100% | 3.70 | 5 |
| Normal | 8 | 100 | 100% | 5.80 | 7 |
| Hard | 5 | 50 | 62% | 4.16 | 5 |

**Logging and error handling:** `game.log` records every guess, retrieval query, rejected hint and API failure. Model errors are caught and the game continues with the offline hint.

**What I learned**
- Following the coach wins every Easy and Normal game, so the advice is sound. Hard is only 62% because five guesses can cover at most 31 of 50 numbers even with perfect play. That is a game-balance problem, not a coach problem, and the evaluation is what showed it.
- My first fix for the coach was wrong. I made the offline hint avoid suggesting the secret, and the evaluation showed it broke the strategy and dropped Hard to 0%. I reverted it, because the suggestion is computed without knowing the secret and so reveals nothing.
- Not verified: the real model call has only been tested with mocks, and the Streamlit UI hasn't been exercised in an automated test on this machine.

## Reflection

Building this showed me that an AI feature is mostly the engineering around the model: deciding what it sees, checking what it says, and defining what happens when it fails. The model call is a few lines, while retrieval, validation, logging and fallbacks are most of the work. The responsible-AI reflection is in `model_card.md`.
