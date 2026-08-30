"""Mock provider - vendor information, pricing, technical extraction."""
from __future__ import annotations

import re
from typing import List, Optional

from app.ai.mock_provider import MockProvider
from app.ai.schemas import (
    Evidence,
    PricingAnalysis,
    TechnicalCapabilities,
    VendorInformation,
)


def _vendor_info(text: str) -> VendorInformation:
    name = None
    m = re.search(
        r"(?:proposal from|proposed by|by)\s+([A-Za-z0-9 &.\-]+?)(?=\s+dated|\s+version|\s+v\d|\n|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
    if not name:
        m = re.search(
            r"(?:proposal from|proposed by|by)\s+([A-Za-z0-9 &.\-]{1,60})",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            name = m.group(1).strip()
    if not name:
        m = re.search(
            r"^([A-Z][A-Za-z0-9 &.\-]{2,60})\s+(?:Proposal|Response|Quotation|RFP)",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if m:
            name = m.group(1).strip()
    contact = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"\+?\d[\d\s().-]{7,}\d", text)
    return VendorInformation(
        vendor_name=name,
        contact_email=contact.group(0) if contact else None,
        contact_phone=phone.group(0) if phone else None,
    )


def _pricing(text: str) -> PricingAnalysis:
    amounts = MockProvider._find_money(text)
    annual = next((a for a in amounts if a > 1000), None)
    impl = next((a for a in amounts if 1_000 < a < 100_000 and "implementation" in text.lower()), None)
    license = next((a for a in amounts if "license" in text.lower()), None)
    support = next((a for a in amounts if "support" in text.lower()), None)
    monthly = next((a for a in amounts if "month" in text.lower() and a < 10_000), None)
    currency = "USD" if "$" in text else None
    escal = MockProvider._find_percentage(text, r"(escalation|annual increase|price increase)")
    y1 = annual or (monthly * 12 if monthly else None)
    y3 = (y1 * 3 + (impl or 0)) if y1 else None
    y5 = (y1 * 5 + (impl or 0)) if y1 else None
    return PricingAnalysis(
        currency=currency,
        annual_cost=annual,
        monthly_cost=monthly,
        implementation_cost=impl,
        license_cost=license,
        support_cost=support,
        price_escalation_pct=escal,
        year1_total=y1,
        year3_total=y3,
        year5_total=y5,
        recurring_annual_cost=annual,
        assumptions=[
            "Calculated from explicitly stated amounts in the proposal",
            "Year 3/5 totals assume recurring annual cost repeats unless escalation specified",
        ],
        notes=("Normalized from line items where available." if annual else "Pricing could not be confidently derived."),
    )


def _technical(text: str) -> TechnicalCapabilities:
    t = text.lower()
    sla = None
    m = re.search(r"(99\.[0-9]+)\s*%", t)
    if m:
        sla = float(m.group(1))
    max_users = None
    m = re.search(r"([0-9][0-9,]+)\s+(concurrent\s+users|users)", t)
    if m:
        try:
            max_users = int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return TechnicalCapabilities(
        api=MockProvider._bool_match(t, ["rest api", " api ", "restful", "graphql"]),
        api_rest=MockProvider._bool_match(t, ["rest api", "restful"]),
        api_graphql=MockProvider._bool_match(t, ["graphql"]),
        api_soap=MockProvider._bool_match(t, ["soap api", "soap "]),
        sso=MockProvider._bool_match(t, ["sso", "single sign-on", "single sign on"]),
        oauth=MockProvider._bool_match(t, ["oauth"]),
        saml=MockProvider._bool_match(t, ["saml"]),
        encryption_at_rest=MockProvider._bool_match(t, ["encryption at rest", "encrypted at rest", "at-rest encryption"]),
        encryption_in_transit=MockProvider._bool_match(t, ["encryption in transit", "tls", "https", "ssl"]),
        cloud_deployment=MockProvider._bool_match(t, ["cloud", "saas", "aws", "azure", "gcp"]),
        on_premise_deployment=MockProvider._bool_match(t, ["on-premise", "on premise", "on-premises", "self-hosted"]),
        sla_percentage=sla,
        max_concurrent_users=max_users,
        backup=MockProvider._bool_match(t, ["backup", "backups"]),
        disaster_recovery=MockProvider._bool_match(t, ["disaster recovery", " dr ", "rto", "rpo"]),
        monitoring=MockProvider._bool_match(t, ["monitoring", "observability", "metrics", "logs"]),
        integrations=[k for k in ["slack", "salesforce", "jira", "github", "okta", "azure ad", "active directory", "sap", "oracle"] if k in t],
        compliance=[k.upper() if k != "pci-dss" else "PCI-DSS" for k in ["soc 2", "soc2", "iso 27001", "iso27001", "gdpr", "hipaa", "pci", "pci-dss", "fedramp"] if k in t],
        database_support=[k for k in ["postgresql", "postgres", "mysql", "mongodb", "mssql", "sql server", "dynamodb", "redis"] if k in t],
    )