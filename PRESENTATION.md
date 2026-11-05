# Presentation Outline (5-7 minutes)

**1. The problem and the starting point (45s)**
- Original project: Game Glitch Investigator, a deliberately broken number-guessing game I debugged and tested.
- Goal now: add an AI feature that is useful, grounded and safe.

**2. The system (90s)**: walk through `diagrams/architecture.mmd`
- Input: player's guess. Game logic narrows the remaining range.
- Retriever: matches the situation to notes in `knowledge/strategy.md`.
- Generator: model (or offline template) writes a short hint in a constrained coach style, taught by few-shot examples.
- Evaluator: rejects replies that leak the secret, are too long or are empty. One retry, then a safe fallback.

**3. Live demo (90s)**
- `python -m streamlit run app.py`: play a game on Normal, show the coach hint change after each guess.
- Show `game.log` filling with guesses, retrieval queries and rejections.
- Optional: set `ANTHROPIC_API_KEY` and show a model-written hint.

**4. Proof it works (90s)**
- `python evaluate.py`: 11/11 predefined cases, style comparison (25.6 to 11.0 average words, 0% to 100% encouraging opener), full-game win rates (Easy 100%, Normal 100%, Hard 62%).
- `python -m pytest`: 17 passed.

**5. What I learned (60s)**
- My first fix (dodging the secret) dropped Hard to 0% wins. Only the evaluation caught it.
- Hard's 62% is a game-balance limit (5 guesses cover at most 31 of 50 numbers), not a coach flaw.
- The harness also found an empty-reply bug and a missing-number bug.

**6. Limits and next steps (30s)**
- Keyword retrieval, one strategy, model call tested only with mocks. Next: live-API evaluation and more varied notes.
