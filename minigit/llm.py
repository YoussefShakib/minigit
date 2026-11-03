import json
import os
import time
import urllib.error
import urllib.request

PROMPT = """You are resolving a git merge conflict in the file {path}.

BASE (common ancestor):
{base}

OURS:
{ours}

THEIRS:
{theirs}

Return ONLY the final merged file content that correctly combines both
changes. No explanations, no code fences, no conflict markers."""


def _text(data: bytes | None) -> str:
    return "(file does not exist)" if data is None else data.decode(errors="replace")


def build_prompt(
    path: str, base: bytes | None, ours: bytes | None, theirs: bytes | None
) -> str:
    return PROMPT.format(
        path=path, base=_text(base), ours=_text(ours), theirs=_text(theirs)
    )


def _strip_fences(text: str) -> str:
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        lines = lines[1:-1]
    return "\n".join(lines) + "\n"


def suggest_resolution(
    path: str, base: bytes | None, ours: bytes | None, theirs: bytes | None
) -> str:
    key = os.environ.get("MINIGIT_API_KEY")
    model = os.environ.get("MINIGIT_MODEL")
    base_url = os.environ.get("MINIGIT_BASE_URL", "https://api.groq.com/openai/v1")
    if not key or not model:
        raise RuntimeError("set MINIGIT_API_KEY and MINIGIT_MODEL first")

    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": build_prompt(path, base, ours, theirs)}
            ],
        }
    ).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "minigit/0.1",
        },
    )
    last_error = "unknown error"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                reply = json.load(response)
            return _strip_fences(reply["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as e:
            last_error = f"API error {e.code}: {e.read().decode()[:200]}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except urllib.error.URLError as e:
            last_error = f"network error: {e.reason}"
        except TimeoutError:
            last_error = "the API did not answer in time"
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(last_error)