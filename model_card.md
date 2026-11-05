# Model Card: Game Glitch Investigator Hint Coach

**What it is:** a retrieval-augmented hint coach inside a Streamlit number-guessing game. It retrieves strategy notes from `knowledge/strategy.md`, uses them to write advice for the next guess (with Claude when an API key is set, offline otherwise), and checks the advice before showing it. See `README.md` for setup and results.

## Limitations and Biases

- **Narrow scope:** the knowledge base is seven short notes that I wrote, all about binary search. The coach can only give advice that reflects that one strategy, so it has the bias of whoever wrote the notes. It has no notion of other play styles, such as guessing for fun or testing a hunch.
- **Crude retrieval:** matching is word overlap, not meaning. A situation described with different wording would retrieve nothing relevant, and the coach would still produce a hint from the live range alone.
- **Hard mode is not winnable by skill:** my evaluation shows that even perfect play wins only 62% of Hard games (5 attempts for 50 numbers). A hint coach cannot fix a game-balance problem, and a player might wrongly blame themselves.
- **Offline hints are templated:** without an API key the wording is repetitive, and the tip appended to the hint can be longer than the advice itself.
- **Model path is only partly verified:** I tested the model call with mocks, not against the live API, so real-world behavior (odd phrasing, refusals, slow responses) is unmeasured. The leak check is a simple "does the secret appear as a number" test and would miss a hint like "it's the number after thirty-six".
- **English and digits only:** input parsing and the leak check assume ordinary digits.

## Misuse and Prevention

The stakes here are low, but there are still a few ways it could go wrong:

- **Cheating:** the obvious misuse is getting the answer from the coach. The secret is never passed to the model or the offline coach, so it cannot be told what the answer is. The guardrail also rejects any model reply that contains the secret, with one retry and then a safe fallback. The remaining way to "cheat" is the Developer Debug Info panel, which shows the secret on purpose for debugging. It should be removed or hidden before real use.
- **API key and cost:** the key is read from an environment variable, never stored in the repo (`.env` is in `.gitignore`), and calls have a 10-second timeout and a small token limit so a loop cannot run up a large bill.
- **Prompt injection:** the only user text is a number that gets parsed to an integer, and the model prompt is built from the notes file and computed values, not raw user text. That keeps this risk small. If free-text input were ever added, it would need its own sanitizing.
- **Reuse of the pattern:** the same retrieve, generate, check design could be pointed at higher-stakes topics. Anyone doing that would need a much stronger evaluator than a leak check, and a human review step.

## What Surprised Me While Testing Reliability

- **My own fix made things worse.** I noticed that the offline hint sometimes suggested the exact secret, because the midpoint of the remaining range equalled it, so I made the coach dodge that number. When I built `evaluate.py` and ran it, Hard mode dropped to 0% wins. In a two-number range, dodging forced the coach to point at the wrong number every time. Without the measurement I would have shipped it and believed it was a safety improvement.
- **The "leak" was not a leak.** The coach computes the midpoint without knowing the secret, so a suggestion that matches the secret is a coincidence that carries no information. I had been treating a correct-looking symptom as a real problem.
- **Hard mode was the real bug.** I expected the coach to be the weak point. Instead the evaluation showed it wins every Easy and Normal game and that Hard is limited by the number of attempts.

## Collaboration with AI

I used Claude Code as an assistant for this project: it wrote most of the first draft of the code, tests, diagram and documentation, and I directed it, ran things and decided what to keep.

**A suggestion I accepted:** the AI proposed making the feature a retrieval-augmented hint coach where the retrieved notes actually shape the prompt, with a guardrail and an offline fallback, instead of a standalone script that prints tips next to a normal hint. I accepted it because the assignment requires the feature to change how the system behaves, and because the fallback means the project runs for anyone without an API key. I checked it by running the 14 tests and by reading the sample outputs to see that the tip changes with the situation (for example "too high" retrieves a different note from the first guess).

**A suggestion I changed:** the AI's first fix for the offline coach suggesting the secret was to make it suggest one number away from the midpoint whenever the midpoint equalled the secret, and it added a test for it. I accepted that at first, then rejected it after the evaluation showed it broke the strategy (Hard fell to 0% wins). I reverted it, removed the test, and rewrote the README to explain that the midpoint is computed without the secret. I also changed the evaluation itself: its first version counted "hints that suggested the secret" as a failure metric, which was misleading, so I replaced it with win rate and guess counts.

**What I took from it:** the AI was fast and mostly right, but it was confidently wrong about the dodge fix. Measuring the behavior, rather than trusting that a change sounded safer, is what caught it.
