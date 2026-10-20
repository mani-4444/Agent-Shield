"""Patterns that must never appear in generated data or fixtures.

Sources: SPEC.md AC-3 and Part 4; AGENTS.md "Never".

Synthetic identifiers only: phones start "+91 0", VPAs end @fakepay or @examplebank, secrets start
CANARY-. Each finder returns the offending substrings so a failure message shows what leaked.
"""

from __future__ import annotations

import re

ALLOWED_VPA_DOMAINS = frozenset({"fakepay", "examplebank"})

# Indian mobile numbers start 6-9; fakes start with 0. Allow one space/dash between 5-digit halves.
MOBILE = re.compile(r"(?<!\d)[6-9]\d{4}[ -]?\d{5}(?!\d)", re.ASCII)
# Any "+91" not followed by " 0" is a real-format phone number.
PHONE_PREFIX = re.compile(r"\+91(?! 0)")
# Aadhaar-like: 12 digits, optionally grouped 4-4-4.
AADHAAR = re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)", re.ASCII)
# PAN-like: AAAAA9999A.
PAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Za-z0-9])", re.ASCII)
# Anything handle@domain; the domain (first label) must be an allowed fake one.
AT_HANDLE = re.compile(r"[A-Za-z0-9._-]+@([A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)*)")
# Real Indian banks / UPI apps (AGENTS.md "Never": no real bank names). Word-bounded, any case.
REAL_BRANDS = re.compile(
    r"\b(sbi|state bank|hdfc|icici|axis bank|kotak|yes bank|idfc|indusind|canara|pnb|"
    r"punjab national|bank of baroda|union bank|paytm|phonepe|google pay|gpay|bhim|"
    r"amazon pay|airtel payments)\b",
    re.IGNORECASE,
)


def find_pii(text: str) -> list[str]:
    """Return every real-looking identifier in `text` (empty list = clean)."""
    hits: list[str] = []
    hits += MOBILE.findall(text)
    hits += [m.group(0) + "..." for m in PHONE_PREFIX.finditer(text)]
    hits += AADHAAR.findall(text)
    hits += PAN.findall(text)
    for m in AT_HANDLE.finditer(text):
        domain = m.group(1).lower()
        if domain not in ALLOWED_VPA_DOMAINS:
            hits.append(m.group(0))
    hits += [m.group(0) for m in REAL_BRANDS.finditer(text)]
    return hits


def iter_strings(value: object) -> list[str]:
    """All string (and integer, as text) leaves of a parsed JSON value."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, bool):
        pass
    elif isinstance(value, int):
        out.append(str(value))
    elif isinstance(value, dict):
        for v in value.values():
            out += iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            out += iter_strings(v)
    return out
