"""
European Custom Data Hub — Real-Time Demo API
FastAPI backend on port 8505.

Endpoints
─────────
GET  /health
GET  /api/queue                 latest 30 live transactions (real-time feed)
GET  /api/transactions          paginated historical query
GET  /api/metrics               VAT aggregates with filters
GET  /api/simulation/status     current simulation state
POST /api/simulation/start
POST /api/simulation/pause
POST /api/simulation/resume
POST /api/simulation/speed      body: {"speed": <float>}
POST /api/simulation/reset
GET  /api/catalog/suppliers     list of supplier names
GET  /api/catalog/countries     list of country codes + names
"""
from __future__ import annotations

import asyncio
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lib.config import DEFAULT_SPEED, MIN_SPEED, MAX_SPEED, QUEUE_SIZE
from lib.database import (
    get_latest_transactions,
    get_transaction_count,
    get_vat_metrics,
    insert_transaction,
    query_transactions,
    reset_simulation_db,
    get_sim_counts,
)
from lib.simulator import state, simulation_loop
from lib.catalog import SUPPLIERS, COUNTRY_NAMES

# ── Live queue (in-memory ring buffer, filled by simulation) ──────────────────

_live_queue: deque[dict] = deque(maxlen=QUEUE_SIZE)


def _fire_transactions(rows: list[dict]) -> None:
    """Called by the simulation loop when transactions are due."""
    for row in rows:
        insert_transaction(row)
        _live_queue.appendleft(row)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    from lib.database import init_european_custom_db, init_simulation_db
    init_european_custom_db()
    init_simulation_db()
    task = asyncio.create_task(simulation_loop(_fire_transactions))
    yield
    task.cancel()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="European Custom Data Hub — RTDemo",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "records_in_db": get_transaction_count()}


# ── Live queue ────────────────────────────────────────────────────────────────

@app.get("/api/queue")
def get_queue():
    """Return the latest 30 transactions from the live simulation feed."""
    # If simulation has not started yet, fall back to DB
    if not _live_queue:
        return {"items": get_latest_transactions(QUEUE_SIZE), "source": "db"}
    return {"items": list(_live_queue)[:QUEUE_SIZE], "source": "live"}


# ── Historical transactions ────────────────────────────────────────────────────

@app.get("/api/transactions")
def get_transactions(
    seller_name:    str | None = Query(None),
    buyer_country:  str | None = Query(None),
    seller_country: str | None = Query(None),
    date_from:      str | None = Query(None),
    date_to:        str | None = Query(None),
    limit:          int        = Query(200, ge=1, le=1000),
    offset:         int        = Query(0,   ge=0),
):
    rows = query_transactions(
        seller_name=seller_name,
        buyer_country=buyer_country,
        seller_country=seller_country,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"total": len(rows), "items": rows}


# ── Metrics ───────────────────────────────────────────────────────────────────

@app.get("/api/metrics")
def get_metrics(
    seller_name:    str | None = Query(None),
    buyer_country:  str | None = Query(None),
    seller_country: str | None = Query(None),
    date_from:      str | None = Query(None),
    date_to:        str | None = Query(None),
):
    return get_vat_metrics(
        seller_name=seller_name,
        buyer_country=buyer_country,
        seller_country=seller_country,
        date_from=date_from,
        date_to=date_to,
    )


# ── Simulation control ────────────────────────────────────────────────────────

@app.get("/api/simulation/status")
def sim_status():
    counts = get_sim_counts()
    s = state.to_dict()
    s.update(counts)
    return s


@app.post("/api/simulation/start")
def sim_start():
    if state.sim_time >= __import__("lib.config", fromlist=["SIM_END_DT"]).SIM_END_DT:
        return {"ok": False, "reason": "simulation already finished — reset first"}
    state.running = True
    return {"ok": True, "status": state.to_dict()}


@app.post("/api/simulation/pause")
def sim_pause():
    state.running = False
    return {"ok": True, "status": state.to_dict()}


@app.post("/api/simulation/resume")
def sim_resume():
    state.running = True
    return {"ok": True, "status": state.to_dict()}


class SpeedPayload(BaseModel):
    speed: float


@app.post("/api/simulation/speed")
def sim_speed(payload: SpeedPayload):
    state.speed = max(MIN_SPEED, min(MAX_SPEED, payload.speed))
    return {"ok": True, "speed": state.speed}


@app.post("/api/simulation/reset")
def sim_reset():
    state.reset()
    reset_simulation_db()
    _live_queue.clear()
    return {"ok": True, "status": state.to_dict()}


# ── Catalog ───────────────────────────────────────────────────────────────────

@app.get("/api/catalog/suppliers")
def catalog_suppliers():
    return [{"id": s["id"], "name": s["name"], "country": s["country"]}
            for s in SUPPLIERS]


@app.get("/api/catalog/countries")
def catalog_countries():
    return [{"code": k, "name": v} for k, v in COUNTRY_NAMES.items()]
