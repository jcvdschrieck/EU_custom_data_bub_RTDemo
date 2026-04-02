"""
Subprocess bridge to the vat_fraud_detection analyser.

Runs _analyse_tx.py inside the vat_fraud_detection project directory as an
isolated subprocess so the two projects' `lib` packages do not conflict.

Returns:
    {"verdict": "correct"|"incorrect"|"uncertain", "reasoning": str, "success": bool}
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Absolute path to the vat_fraud_detection project root
_VFD_DIR = Path(__file__).parent.parent.parent / "vat_fraud_detection"
_SCRIPT  = _VFD_DIR / "_analyse_tx.py"


def analyse_transaction_sync(tx: dict) -> dict:
    """
    Run the VAT fraud detection analyser on a single transaction dict.
    Blocking — call from a thread pool when used inside asyncio.
    """
    try:
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            input=json.dumps(tx),
            capture_output=True,
            text=True,
            cwd=str(_VFD_DIR),
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
