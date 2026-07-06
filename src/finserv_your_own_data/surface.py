"""Payload entrypoint (issue #10) — enrich the caller's own company, cost
label it, and store it as a per-run isolated trace.

Unlike the async Slack surface in ../no-code-trigger (a different value prop),
this scenario's wow moment is the synchronous call-and-read: the caller
brings their own company, calls the endpoint, and immediately reads back
both the enrichment brief and its labeled cost estimate — no separate
delivery channel needed.

Real-world payloads are messier than fixtures. `run_enrichment` never lets a
crash reach the caller — an empty/blank payload or a company enrichment
failure both degrade to a legible result (issue #10 acceptance), never an
unhandled exception.
"""

from __future__ import annotations

from dataclasses import dataclass

from finserv_your_own_data.cost import estimate_cost
from finserv_your_own_data.crew import build_enrichment_crew
from finserv_your_own_data.lookup import lookup_company
from finserv_your_own_data.trace import TraceStore

# Shown at the point of input (surface + docs, issue #10 acceptance) — framing
# borrowed from the portfolio brief: "a public company you'd love as a
# customer," never a private/confidential client record.
PUBLIC_DATA_NOTICE = (
    "Public / non-PII data only — enter a real PUBLIC company you'd love as a client. "
    "Never paste a private, confidential, or client-specific record."
)


@dataclass(frozen=True)
class PayloadRequest:
    """One caller's own payload — never shared/merged with another
    caller's (per-run isolation, issue #10 acceptance)."""

    caller_id: str
    company_name: str


@dataclass(frozen=True)
class EnrichmentResult:
    run_id: str
    summary: str
    found_profile: bool
    cost_label: str


def run_enrichment(request: PayloadRequest, llm, trace_store: TraceStore) -> EnrichmentResult:
    """Run one caller's enrichment, cost-label it, and record it under a
    fresh run_id — never raises, so a messy payload degrades to a legible
    result instead of crashing the caller's call."""
    company_name = request.company_name.strip()

    if not company_name:
        summary = "Please provide a company name — public companies only, no private client data."
        record = trace_store.record(
            company_name="",
            found_profile=False,
            summary=summary,
            cost=estimate_cost(summary),
        )
        return EnrichmentResult(
            run_id=record.run_id,
            summary=summary,
            found_profile=False,
            cost_label=record.cost.label,
        )

    try:
        summary = build_enrichment_crew(company_name, llm).kickoff().raw
    except Exception as exc:  # crewai/LLM failure — degrade, never crash the caller
        summary = (
            f"Couldn't complete enrichment for {company_name!r} ({exc}). "
            "Here's where it found nothing — try again."
        )

    found_profile = lookup_company(company_name) is not None
    cost = estimate_cost(company_name, summary)
    record = trace_store.record(
        company_name=company_name,
        found_profile=found_profile,
        summary=summary,
        cost=cost,
    )
    return EnrichmentResult(
        run_id=record.run_id,
        summary=summary,
        found_profile=found_profile,
        cost_label=record.cost.label,
    )
