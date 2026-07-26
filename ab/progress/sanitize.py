"""Deterministic sanitization of API responses before they are committed (#70).

This repository is public. Committed fixtures are **sanitized structural
evidence**, not raw API captures: they exist to prove a model's shape, and no
production value needs to survive for that.

Three properties matter:

**Deterministic.** The same input always produces the same output, in this
process and the next. Substitutions derive from SHA-256 of the original value
plus a fixed salt, so re-capturing an unchanged response yields byte-identical
output. Anything random would make every recapture look like a real diff, the
no-drift gates would thrash, and reviewers would stop reading fixture diffs --
which is exactly when unsanitized data slips through.

**Structure-preserving.** Keys (and therefore aliases), types, nullability,
nesting and list cardinality survive untouched. Only leaf values change, and a
sanitized fixture still validates against the model it certifies -- an email
stays an email, a UUID stays a UUID, ``None`` stays ``None``.

**Referentially consistent.** Because substitution is a pure function of the
value, the same input maps to the same output everywhere: a company id repeated
across three nested objects stays equal to itself after sanitization, so
fixtures that join on an identifier still join.

## Confident vs. ambiguous

Blind key matching is destructive here. ``name`` appears 158 times across these
fixtures and is usually an enum label ("Invoice", "Active"); ``countryName`` is
"United States". Rewriting those to a person name would corrupt reference data
and teach reviewers to ignore the diff.

So detections carry a :class:`Confidence`:

* :attr:`Confidence.HIGH` -- unambiguous (an email, a phone, a street address,
  a coordinate, a person-shaped name). Rewritten automatically.
* :attr:`Confidence.REVIEW` -- plausible but not certain (a bare ``name`` whose
  value is a single word, a generic identifier). **Never rewritten silently.**
  Reported for an operator decision.

That split is what makes sanitization safe to run repository-wide.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

#: Fixed salt. Changing it re-pseudonymises every fixture, so treat it as frozen
#: once fixtures are committed.
_SALT = "ab-sdk-fixture-sanitizer-v1"


class Confidence(str, Enum):
    """How certain a detection is -- decides rewrite vs. operator review."""

    HIGH = "high"
    REVIEW = "review"


class Kind(str, Enum):
    """What a detected value is."""

    NAME = "name"
    COMPANY = "company"
    EMAIL = "email"
    PHONE = "phone"
    STREET = "street"
    CITY = "city"
    POSTCODE = "postcode"
    COORDINATE = "coordinate"
    TRACKING = "tracking"
    GOVID = "govid"
    ACCOUNT = "account"
    MONEY = "money"
    TEXT = "text"
    SECRET = "secret"
    UUID = "uuid"
    USERNAME = "username"
    IDENTIFIER = "identifier"


# ---------------------------------------------------------------------------
# Key classification
# ---------------------------------------------------------------------------

#: Keys never touched: structural, enumeration or geographic-reference values
#: that carry no personal data and whose mutation would break validation or make
#: fixtures unreadable.
SAFE_KEYS = frozenset(
    {
        "type", "status", "state", "code", "kind", "category", "unit",
        "currency", "country", "countrycode", "countryname", "countryid",
        "method", "surface", "version", "success", "successfully", "iserror",
        "isvalid", "isactive", "isdefault", "isdeleted", "enabled", "disabled",
        "page", "pagesize", "pagenumber", "totalpages", "totalcount", "count",
        "propertytype", "dontvalidate", "forceempty",
    }
)

_HIGH_KEY_PATTERNS: list[tuple[re.Pattern, Kind]] = [
    (re.compile(r"e?mail", re.I), Kind.EMAIL),
    (re.compile(r"phone|mobile|^fax$|telephone", re.I), Kind.PHONE),
    (re.compile(r"^address\d|^address\d?value$|street|addressline", re.I), Kind.STREET),
    (re.compile(r"latitude|longitude|^lat$|^lng$|^lon$", re.I), Kind.COORDINATE),
    (re.compile(r"zip|postal", re.I), Kind.POSTCODE),
    (re.compile(r"tracking|waybill|pro_?number|barcode", re.I), Kind.TRACKING),
    (re.compile(r"ssn|tax_?id|^ein$|license|passport", re.I), Kind.GOVID),
    (re.compile(r"account_?number|routing|iban|^card|cvv", re.I), Kind.ACCOUNT),
    (re.compile(r"token|secret|password|api_?key|authorization|bearer", re.I), Kind.SECRET),
    (re.compile(r"^(first|last|middle|full|given|family)[a-z]*_?name$|contact_?name$|payer_?name$", re.I), Kind.NAME),
    (re.compile(r"created_?by|modified_?by|updated_?by|^user_?name$|^owner$|^login$", re.I), Kind.USERNAME),
    # Company/franchise names identify Annex customers and partners. Not
    # personal data, but the customer list is commercially sensitive and a
    # fixture only needs the *shape* of a company name to prove the model.
    (re.compile(r"company_?name$|^company$", re.I), Kind.COMPANY),
    (re.compile(r"^city$|cityline|township|locality", re.I), Kind.CITY),
]

_REVIEW_KEY_PATTERNS: list[tuple[re.Pattern, Kind]] = [
    (re.compile(r"name$", re.I), Kind.NAME),
    (re.compile(r"note|comment|description|memo|remark|instruction|message", re.I), Kind.TEXT),
    (re.compile(r"price|amount|cost|total|subtotal|fee|charge|rate|balance|revenue", re.I), Kind.MONEY),
    (re.compile(r"id$|guid|uuid", re.I), Kind.IDENTIFIER),
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_PHONE_RE = re.compile(r"^\+?[\d][\d\-.() ]{7,}\d$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")
#: "Dana Whitfield" / "Mary-Jo O'Brien" -- two or more capitalised word tokens.
_PERSON_NAME_RE = re.compile(r"^[A-Z][a-z'\-]+(?: [A-Z][a-z'\-.]+){1,3}$")
#: "7580 Metropolitan Dr" -- a street number followed by words.
_STREET_RE = re.compile(r"^\d+[A-Za-z]?\s+\w+")

#: Sentinel values that carry meaning rather than data. Rewriting an all-zero
#: UUID would turn "explicitly absent" into "some other record" and can break
#: code that tests for it.
SENTINELS = frozenset(
    {
        "00000000-0000-0000-0000-000000000000",
        "0001-01-01T00:00:00",
        "N/A",
        "n/a",
        "-",
    }
)

# --- idempotency ------------------------------------------------------------
# Sanitization must be a *fixed point*: sanitizing an already-sanitized value
# must return it unchanged. Without this, re-running the tool churns every
# fixture (74 values on CompanyDetails.json alone), the no-drift gate thrashes,
# committed hashes move for no reason, and the repository-wide safety test
# flags the sanitizer's own output as sensitive.
#
# Every substitution therefore lands in a recognisable image: reserved pools for
# text-like kinds, a marked UUID version nibble, and small reserved sets for the
# numeric kinds that would otherwise be indistinguishable from real data.

#: Version nibble marking a UUID as sanitiser output. Real UUIDs are v1-v5/v7.
_UUID_MARK = "a"
#: Reserved numeric sets, so a sanitized number is recognisable as one.
_ZIPS = ("90210", "10001", "60601", "73301", "94105", "30301", "80202", "02108")
_LATS = (34.05, 40.71, 41.88, 30.27, 37.77, 33.75, 39.74, 42.36)
_LONS = (-118.24, -74.01, -87.63, -97.74, -122.42, -84.39, -104.99, -71.06)
_MONEY = (10.0, 25.5, 49.99, 100.0, 250.0, 499.95, 1000.0, 2500.0)
#: Reserved integers for numeric identifiers/secrets (e.g. a carrier locationId),
#: which are otherwise indistinguishable from a real value on a second pass.
_INTS = (1001, 2002, 3003, 4004, 5005, 6006, 7007, 8008)

_COMPANY_HEAD = ("Northwind", "Lakeshore", "Ridgeline", "Fairmont", "Brightwater")
_COMPANY_TAIL = ("Logistics", "Galleries", "Trading Co", "Interiors", "Freight")
_FIRST = ("Avery", "Bailey", "Casey", "Devon", "Emery", "Finley", "Harper", "Jordan")
_LAST = ("Alder", "Brook", "Cedar", "Dunmore", "Everly", "Fenwick", "Grayson", "Holt")
_STREETS = ("Cedar Way", "Juniper Ln", "Meridian Ave", "Quarry Rd", "Sable St")
_CITIES = ("Fairview", "Lakemont", "Northgate", "Riverton", "Westfield")


def _norm(key: str) -> str:
    return key.lower().replace("_", "")


def is_sanitized(value: Any) -> bool:
    """True when *value* is already this module's output.

    Makes :func:`sanitize` idempotent and stops :func:`audit` reporting the
    sanitizer's own substitutions as findings.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return (
            value in _MONEY
            or value in _LATS
            or value in _LONS
            or value in _INTS
            or str(int(value)).zfill(5) in _ZIPS
        )
    if not isinstance(value, str):
        return False
    if value == "REDACTED" or value.startswith("sanitized"):
        return True
    if value in _ZIPS or value in _CITIES:
        return True
    if _UUID_RE.match(value) and value[14:15].lower() == _UUID_MARK:
        return True
    if value.endswith("@example.com"):
        return True
    if value.startswith("555-"):
        return True
    if value.startswith("1Z") and value[2:].isdigit():
        return True
    if value.startswith("XXX-XX-") or value.startswith("****"):
        return True
    parts = value.replace(".", " ").split()
    if len(parts) == 2:
        first, last = parts[0].strip(), parts[1].strip()
        if first.capitalize() in _FIRST and last.capitalize() in _LAST:
            return True  # "Bailey Holt" or "bailey.holt"
        if first in _COMPANY_HEAD:
            return True
    if any(value.endswith(s) for s in _STREETS) or any(
        value.endswith(t) for t in _COMPANY_TAIL
    ):
        return True
    return False


