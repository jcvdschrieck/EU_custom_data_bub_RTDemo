"""Shared configuration."""
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EUROPEAN_CUSTOM_DB = DATA_DIR / "european_custom.db"
SIMULATION_DB      = DATA_DIR / "simulation.db"

API_PORT     = 8505
API_BASE_URL = f"http://localhost:{API_PORT}"

# Simulation time window
SIM_START_STR = "2026-03-01T00:00:00"
SIM_END_STR   = "2026-03-31T23:59:59"
SIM_START_DT  = datetime.fromisoformat(SIM_START_STR).replace(tzinfo=timezone.utc)
SIM_END_DT    = datetime.fromisoformat(SIM_END_STR).replace(tzinfo=timezone.utc)

# Speed: simulated minutes that advance per real second.
# The UI exposes three user-facing multipliers that map onto this unit so that
# ×1 plays the full active replay (March 2026, 44 640 sim-min) in ~15 real
# minutes — the intended default horizon:
#   ×1   → 50   sim-min/real-sec → full March in ~15 real minutes  (default)
#   ×10  → 500  sim-min/real-sec → full March in  ~1.5 real minutes
#   ×100 → 5000 sim-min/real-sec → full March in   ~9 real seconds
DEFAULT_SPEED = 50.0
MIN_SPEED     = 1.0
MAX_SPEED     = 5000.0

QUEUE_SIZE = 30   # transactions shown in live queue
