import logging
import random

import streamlit as st

from hint_coach import get_hint
from logic_utils import (
    ATTEMPT_LIMITS,
    check_guess,
    get_range_for_difficulty,
    hint_message,
    narrow_range,
    parse_guess,
    update_score,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("game.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("game")

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("A number guessing game with an AI hint coach.")

st.sidebar.header("Settings")
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)
attempt_limit = ATTEMPT_LIMITS[difficulty]
low, high = get_range_for_difficulty(difficulty)
st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


def start_new_game():
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []  # (guess, outcome) pairs
    st.session_state.coach = None
    st.session_state.difficulty = difficulty
    logger.info("new game difficulty=%s range=%d-%d", difficulty, low, high)


# Start a game on first load, and restart when the difficulty changes.
if "secret" not in st.session_state or st.session_state.difficulty != difficulty:
    start_new_game()

st.subheader("Make a guess")
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    # st.text instead of st.write: st.write on a list imports pandas, which some
    # locked-down Windows setups block.
    st.text(f"Secret: {st.session_state.secret}")
    st.text(f"Attempts: {st.session_state.attempts}")
    st.text(f"Score: {st.session_state.score}")
    st.text(f"Difficulty: {difficulty}")
    st.text(f"History: {st.session_state.history}")

raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game()
    st.success("New game started.")
    st.rerun()

if submit and st.session_state.status == "playing":
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        logger.info("invalid input %r: %s", raw_guess, err)
        st.error(err)
    elif not (low <= guess_int <= high):
        logger.info("out of range guess %d", guess_int)
        st.error(f"Pick a number between {low} and {high}.")
    else:
        st.session_state.attempts += 1
        outcome = check_guess(guess_int, st.session_state.secret)
        st.session_state.history.append((guess_int, outcome))
        st.session_state.score = update_score(
            st.session_state.score, outcome, st.session_state.attempts
        )
        logger.info(
            "attempt=%d guess=%d outcome=%s score=%d",
            st.session_state.attempts, guess_int, outcome, st.session_state.score,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.session_state.coach = None
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.session_state.coach = None
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )
        else:
            if show_hint:
                st.warning(hint_message(outcome))
            # The AI coach decides what advice to show for the next guess.
            nlow, nhigh = narrow_range(low, high, st.session_state.history)
            situation = {
                "low": nlow,
                "high": nhigh,
                "last_outcome": outcome,
                "attempts_left": attempt_limit - st.session_state.attempts,
            }
            st.session_state.coach = get_hint(situation, st.session_state.secret)

elif st.session_state.status == "won":
    st.success("You already won. Start a new game to play again.")
elif st.session_state.status == "lost":
    st.error("Game over. Start a new game to try again.")

if show_hint and st.session_state.coach and st.session_state.status == "playing":
    text, source = st.session_state.coach
    label = "AI coach" if source.startswith("ai") else "Coach (offline)"
    st.info(f"🧠 {label}: {text}")

st.divider()
st.caption("Hints are grounded in knowledge/strategy.md and checked so they never reveal the secret.")
