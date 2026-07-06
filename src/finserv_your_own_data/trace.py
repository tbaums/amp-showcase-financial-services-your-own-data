"""Per-run, per-caller isolated trace store (issue #10).

Every enrichment run gets its own `run_id` and its own `TraceRecord` — two
callers' runs must never merge or overwrite each other (acceptance: a
per-call isolated, cost-annotated trace retrievable by run_id).
`TraceStore` is a plain in-memory dict scoped to one process; the
authoritative, cross-restart trace once this is actually deployed is AMP's
own observability (keyed by that same kickoff's run), not this store — this
module exists so the crew's own output can be attributed a labeled cost
figure and looked back up within a process, which is exactly what the unit
tests exercise offline (mock-first; no live AMP trace API here).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from finserv_your_own_data.cost import CostEstimate


@dataclass(frozen=True)
class TraceRecord:
    run_id: str
    company_name: str
    found_profile: bool
    summary: str
    cost: CostEstimate


class TraceStore:
    def __init__(self) -> None:
        self._records: dict[str, TraceRecord] = {}

    def record(
        self, *, company_name: str, found_profile: bool, summary: str, cost: CostEstimate
    ) -> TraceRecord:
        run_id = str(uuid.uuid4())
        rec = TraceRecord(
            run_id=run_id,
            company_name=company_name,
            found_profile=found_profile,
            summary=summary,
            cost=cost,
        )
        self._records[run_id] = rec
        return rec

    def get(self, run_id: str) -> TraceRecord | None:
        """Exactly the record for `run_id`, never another caller's — the
        isolation this scenario's acceptance criteria require."""
        return self._records.get(run_id)
