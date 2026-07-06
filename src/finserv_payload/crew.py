"""The company-enrichment crew (issue #10).

One agent, one task: look up the caller's own company payload against the
synthetic profile data (tutorial/lab) or a real public company (live step),
and produce a concise, sales-enrichment-style brief. `llm` is injected by
the caller (`main.py` for a real deployment, `ScriptedLLM` for offline
tests — see scenarios/_shared/llm_mock.py) so this module never hard-codes a
provider.
"""

from __future__ import annotations

from crewai import Agent, Crew, Task
from crewai.tools import tool

from finserv_payload.lookup import lookup_company


@tool("enrich_company")
def enrich_company_tool(company_name: str) -> str:
    """Look up a company in the synthetic profile database by its exact
    name. Returns a short profile description, or that nothing is on file
    for that name — never fabricate a profile that isn't there."""
    record = lookup_company(company_name)
    if record is None:
        return (
            f"No public profile on file for {company_name!r}. Report this plainly — "
            "do not invent sector, headquarters, or history."
        )
    return (
        f"{company_name} — {record['sector']}, headquartered in {record['headquarters']}. "
        f"{record['notable']} Relationship notes: {record['relationship_notes']}"
    )


def build_enrichment_crew(company_name: str, llm) -> Crew:
    """A crew scoped to enriching exactly one company. Built fresh per
    request (never shared/mutated across callers) so two callers' payloads
    can never leak into each other — see surface.py's per-run isolation."""
    analyst = Agent(
        role="Client Enrichment Analyst",
        goal=(
            f"Research {company_name!r} using the enrich_company tool and write a concise, "
            "factual sales-enrichment brief a relationship manager can use to judge fit as a "
            "client."
        ),
        backstory=(
            "A careful research analyst who enriches a caller's own company payload before a "
            "relationship manager considers it as a prospective client. Reports facts plainly — "
            "explicitly says when nothing is on file rather than inventing details."
        ),
        tools=[enrich_company_tool],
        llm=llm,
    )
    task = Task(
        description=(
            f"Research {company_name!r} using the enrich_company tool, then write a 2-3 "
            "sentence enrichment brief naming the company and stating what was found — or "
            "plainly stating that no public profile is on file."
        ),
        expected_output=(
            "A short enrichment brief that names the company and states its profile result."
        ),
        agent=analyst,
    )
    return Crew(agents=[analyst], tasks=[task])