#: Containers whose entire subtree is credential material, whatever the leaf is
#: called. Chasing key names here is a losing game -- ``accountInformation``
#: alone holds ``clientSecret``, ``accessKey``, ``appId``, ``billTo``,
#: ``controlStation`` and ``shipperNumber``, and the next carrier integration
#: will invent three more. Classifying by container catches them all, including
#: fields that do not exist yet.
SECRET_CONTAINERS = ("accountinformation", "credentials", "apiaccounts", "restapiaccounts")


def _in_secret_container(path: str | None) -> bool:
    if not path:
        return False
    segments = re.split(r"[.\[\]]+", path.lower())
    return any(seg in SECRET_CONTAINERS for seg in segments)


#: Sibling fields that mark the containing object as a *person or company
#: record* rather than a lookup row. Without this, a bare ``name`` holding
#: "American Samoa" or "Credit Card Auth" scores the same as "Dana Whitfield" --
#: which corrupted 69 reference labels across CountryCodeDto, GridViewInfo and
#: DocumentTypeBySource on the first repository-wide pass.
PERSON_SIGNALS = frozenset(
    {
        "email", "contactemail", "phone", "contactphone", "mobile", "fax",
        "login", "username", "firstname", "lastname", "fullname",
        "address1", "address2", "contactid", "companyid", "userid",
    }
)


