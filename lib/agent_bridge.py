"""
Subprocess bridge to the vat_fraud_detection analyser.

Runs _analyse_tx.py inside the vat_fraud_detection project directory as an
isolated subprocess so the two projects' `lib` packages do not conflict.

Environment variables are resolved in this priority order:
  1. Already set in the parent process (e.g. exported before running uvicorn)
  2. vat_fraud_detection/.env  (auto-loaded if present)

Returns:
    {"verdict": "correct"|"incorrect"|"uncertain", "reasoning": str, "success": bool}
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Path to the vat_fraud_detection git submodule (lives inside this project)
_VFD_DIR = Path(__file__).parent.parent / "vat_fraud_detection"
_SCRIPT  = _VFD_DIR / "_analyse_tx.py"


def _load_dotenv(env_path: Path) -> dict[str, str]:
    """
    Parse a .env file and return its key=value pairs.
    Skips blank lines and comments.  Strips inline comments and quotes.
    Does NOT override values already present in os.environ.
    """
    result: dict[str, str] = {}
    if not env_path.is_file():
        return result
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, rest = line.partition("=")
        key = key.strip()
        # Strip inline comment (but not inside URL strings like ://)
        value = rest.split(" #")[0].split("\t#")[0].strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def analyse_transaction_sync(tx: dict) -> dict:
    """
    Run the VAT fraud detection analyser on a single transaction dict.
    Blocking — call from a thread pool when used inside asyncio.
    """
    # Build subprocess environment: start from current env, then layer .env
    # on top for any keys not already set.
    env = dict(os.environ)
    dotenv_vals = _load_dotenv(_VFD_DIR / ".env")
    for k, v in dotenv_vals.items():
        env.setdefault(k, v)   # parent-process vars take priority

    try:
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            input=json.dumps(tx),
            capture_output=True,
            text=True,
            cwd=str(_VFD_DIR),
            env=env,
            timeout=90,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {
                "verdict":   "uncertain",
                "reasoning": f"Subprocess error (rc={result.returncode}): {result.stderr[:500]}",
                "success":   False,
            }
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return {
            "verdict":   "uncertain",
            "reasoning": "Agent timed out after 90 seconds.",
            "success":   False,
        }
    except Exception as e:
        return {
            "verdict":   "uncertain",
            "reasoning": f"Bridge error: {e}",
            "success":   False,
        }
