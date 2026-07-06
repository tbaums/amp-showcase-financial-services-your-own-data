"""AMP Flow entrypoint (issue #10) — mirrors the proven Autodesk shape
(a `Flow` subclass + a no-argument `kickoff()`), fixing the live-deploy bug
where `type="flow"` requires a real Flow, not a bare function (amp-showcase
#29). The trigger payload (`caller_id`, `company_name`) is read from env
(with synthetic defaults) so the deployed crew is runnable for a smoke
kickoff; a real shared surface supplies these fields live.

Enrichment + cost-labeling + trace recording run synchronously inside the
Flow step — this scenario's wow moment is the synchronous call-and-read, and
there is no external delivery channel to guard. AMP runs the kickoff
asynchronously and exposes the result via its own status endpoint.

`_TRACE_STORE` is process-scoped, not the authoritative record: once
deployed, "read the trace" means opening AMP's own per-run observability for
this kickoff's run — this module's job is only to make sure its own output
always names a run_id and a clearly-labeled cost estimate.
"""

from __future__ import annotations

import os

from crewai import LLM
from crewai.flow.flow import Flow, start

from finserv_your_own_data.surface import PUBLIC_DATA_NOTICE, PayloadRequest, run_enrichment
from finserv_your_own_data.trace import TraceStore

DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"

_TRACE_STORE = TraceStore()


def _request_from_env() -> PayloadRequest:
    return PayloadRequest(
        caller_id=os.environ.get("SMOKE_CALLER_ID", "live-smoke-test"),
        company_name=os.environ.get("SMOKE_COMPANY", "Cascadia Mercantile Bank"),
    )


class PayloadFlow(Flow):
    @start()
    def enrich_and_trace(self) -> dict:
        request = _request_from_env()
        result = run_enrichment(request, LLM(model=DEFAULT_MODEL), _TRACE_STORE)
        return {
            "run_id": result.run_id,
            "summary": result.summary,
            "found_profile": result.found_profile,
            "cost": result.cost_label,
            "notice": PUBLIC_DATA_NOTICE,
        }


def kickoff():
    """AMP deployment entrypoint (no args; mirrors Autodesk)."""
    return PayloadFlow().kickoff()


def read_trace(run_id: str) -> dict | None:
    """Look back up a prior run by its run_id — this process's own record
    of it, not a shared/merged view across callers."""
    record = _TRACE_STORE.get(run_id)
    if record is None:
        return None
    return {
        "run_id": record.run_id,
        "company_name": record.company_name,
        "found_profile": record.found_profile,
        "summary": record.summary,
        "cost": record.cost.label,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(kickoff(), indent=2, default=str))