#: Keys of the portal's "overridable field" wrapper. Such an object names its
#: field in the *parent* key (``firstLastName``, ``company``) and holds the data
#: under generic leaves, so leaf-key classification sees only ``defaultValue``
#: and misses the payload entirely.
OVERRIDE_SLOTS = frozenset({"defaultvalue", "value", "overridevalue", "forceempty"})


def is_override_wrapper(node: Any) -> bool:
    """True when *node* is an overridable-field wrapper rather than a record."""
    if not isinstance(node, dict) or not node:
        return False
    return all(_norm(k) in OVERRIDE_SLOTS for k in node)


#: Sibling fields marking the containing object as a *company* record.
#: SearchCompanyResponse rows carry companyName + parentCompanyId; a
#: CountryCodeDto row ({code, iataCode, id, name}) carries neither, which is
#: what separates "Lefflers Antiques" from "American Samoa".
COMPANY_SIGNALS = frozenset(
    {
        "companyname", "parentcompanyid", "companytype", "companycode",
        "companyid", "companydisplayid", "franchiseeid", "typeid",
    }
)


def has_person_signal(siblings: dict | None) -> bool:
    """True when the containing object looks like a real person record."""
    if not isinstance(siblings, dict):
        return False
    return any(_norm(k) in PERSON_SIGNALS for k in siblings)


