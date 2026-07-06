"""Synthetic company-profile lookup (issue #10).

All entities are invented and unmistakably fictional (CONTRIBUTING.md) — used
only for tutorial/lab fixtures. The live step (steps/05) has an attendee
enrich a REAL public company instead; a real name simply won't be on file
here, which is the expected, gracefully-handled "no profile" path (see
crew.py / surface.py), never an error.

The data ships as **package data** inside this package (`data/companies.json`)
and is loaded via `importlib.resources`, so it resolves identically whether the
module runs from source, from the compiler's copied demo-checkpoint tree, or
from an installed wheel on AMP (amp-showcase #31 — a source-relative path
breaks once the package is installed).
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def _load_companies() -> dict[str, Any]:
    data = files("finserv_your_own_data").joinpath("data/companies.json").read_text()
    return json.loads(data)


def lookup_company(name: str) -> dict[str, Any] | None:
    """The synthetic profile for `name`, or None if nothing is on file —
    never raises. A caller-supplied real company (the live step) or a typo
    both legitimately resolve to None; that's a normal outcome, not a
    failure."""
    return _load_companies().get(name)


def known_company_names() -> list[str]:
    return sorted(_load_companies())
