"""AI hint coach: retrieval-augmented hints with guardrails and logging.

Flow (app.py uses the result as the hint the player sees):
  1. RETRIEVE  - pull the most relevant strategy passages from knowledge/strategy.md
  2. GENERATE  - ask the model for a hint grounded in those passages, or build one
                 locally from them when there is no API key or the call fails
  3. CHECK     - guardrail rejects any hint that leaks the secret number
  4. RETRY / FALLBACK - one retry, then a safe local hint
"""
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger("hint_coach")

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge" / "strategy.md"
MODEL = os.environ.get("HINT_MODEL", "claude-haiku-5-5")
MAX_HINT_CHARS = 400


def load_passages(path: Path = KNOWLEDGE_FILE):
    """Split the knowledge file into (title, text) passages."""
    passages = []
    title, lines = None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if title:
                passages.append((title, " ".join(lines).strip()))
            title, lines = line[3:].strip(), []
        elif title and line.strip():
            lines.append(line.strip())
    if title:
        passages.append((title, " ".join(lines).strip()))
    return passages


def _tokens(text: str):
    return set(re.findall(r"[a-z]+", text.lower()))


def retrieve(query: str, passages, k: int = 2):
    """Rank passages by word overlap with the query (title words count double)."""
    q = _tokens(query)
    scored = []
    for title, text in passages:
        score = len(q & _tokens(text)) + 2 * len(q & _tokens(title))
        scored.append((score, title, text))
    scored.sort(key=lambda s: -s[0])
    return [(t, x) for s, t, x in scored[:k] if s > 0]


def build_query(situation: dict) -> str:
    """Describe the game situation in words so retrieval can match it."""
    parts = []
    last = situation.get("last_outcome")
    if last == "Too High":
        parts.append("too high")
    elif last == "Too Low":
        parts.append("too low")
    else:
        parts.append("first guess")
    if situation["high"] - situation["low"] + 1 <= 5:
        parts.append("narrow range few numbers remain")
    if situation["attempts_left"] <= 2:
        parts.append("running low on attempts")
    parts.append("binary search midpoint")
    return " ".join(parts)


def leaks_secret(text: str, secret: int) -> bool:
    """Guardrail: True if the hint contains the secret as a standalone number."""
    return any(int(n) == secret for n in re.findall(r"\d+", text))


def local_hint(situation: dict, passages, secret=None) -> str:
    """Deterministic hint built from the retrieved passages and the live range."""
    low, high = situation["low"], situation["high"]
    mid = (low + high) // 2
    if mid == secret and high > low:
        # Suggesting the exact secret would give the game away; stay one off.
        mid = mid + 1 if mid < high else mid - 1
    tip = passages[0][1].split(". ")[0].rstrip(".") if passages else "Split the range in half"
    return f"The secret is between {low} and {high}. Try {mid}. Tip: {tip}."


def _llm_hint(situation: dict, passages, extra: str = ""):
    """Ask the model for a hint. Returns text, or None when no API key is set."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import anthropic

    notes = "\n".join(f"- {t}: {x}" for t, x in passages)
    prompt = (
        "You are a friendly coach for a number guessing game. Write one or two short "
        "sentences of advice for the player's next guess, using the strategy notes below.\n"
        f"Strategy notes:\n{notes}\n\n"
        f"The possible range is {situation['low']} to {situation['high']} (inclusive). "
        f"Last result: {situation.get('last_outcome') or 'none yet'}. "
        f"Attempts left: {situation['attempts_left']}.\n"
        "Suggest a specific number to try. Never state or hint at what the secret is."
        f"{extra}"
    )
    client = anthropic.Anthropic(api_key=key, timeout=10.0)
    msg = client.messages.create(
        model=MODEL, max_tokens=150, messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def get_hint(situation: dict, secret: int, passages=None):
    """Return (hint_text, source); source is 'ai', 'ai-retry' or 'local'."""
    passages = passages if passages is not None else load_passages()
    query = build_query(situation)
    retrieved = retrieve(query, passages)
    logger.info("query=%r retrieved=%s", query, [t for t, _ in retrieved])

    extra = ""
    for attempt in range(2):
        try:
            text = _llm_hint(situation, retrieved, extra)
        except Exception as exc:  # network, auth, rate limit
            logger.warning("model call failed: %s", exc)
            break
        if text is None:
            logger.info("no API key set; using local hint")
            break
        if len(text) > MAX_HINT_CHARS:
            logger.warning("hint rejected: too long (%d chars)", len(text))
        elif leaks_secret(text, secret):
            logger.warning("hint rejected: leaked the secret")
            extra = "\nYour last answer revealed the secret. Do not mention it at all."
        else:
            return text, "ai" if attempt == 0 else "ai-retry"

    return local_hint(situation, retrieved, secret), "local"
