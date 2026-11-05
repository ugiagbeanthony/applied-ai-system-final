# Model Card: Game Glitch Investigator Hint Coach

**What it is:** a hint coach built into a Streamlit number-guessing game. It looks up strategy notes in `knowledge/strategy.md`, uses them to write advice for the next guess (with Claude if an API key is set, offline if not), and checks the advice before the player sees it. Setup and results are in `README.md`.

## Limitations and Biases

- **It only knows one strategy.** The knowledge base is seven short notes I wrote, all about binary search. Everything the coach says reflects that one way of playing, and it has no idea about other styles, like guessing for fun or going with a hunch.
- **Retrieval is crude.** It matches on shared words, not meaning. If a situation were described in different words it could retrieve nothing useful, and the coach would just build a hint from the current range.
- **Hard mode can't be won by skill alone.** My evaluation shows that even perfect play wins only 62% of Hard games, since 5 attempts can't cover 50 numbers. A coach can't fix that, and a player might blame themselves for it.
- **Offline hints are repetitive.** Without an API key the wording comes from a template.
- **The model path is only partly tested.** I tested the model call with mocks, not the live API, so I don't know how it behaves in practice (odd phrasing, refusals, slow responses).
- **The leak check is simple.** It only looks for the secret written as digits, so it would miss something like "the number after thirty-six".
- **Digits and English only.** Input parsing and the leak check assume ordinary digits.

## Misuse and Prevention

The stakes are low, but there are still a few ways this could go wrong.

- **Cheating.** The obvious misuse is getting the answer out of the coach. The secret is never given to the model or the offline coach, so it has nothing to leak. The guardrail also rejects any model reply that contains the secret, tries once more, and then falls back. The real hole is the Developer Debug Info panel, which shows the secret on purpose. I'd remove or hide it before anyone else uses the game.
- **API key and cost.** The key comes from an environment variable and is never stored in the repo (`.env` is in `.gitignore`). Calls have a 10-second timeout and a small token limit, so a bug can't run up a big bill.
- **Prompt injection.** The only thing a player types is a number that gets turned into an integer, and the prompt is built from my notes file and computed values, not raw player text. If I ever added free-text input I'd need to sanitize it.
- **Reusing the pattern.** The same retrieve, generate, check design could be pointed at something with real stakes. That would need a much stronger check than mine and a human reviewing the results.

## What Surprised Me During Testing

- **My own fix made things worse.** I noticed the offline hint sometimes suggested the exact secret because the midpoint of the range happened to equal it, so I made the coach avoid that number. Then I wrote `evaluate.py`, and Hard mode dropped to 0% wins. When only two numbers were left, avoiding the secret forced the coach to point at the wrong one every time. Without the measurement I would have kept it and thought it was a safety improvement.
- **The "leak" wasn't a leak.** The coach picks the midpoint without knowing the secret, so when it matches, that's a coincidence that tells the player nothing. I had treated something that looked bad as if it were bad.
- **Hard mode was the real problem.** I expected the coach to be the weak spot. The evaluation showed it wins every Easy and Normal game, and Hard is limited by the number of attempts.
- **The test harness found bugs too.** An empty model reply would have shown up as a blank hint, and a hint with one number left didn't say which number to try. Both are fixed now.

## Collaboration with AI

I used Claude Code as an assistant on this project. It wrote most of the first draft of the code, tests and diagram, and I told it what to build, ran everything, and decided what to keep.

**A suggestion I accepted:** the AI suggested making the feature a retrieval-based hint coach, where the retrieved notes actually shape the prompt, with a guardrail and an offline fallback. The other option was a separate script that prints tips next to a normal hint. I went with the coach because the assignment says the feature has to change how the system behaves, and the fallback means anyone can run it without an API key. I checked it by running the tests and reading the sample outputs to see that the advice changes with the situation. For example, "too high" pulls up a different note than the first guess does.

**A suggestion I changed:** my first fix for the offline coach suggesting the secret was the AI's idea. When the midpoint equalled the secret, it suggested a number one away instead, and it added a test for that. I accepted it at first. After the evaluation showed it broke the strategy and Hard fell to 0% wins, I undid it and deleted the test. I also changed the evaluation itself. The first version counted "hints that suggested the secret" as a failure, which was misleading, so I replaced it with win rate and guess counts.

**What I took from it:** the AI was fast and mostly right, but it was confidently wrong about the dodge fix. Measuring what the code actually did, instead of trusting that a change sounded safer, is what caught it.
