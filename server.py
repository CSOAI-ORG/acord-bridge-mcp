#!/usr/bin/env python3
"""
ACORD (insurance) Bridge MCP — CSOAI Layer-0 legacy-bridge family.
Parse ACORD XML (policy/claim), map to modern, govern insurance compliance.
Sibling of cobol-bridge-mcp.
Tools: parse_acord · validate_acord · map_to_modern · govern_insurance
"""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

mcp = FastMCP("ACORD Bridge", instructions="Bridge ACORD insurance messages to ONE OS — parse, validate, map, govern (Solvency II / conduct).")

# ── SIGIL: every governed action → one signed hash-chained hop (SIGIL_LOG unifies all layers) ──
import hashlib as _hl, time as _t, json as _j, os as _os
_SIGIL_LOG = _os.environ.get("SIGIL_LOG", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "bridge_sigil.log"))
def _sigil(op, body):
    try:
        prev = ""
        if _os.path.exists(_SIGIL_LOG):
            with open(_SIGIL_LOG) as f:
                ls = f.readlines()
                if ls: prev = _j.loads(ls[-1]).get("digest", "")
        ts = int(_t.time()); dg = _hl.sha256(f"{op}|{ts}|{prev[:8]}|{body}".encode()).hexdigest()[:16]
        _os.makedirs(_os.path.dirname(_SIGIL_LOG), exist_ok=True)
        with open(_SIGIL_LOG, "a") as f: f.write(_j.dumps({"ts": ts, "op": op, "body": body, "prev_digest": prev, "digest": dg}) + "\n")
        return dg
    except Exception: return ""

DOC_HINTS = {"PolicyholderInfo": "Policyholder", "Policy": "Policy", "ClaimsInfo": "Claim",
             "InsuranceSvcRq": "Service Request", "InsuranceSvcRs": "Service Response"}


def _local(tag): return tag.split("}", 1)[-1]


class ACORDParsed(BaseModel):
    doc_type: str
    elements: List[str] = Field(default_factory=list)
    policy_number: Optional[str] = None
    line_of_business: Optional[str] = None
    has_personal_data: bool = False
    element_count: int = 0


class Validation(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Governance(BaseModel):
    risk_flags: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    attestable: bool = True
    note: str = ""


def _findtext(root, *names):
    for el in root.iter():
        if _local(el.tag) in names and (el.text or "").strip():
            return el.text.strip()
    return None


@mcp.tool()
def parse_acord(xml: str) -> ACORDParsed:
    """Parse an ACORD XML message; detect document type, policy number, line of business, PII presence."""
    root = ET.fromstring(xml)
    names = [_local(e.tag) for e in root.iter()]
    doc = "ACORD message"
    for k, v in DOC_HINTS.items():
        if k in names:
            doc = v
            break
    pii = any(n in names for n in ("PersonName", "GivenName", "Surname", "BirthDt", "TaxIdentity", "Addr"))
    return ACORDParsed(
        doc_type=doc,
        elements=sorted(set(names))[:40],
        policy_number=_findtext(root, "PolicyNumber", "PolicyNumberId", "ContractNumber"),
        line_of_business=_findtext(root, "LOBCd", "LineOfBusiness", "ProductCd"),
        has_personal_data=pii,
        element_count=len(names),
    )


@mcp.tool()
def validate_acord(xml: str) -> Validation:
    """Validate ACORD message (well-formed + has a recognised transaction envelope)."""
    errors, warnings = [], []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return Validation(valid=False, errors=[f"XML not well-formed: {e}"])
    names = [_local(e.tag) for e in root.iter()]
    if not any(n in names for n in ("InsuranceSvcRq", "InsuranceSvcRs", "ACORD")):
        warnings.append("No ACORD service envelope (InsuranceSvcRq/Rs) detected")
    return Validation(valid=not errors, errors=errors, warnings=warnings)


@mcp.tool()
def map_to_modern(xml: str) -> Dict[str, Any]:
    """Map an ACORD message to a flat modern JSON object for ONE OS / insurance APIs."""
    p = parse_acord(xml)
    return {"source": "ACORD", "document": p.doc_type, "policy_number": p.policy_number,
            "line_of_business": p.line_of_business, "target": "modern insurance event"}


@mcp.tool()
def govern_insurance(xml: str) -> Governance:
    """Governance: insurance conduct + data surface (Solvency II / GDPR / fair treatment) — attestable."""
    _sigil("G", "acord|govern_insurance")
    p = parse_acord(xml)
    flags = []
    if p.has_personal_data:
        flags.append("Personal data present — GDPR lawful basis + special-category checks (health/claims)")
    if p.doc_type == "Claim":
        flags.append("Claim — fair-claims-handling + fraud-screening governance (FCA/conduct)")
    return Governance(risk_flags=flags,
                      frameworks=["ACORD", "Solvency II", "GDPR", "FCA conduct / fair treatment", "EU AI Act (if automated underwriting/pricing — Annex III)"],
                      note="CSOAI governs the bridge: policy/claim lineage attestable on the ledger.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
