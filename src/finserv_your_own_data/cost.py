"""Per-run cost ESTIMATION (issue #10) — never presented as a billed actual.

A real deployment's authoritative dollar figure lives behind AMP's own
observability once this crew is deployed (out of scope here, mock-first
discipline). This module exists so a kickoff's own output can still name a
concrete cost figure offline, where no real usage metrics exist at all — a
`ScriptedLLM` makes no network call, so crewai's own token accounting never
populates in tests. `docs/research/ideas/amp-paid-hands-on/the-bill.md`'s
"ten thousand runs" arithmetic only works if the run names a number; this is
that number, clearly labeled as rough.
"""

from __future__ import annotations

from dataclasses import dataclass

# A rough, blended $/1K-token constant — NOT a real provider rate, and never
# swapped for one silently. A real deployment should read AMP's own
# billed-actual figure instead of this estimate.
ESTIMATED_USD_PER_1K_TOKENS = 0.003

# ~4 characters per token is the standard rough heuristic for English text —
# no tokenizer dependency, no network. Good enough for an explicitly-labeled
# estimate, not for anything billed.
_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class CostEstimate:
    """A cost figure that is ALWAYS an estimate in this codebase — issue #10
    acceptance requires it never be presented as a billed actual."""

    estimated_tokens: int
    estimated_usd: float

    @property
    def label(self) -> str:
        return (
            f"~${self.estimated_usd:.4f} (ESTIMATE, not a billed actual — "
            f"~{self.estimated_tokens} tokens)"
        )


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_cost(*texts: str) -> CostEstimate:
    """Estimate a run's cost from the raw text it pushed through the model
    (prompt + completion) — the only signal available offline / under
    ScriptedLLM, which reports no real usage."""
    tokens = sum(estimate_tokens(t) for t in texts if t)
    usd = (tokens / 1000) * ESTIMATED_USD_PER_1K_TOKENS
    return CostEstimate(estimated_tokens=tokens, estimated_usd=usd)
