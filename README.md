# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # macOS/Linux/Git Bash: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
python -m pytest
```

Optional: set `ANTHROPIC_API_KEY` to get model-written hints. Without it the coach builds hints offline from the same retrieved notes, so the app runs either way. Activity is logged to `game.log`.

## 🤖 AI Feature: Hint Coach (RAG + guardrails)

After each wrong guess the coach decides what advice the player sees:

1. **Retrieve**: the game situation (last result, remaining range, attempts left) is turned into a query and matched against `knowledge/strategy.md`.
2. **Generate**: the retrieved notes plus the live range go into the model prompt, so the hint depends on them. Offline, the hint is built directly from the retrieved note and the narrowed range.
3. **Check**: a guardrail rejects any hint that contains the secret number or is too long.
4. **Retry / fall back**: one retry, then a safe local hint. API errors are caught and logged.

See `diagrams/architecture.mmd` (PNG in `assets/`) and `hint_coach.py`. Tests for retrieval, the guardrail, retry and fallback are in `tests/test_game_logic.py`.

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose.
- [ ] Detail which bugs you found.
- [ ] Explain what fixes you applied.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
# Paste your pytest output here, e.g.:
# pytest tests/
# ========================= X passed in 0.XXs =========================
```

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