def has_company_signal(siblings: dict | None) -> bool:
    """True when the containing object looks like a real company record."""
    if not isinstance(siblings, dict):
        return False
    return any(_norm(k) in COMPANY_SIGNALS for k in siblings)


def classify(
    key: str | None,
    value: Any,
    path: str | None = None,
    siblings: dict | None = None,
) -> tuple[Kind, Confidence] | None:
    """Classify a leaf value. ``None`` means "not sensitive".

    Value shape can *promote* a key-based guess: a bare ``name`` holding
    "Dana Whitfield" is a person, while one holding "Invoice" is an enum label.
    *path* enables container-scoped rules (see :data:`SECRET_CONTAINERS`).
    """
    if value is None or isinstance(value, bool) or value == "":
        return None
    if isinstance(value, str) and value in SENTINELS:
        return None

    # Already our own output: leave it alone, so sanitization is a fixed point
    # and the audit never flags values this module produced.
    if is_sanitized(value):
        return None

    # Container rule wins: inside a credentials blob, every populated scalar is
    # a secret regardless of what the field happens to be named.
    if _in_secret_container(path):
        return Kind.SECRET, Confidence.HIGH

    # Value-shape detections win outright -- they are self-evidencing.
    if isinstance(value, str):
        if _EMAIL_RE.match(value):
            return Kind.EMAIL, Confidence.HIGH
        if _ISO_DATE_RE.match(value):
            return None  # dates drive validation and identify no one alone

    if key and _norm(key) in SAFE_KEYS:
        return None

    if key:
        for rx, kind in _HIGH_KEY_PATTERNS:
            if rx.search(key):
                # A "phone" key holding something clearly not a phone is worth
                # flagging, but not worth silently rewriting.
                if kind is Kind.PHONE and isinstance(value, str) and not _PHONE_RE.match(value):
                    return kind, Confidence.REVIEW
                return kind, Confidence.HIGH

    if isinstance(value, str) and _UUID_RE.match(value):
        return Kind.UUID, Confidence.HIGH

    if key:
        for rx, kind in _REVIEW_KEY_PATTERNS:
            if rx.search(key):
                if kind is Kind.NAME and isinstance(value, str):
                    # Decide by the record the value sits in, not by string
                    # shape alone: a lookup row ({id, name, code}) holding
                    # "American Samoa" is a label, while a company row
                    # (companyName + parentCompanyId) holding "Lefflers
                    # Antiques" is a customer.
                    if has_company_signal(siblings):
                        return Kind.COMPANY, Confidence.HIGH
                    if _PERSON_NAME_RE.match(value) and has_person_signal(siblings):
                        return Kind.NAME, Confidence.HIGH
                    return Kind.NAME, Confidence.REVIEW
                if kind is Kind.TEXT and isinstance(value, str):
                    # Long free text is far more likely to carry real content.
                    conf = Confidence.HIGH if len(value) > 60 else Confidence.REVIEW
                    return kind, conf
                return kind, Confidence.REVIEW

    # Generic override slots carry whatever the record carries. Only treat them
    # as sensitive inside an object that is already a person/company record.
    if (
        key
        and _norm(key) in {"value", "defaultvalue", "overridevalue"}
        and isinstance(value, str)
        and (has_person_signal(siblings) or has_company_signal(siblings))
    ):
        if _PERSON_NAME_RE.match(value):
            return Kind.NAME, Confidence.HIGH
        if _STREET_RE.match(value) and len(value) < 80:
            return Kind.STREET, Confidence.HIGH

    if isinstance(value, str):
        if _PERSON_NAME_RE.match(value) and len(value) < 40:
            return Kind.NAME, Confidence.REVIEW  # never auto-rewritten
        if _STREET_RE.match(value) and len(value) < 80:
            return Kind.STREET, Confidence.REVIEW
    return None


# ---------------------------------------------------------------------------
# Substitution
# ---------------------------------------------------------------------------


def _digest(value: Any) -> int:
    return int(hashlib.sha256(f"{_SALT}:{value!r}".encode()).hexdigest()[:12], 16)


def _pick(seq, value: Any):
    return seq[_digest(value) % len(seq)]


def _sanitized_uuid(value: str) -> str:
    """A valid UUID carrying :data:`_UUID_MARK` in the version nibble.

    The mark is what makes UUID sanitization idempotent -- without it a
    sanitized UUID is indistinguishable from a real one and re-sanitizes.
    """
    h = hashlib.sha256(f"{_SALT}:{value}".encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{_UUID_MARK}{h[13:16]}-{h[16:20]}-{h[20:32]}"


def substitute(kind: Kind, value: Any) -> Any:
    """Deterministic replacement preserving *value*'s type and shape."""
    d = _digest(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if kind is Kind.COORDINATE:
            pool = _LONS if value < -90 or value > 90 else _LATS
            return _pick(pool, value)
        if kind is Kind.MONEY:
            return _pick(_MONEY, value)
        if kind is Kind.POSTCODE:
            return int(_pick(_ZIPS, value))
        return _pick(_INTS, value) if isinstance(value, int) else _pick(_MONEY, value)

    if not isinstance(value, str):
        return value

    if kind is Kind.EMAIL:
        return f"{_pick(_FIRST, value).lower()}.{_pick(_LAST, value).lower()}@example.com"
    if kind is Kind.NAME:
        return f"{_pick(_FIRST, value)} {_pick(_LAST, value + 'x')}"
    if kind is Kind.COMPANY:
        return f"{_pick(_COMPANY_HEAD, value)} {_pick(_COMPANY_TAIL, value + 'c')}"
    if kind is Kind.USERNAME:
        return f"{_pick(_FIRST, value).lower()}.{_pick(_LAST, value).lower()}"
    if kind is Kind.PHONE:
        return f"555-{d % 900 + 100:03d}-{d % 9000 + 1000:04d}"
    if kind is Kind.STREET:
        return f"{d % 8999 + 100} {_pick(_STREETS, value)}"
    if kind is Kind.CITY:
        return _pick(_CITIES, value)
    if kind is Kind.POSTCODE:
        return _pick(_ZIPS, value)
    if kind is Kind.TRACKING:
        return f"1Z{d % 10**14:014d}"
    if kind is Kind.GOVID:
        return f"XXX-XX-{d % 9000 + 1000:04d}"
    if kind is Kind.ACCOUNT:
        return f"****{d % 9000 + 1000:04d}"
    if kind is Kind.SECRET:
        # Preserve the shape the model may validate against: a UUID-typed
        # field must still receive a UUID, an email-typed one an email.
        if _UUID_RE.match(value):
            return _sanitized_uuid(value)
        if _EMAIL_RE.match(value):
            return f"{_pick(_FIRST, value).lower()}.{_pick(_LAST, value).lower()}@example.com"
        return "REDACTED"
    if kind is Kind.UUID:
        return _sanitized_uuid(value)
    if kind is Kind.TEXT:
        return f"sanitized text {d % 1000:03d}"
    return f"sanitized-{d % 10000:04d}"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Detection:
    """One sensitive value found at one path."""

    path: str
    key: str | None
    kind: Kind
    confidence: Confidence
    original: Any
    replacement: Any = None

    @property
    def rewritten(self) -> bool:
        return self.confidence is Confidence.HIGH

    def render(self) -> str:
        if self.rewritten:
            return f"{self.path}: {self.original!r} -> {self.replacement!r}  [{self.kind.value}]"
        return f"{self.path}: {self.original!r}  [{self.kind.value}, needs review]"


@dataclass
class SanitizeReport:
    """What sanitization changed and what still needs an operator decision."""

    detections: list[Detection] = field(default_factory=list)
    #: Hash of the raw payload as received. Never committed; recorded for provenance.
    live_sha256: str | None = None
    #: Hash of the sanitized payload actually written to disk.
    sanitized_sha256: str | None = None

    @property
    def changes(self) -> list[Detection]:
        return [d for d in self.detections if d.rewritten]

    @property
    def review(self) -> list[Detection]:
        return [d for d in self.detections if not d.rewritten]

    @property
    def changed_count(self) -> int:
        return len(self.changes)

    @property
    def was_sanitized(self) -> bool:
        return bool(self.changes)

    @property
    def needs_review(self) -> bool:
        return bool(self.review)

    def mapping(self) -> dict[str, Any]:
        """``{original: replacement}`` -- proof that equal values map equally."""
        return {repr(d.original): d.replacement for d in self.changes}

    def diff_lines(self, limit: int = 40) -> list[str]:
        out = [d.render() for d in self.changes[:limit]]
        if self.changed_count > limit:
            out.append(f"... and {self.changed_count - limit} more")
        if self.review:
            out.append(f"-- {len(self.review)} value(s) flagged for operator review --")
            out.extend(d.render() for d in self.review[:limit])
        return out


def payload_sha256(payload: Any) -> str:
    """Stable hash of a JSON-able payload (sorted keys, compact separators)."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


# ---------------------------------------------------------------------------
# Walk
# ---------------------------------------------------------------------------


def _walk(
    node: Any,
    path: str,
    key: str | None,
    report: SanitizeReport,
    rewrite: bool,
    siblings: dict | None = None,
) -> Any:
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            child_path = f"{path}.{k}" if path else k
            # An override wrapper's leaves are classified under the parent key,
            # which is the only place the field's identity appears.
            if is_override_wrapper(v):
                out[k] = {
                    slot: _walk(sv, f"{child_path}.{slot}", k, report, rewrite, node)
                    for slot, sv in v.items()
                }
            else:
                out[k] = _walk(v, child_path, k, report, rewrite, node)
        return out
    if isinstance(node, list):
        # List cardinality is preserved: every element is visited, none dropped.
        return [
            _walk(v, f"{path}[{i}]", key, report, rewrite, siblings)
            for i, v in enumerate(node)
        ]

    hit = classify(key, node, path, siblings)
    if hit is None:
        return node
    kind, confidence = hit

    if confidence is Confidence.HIGH and rewrite:
        new = substitute(kind, node)
        if new != node:
            report.detections.append(Detection(path, key, kind, confidence, node, new))
            return new
        return node

    report.detections.append(Detection(path, key, kind, confidence, node))
    return node


def sanitize(payload: Any) -> tuple[Any, SanitizeReport]:
    """Return ``(sanitized_payload, report)``.

    Only :attr:`Confidence.HIGH` detections are rewritten. Ambiguous values are
    reported for operator review and left untouched -- silently rewriting them
    would corrupt reference data and destroy trust in the diff.
    """
    report = SanitizeReport(live_sha256=payload_sha256(payload))
    cleaned = _walk(payload, "", None, report, rewrite=True)
    report.sanitized_sha256 = payload_sha256(cleaned)
    return cleaned, report


def audit(payload: Any) -> SanitizeReport:
    """Detect without rewriting -- used by the repository-wide safety test."""
    report = SanitizeReport(live_sha256=payload_sha256(payload))
    _walk(payload, "", None, report, rewrite=False)
    report.sanitized_sha256 = report.live_sha256
    return report
