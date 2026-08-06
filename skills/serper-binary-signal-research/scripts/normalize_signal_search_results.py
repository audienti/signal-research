#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PUBLISHER_DOMAINS = {
    "businesswire.com",
    "globenewswire.com",
    "prnewswire.com",
    "deadline.com",
    "finance.yahoo.com",
    "yahoo.com",
    "jdsupra.com",
    "marketscreener.com",
    "streetinsider.com",
    "businessinsider.com",
    "crunchbase.com",
    "pitchbook.com",
    "marketwatch.com",
    "benzinga.com",
    "seekingalpha.com",
    "bloomberg.com",
    "nytimes.com",
    "reuters.com",
    "spacenews.com",
    "variety.com",
}
OFFICIAL_SITE_RE = re.compile(r"\bofficial site\b", re.IGNORECASE)
LINKEDIN_RESOLUTION_RE = re.compile(r"site:linkedin\.com/company", re.IGNORECASE)
AFTER_DATE_RE = re.compile(r"after:(\d{4}-\d{2}-\d{2})")
ABSOLUTE_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)
RELATIVE_DATE_RE = re.compile(
    r"\b(\d+)\s+(hour|day|week|month|year)s?\s+ago\b",
    re.IGNORECASE,
)
YESTERDAY_RE = re.compile(r"\byesterday\b", re.IGNORECASE)
TODAY_RE = re.compile(r"\btoday\b", re.IGNORECASE)
LINKEDIN_COMPANY_RE = re.compile(r"linkedin\.com/company/[^/?#]+", re.IGNORECASE)
NON_COMPANY_POSSESSIVE_RE = re.compile(
    r"[’']s\b.*\b(?:firm|team|office|family|fund|vc|venture|capital)\b",
    re.IGNORECASE,
)
PRIMARY_TAIL_RE = re.compile(
    r"\b(?:expands?|announces?|sets?|plans?|moves?|awards?|secures?|wins?|launches?|opens?)\b.*$",
    re.IGNORECASE,
)
SECONDARY_TAIL_RE = re.compile(
    r"\bto\s+(?:transform|create|house|power|accelerate|expand|support|grow|scale)\b.*$",
    re.IGNORECASE,
)

MA_PRIMARY_PATTERNS = [
    re.compile(
        r"(?P<primary>.+?)\s+(?:to\s+)?(?:acquire|acquires|acquired|buy|buys|bought|merges with|merge with|completes acquisition of|announces acquisition of|closes acquisition of)\s+(?P<secondary>.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<secondary>.+?)\s+acquired by\s+(?P<primary>.+)",
        re.IGNORECASE,
    ),
]
LEADERSHIP_PATTERNS = [
    re.compile(
        r"(?P<company>.+?)\s+(?:appoints|appointed|names|named|hires|hired|promotes|promoted)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:at|for|to)\s+(?P<company>[A-Z0-9][A-Za-z0-9&'().,\- ]{1,100})$",
        re.IGNORECASE,
    ),
]
FUNDING_PATTERNS = [
    re.compile(
        r"(?P<company>.+?)\s+(?:raises|raised|secures|secured|announces|announced|opens|opened|expands|expanded|launches|launched)\b",
        re.IGNORECASE,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize Serper search runs into ranked company targets."
    )
    parser.add_argument("--input", help="Path to Serper run JSON. Reads stdin when omitted.")
    parser.add_argument(
        "--archetype",
        default="generic_binary_signal",
        help="Signal archetype, for example ma_rationalization.",
    )
    parser.add_argument(
        "--window-start",
        help="Optional absolute lower-bound date in YYYY-MM-DD format.",
    )
    parser.add_argument("--output", help="Optional path to write JSON output.")
    return parser.parse_args()


def load_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text() if path else sys.stdin.read()
    payload = json.loads(raw)
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"jobs": payload}
    raise ValueError("Expected a JSON object or array.")


def parse_run_anchor(payload: dict[str, Any]) -> datetime:
    raw = payload.get("ranAt")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def parse_window_start(
    explicit_value: str | None,
    payload: dict[str, Any],
) -> date | None:
    if explicit_value:
        return date.fromisoformat(explicit_value)
    starts = []
    for job in payload.get("jobs", []):
        query = str(job.get("query") or "")
        for match in AFTER_DATE_RE.findall(query):
            try:
                starts.append(date.fromisoformat(match))
            except ValueError:
                continue
    return min(starts) if starts else None


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_link(link: str) -> str:
    parsed = urlparse(link)
    if not parsed.scheme:
        return link
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def domain_from_link(link: str) -> str | None:
    parsed = urlparse(link)
    host = parsed.netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def source_type_for(link: str, domain: str | None) -> str:
    if not domain:
        return "unknown"
    if "linkedin.com" in domain:
        return "linkedin_company" if LINKEDIN_COMPANY_RE.search(link) else "linkedin_other"
    if domain in PUBLISHER_DOMAINS:
        return "publisher"
    return "company_site"


def parse_observed_date(result: dict[str, Any], anchor: datetime) -> str | None:
    candidates = [
        clean_text(result.get("date")),
        clean_text(result.get("snippet")),
        clean_text(result.get("title")),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        absolute = ABSOLUTE_DATE_RE.search(candidate)
        if absolute:
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    return datetime.strptime(absolute.group(0), fmt).date().isoformat()
                except ValueError:
                    continue
        relative = RELATIVE_DATE_RE.search(candidate)
        if relative:
            amount = int(relative.group(1))
            unit = relative.group(2).lower()
            if unit == "hour":
                return (anchor - timedelta(hours=amount)).date().isoformat()
            if unit == "day":
                return (anchor - timedelta(days=amount)).date().isoformat()
            if unit == "week":
                return (anchor - timedelta(weeks=amount)).date().isoformat()
            if unit == "month":
                return (anchor - timedelta(days=30 * amount)).date().isoformat()
            if unit == "year":
                return (anchor - timedelta(days=365 * amount)).date().isoformat()
        if YESTERDAY_RE.search(candidate):
            return (anchor - timedelta(days=1)).date().isoformat()
        if TODAY_RE.search(candidate):
            return anchor.date().isoformat()
    return None


def strip_title_source(text: str) -> str:
    cleaned = clean_text(text)
    for separator in (" | ", " - "):
        parts = cleaned.split(separator)
        if len(parts) > 1:
            return parts[0].strip()
    return cleaned


def extract_quoted_company_names(query: str) -> list[str]:
    return [clean_company_name(match) for match in re.findall(r'"([^"]+)"', query) if clean_company_name(match)]


def clean_company_name(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b(?:official site|linkedin)\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"'s\s+.+$", "", text)
    text = re.sub(r"[’']s\s+.+$", "", text)
    text = re.sub(r",\s+.+$", "", text)
    text = re.sub(SECONDARY_TAIL_RE, "", text)
    text = re.sub(r"^(?:remaining|all|the)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(?:portfolio|assets|asset|business|operations|unit|division|platform)\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"'s\s+$", "", text)
    text = text.strip(" -|,:;()[]{}\"'")
    return text


def canonical_company_key(name: str) -> str:
    lowered = clean_company_name(name).lower()
    lowered = re.sub(
        r"\b(?:inc|incorporated|corp|corporation|company|co|limited|ltd|llc|plc|group|holdings?)\b",
        "",
        lowered,
    )
    lowered = re.sub(r"[^a-z0-9]+", "", lowered)
    return lowered


def normalize_primary_company_name(value: str) -> str:
    text = clean_text(value)
    if NON_COMPANY_POSSESSIVE_RE.search(text):
        return ""
    text = re.sub(PRIMARY_TAIL_RE, "", text)
    text = re.sub(r",\s+.+$", "", text)
    text = clean_company_name(text)
    return text


def looks_like_official_domain(
    company: str,
    domain: str | None,
    source_type: str,
    match_kind: str,
    source: str | None,
) -> bool:
    if not domain or source_type != "company_site":
        return False
    if match_kind == "official_site_resolution":
        return True
    company_key = canonical_company_key(company)
    domain_stem = domain.split(".", 1)[0]
    domain_key = re.sub(r"[^a-z0-9]+", "", domain_stem.lower())
    source_key = canonical_company_key(source or "")
    if domain_key and (domain_key in company_key or company_key in domain_key):
        return True
    if source_key and (source_key in company_key or company_key in source_key):
        return True
    return False


def extract_candidates_for_result(result: dict[str, Any], archetype: str) -> list[dict[str, Any]]:
    text = strip_title_source(result["title"])
    query = result["query"]
    candidates: list[dict[str, Any]] = []

    if LINKEDIN_RESOLUTION_RE.search(query):
        for name in extract_quoted_company_names(query):
            candidates.append(
                {
                    "company": name,
                    "matchKind": "linkedin_resolution",
                    "relatedCompany": None,
                }
            )
        return candidates

    if OFFICIAL_SITE_RE.search(query):
        for name in extract_quoted_company_names(query):
            candidates.append(
                {
                    "company": name,
                    "matchKind": "official_site_resolution",
                    "relatedCompany": None,
                }
            )
        return candidates

    if archetype == "ma_rationalization":
        for pattern in MA_PRIMARY_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            primary = normalize_primary_company_name(match.group("primary"))
            secondary = clean_company_name(match.group("secondary"))
            if primary:
                candidates.append(
                    {
                        "company": primary,
                        "matchKind": "ma_primary",
                        "relatedCompany": secondary or None,
                    }
                )
            break
        return candidates

    if archetype == "leadership_change":
        for pattern in LEADERSHIP_PATTERNS:
            match = pattern.search(text)
            if match and clean_company_name(match.group("company")):
                candidates.append(
                    {
                        "company": clean_company_name(match.group("company")),
                        "matchKind": "leadership_change",
                        "relatedCompany": None,
                    }
                )
                break
        return candidates

    if archetype == "funding_or_expansion":
        for pattern in FUNDING_PATTERNS:
            match = pattern.search(text)
            if match and clean_company_name(match.group("company")):
                candidates.append(
                    {
                        "company": clean_company_name(match.group("company")),
                        "matchKind": "funding_or_expansion",
                        "relatedCompany": None,
                    }
                )
                break
        return candidates

    for name in extract_quoted_company_names(query):
        candidates.append(
            {
                "company": name,
                "matchKind": "query_resolution",
                "relatedCompany": None,
            }
        )
    return candidates


def flatten_results(payload: dict[str, Any], anchor: datetime) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for job in payload.get("jobs", []):
        query = clean_text(job.get("query"))
        endpoint = clean_text(job.get("endpoint") or job.get("type") or "search") or "search"
        for item in job.get("results", []):
            if not isinstance(item, dict):
                continue
            link = normalize_link(clean_text(item.get("link")))
            domain = domain_from_link(link) if link else None
            flattened.append(
                {
                    "jobId": clean_text(job.get("id")) or None,
                    "jobLabel": clean_text(job.get("label")) or None,
                    "query": query,
                    "endpoint": endpoint,
                    "title": clean_text(item.get("title")),
                    "link": link,
                    "snippet": clean_text(item.get("snippet")),
                    "dateText": clean_text(item.get("date")) or None,
                    "observedDate": parse_observed_date(item, anchor),
                    "domain": domain,
                    "source": clean_text(item.get("source")) or None,
                    "position": item.get("position"),
                    "sourceType": source_type_for(link, domain),
                }
            )
    return flattened


def dedupe_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for result in results:
        key = result["link"] or f'{result["title"]}|{result["query"]}'
        existing = deduped.get(key)
        if not existing:
            deduped[key] = result
            continue
        if result["observedDate"] and not existing["observedDate"]:
            deduped[key] = result
    return list(deduped.values())


def build_company_groups(
    results: list[dict[str, Any]],
    archetype: str,
) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for result in results:
        candidates = extract_candidates_for_result(result, archetype)
        for candidate in candidates:
            key = canonical_company_key(candidate["company"])
            if not key:
                continue
            group = groups.setdefault(
                key,
                {
                    "company": candidate["company"],
                    "companyKey": key,
                    "domain": None,
                    "linkedinUrl": None,
                    "matchKinds": Counter(),
                    "relatedCompanies": Counter(),
                    "evidence": [],
                    "observedDates": set(),
                },
            )
            if len(candidate["company"]) > len(group["company"]):
                group["company"] = candidate["company"]
            group["matchKinds"][candidate["matchKind"]] += 1
            if candidate["relatedCompany"]:
                group["relatedCompanies"][candidate["relatedCompany"]] += 1
            if result["observedDate"]:
                group["observedDates"].add(result["observedDate"])
            if looks_like_official_domain(
                candidate["company"],
                result["domain"],
                result["sourceType"],
                candidate["matchKind"],
                result["source"],
            ):
                group["domain"] = group["domain"] or result["domain"]
            if result["sourceType"] == "linkedin_company" and result["link"]:
                group["linkedinUrl"] = group["linkedinUrl"] or result["link"]
            group["evidence"].append(
                {
                    "title": result["title"],
                    "link": result["link"],
                    "snippet": result["snippet"],
                    "observedDate": result["observedDate"],
                    "dateText": result["dateText"],
                    "sourceType": result["sourceType"],
                    "query": result["query"],
                    "matchKind": candidate["matchKind"],
                }
            )
    return groups


def is_goodput_target(
    group: dict[str, Any],
    archetype: str,
    window_start: date | None,
) -> bool:
    signal_match = any(
        kind in group["matchKinds"]
        for kind in ("ma_primary", "leadership_change", "funding_or_expansion")
    )
    if archetype == "generic_binary_signal":
        signal_match = signal_match or any(
            kind in group["matchKinds"]
            for kind in ("official_site_resolution", "linkedin_resolution", "query_resolution")
        )
    if not signal_match:
        return False
    if not window_start:
        return True
    for observed in group["observedDates"]:
        if date.fromisoformat(observed) >= window_start:
            return True
    return False


def confidence_for(group: dict[str, Any], is_goodput: bool) -> str:
    evidence_count = len(group["evidence"])
    has_domain = bool(group["domain"])
    has_linkedin = bool(group["linkedinUrl"])
    has_date = bool(group["observedDates"])
    if is_goodput and evidence_count >= 2 and has_date and (has_domain or has_linkedin):
        return "high"
    if is_goodput and evidence_count >= 1 and has_date:
        return "moderate"
    if evidence_count >= 1:
        return "low"
    return "unknown"


def follow_up_jobs_for(group: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = []
    company = group["company"]
    if not group["domain"]:
        jobs.append(
            {
                "id": f"resolve-domain-{group['companyKey']}",
                "label": "company_resolution",
                "query": f'"{company}" official site',
                "type": "search",
                "limit": 5,
                "page_count_limit": 1,
            }
        )
    if not group["linkedinUrl"]:
        jobs.append(
            {
                "id": f"resolve-linkedin-{group['companyKey']}",
                "label": "linkedin_resolution",
                "query": f'site:linkedin.com/company "{company}"',
                "type": "search",
                "limit": 5,
                "page_count_limit": 1,
            }
        )
    return jobs


def primary_failure_mode(
    raw_results: int,
    unique_results: int,
    dated_evidence: int,
    candidate_count: int,
    goodput_count: int,
    publisher_only_ratio: float,
    enriched_count: int,
) -> str:
    if raw_results == 0:
        return "no_search_results"
    if unique_results == 0:
        return "no_unique_results"
    if dated_evidence == 0:
        return "no_dated_evidence"
    if candidate_count == 0:
        return "no_named_companies"
    if goodput_count == 0:
        return "publisher_noise" if publisher_only_ratio >= 0.7 else "weak_signal_match"
    if enriched_count < goodput_count:
        return "enrichment_gap"
    return "goodput_targets_found"


def build_run_ledger(
    payload: dict[str, Any],
    archetype: str,
    summary: dict[str, Any],
) -> dict[str, str]:
    anchor = parse_run_anchor(payload).date().isoformat()
    next_move = (
        "run resolution follow-ups"
        if summary["goodputTargets"] > summary["enrichedTargets"]
        else "tighten source mix"
    )
    header = (
        "| date | archetype | query_count | seed_count | raw_results | dated_evidence | "
        "candidate_companies | goodput_targets | enriched_targets | primary_failure_mode | next_tuning_move |"
    )
    divider = (
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"
    )
    row = (
        f"| {anchor} | {archetype} | {summary['queryCount']} | {summary['seedCount']} | "
        f"{summary['rawResults']} | {summary['datedEvidence']} | {summary['candidateCompanies']} | "
        f"{summary['goodputTargets']} | {summary['enrichedTargets']} | "
        f"{summary['primaryFailureMode']} | {next_move} |"
    )
    return {"header": header, "divider": divider, "row": row}


def render_output(payload: dict[str, Any], output_path: str | None) -> None:
    rendered = json.dumps(payload, indent=2)
    if output_path:
        Path(output_path).write_text(rendered)
    print(rendered)


def main() -> None:
    args = parse_args()
    payload = load_payload(args.input)
    anchor = parse_run_anchor(payload)
    window_start = parse_window_start(args.window_start, payload)
    raw_results = flatten_results(payload, anchor)
    unique_results = dedupe_results(raw_results)
    groups = build_company_groups(unique_results, args.archetype)

    publisher_result_count = sum(1 for result in unique_results if result["sourceType"] == "publisher")
    publisher_ratio = publisher_result_count / len(unique_results) if unique_results else 0.0

    ranked_targets = []
    follow_up_jobs = []
    for group in groups.values():
        goodput = is_goodput_target(group, args.archetype, window_start)
        confidence = confidence_for(group, goodput)
        ranked = {
            "company": group["company"],
            "companyKey": group["companyKey"],
            "domain": group["domain"],
            "linkedinUrl": group["linkedinUrl"],
            "relatedCompanies": [name for name, _count in group["relatedCompanies"].most_common(3)],
            "signalMatched": goodput,
            "confidence": confidence,
            "observedDates": sorted(group["observedDates"]),
            "matchKinds": dict(group["matchKinds"]),
            "evidence": sorted(
                group["evidence"],
                key=lambda item: (
                    item["observedDate"] or "",
                    item["matchKind"] != "ma_primary",
                    item["sourceType"] == "publisher",
                ),
                reverse=True,
            )[:3],
            "gaps": [
                gap
                for gap, missing in (
                    ("missing_domain", not group["domain"]),
                    ("missing_linkedin_url", not group["linkedinUrl"]),
                    ("missing_observed_date", not group["observedDates"]),
                )
                if missing
            ],
        }
        ranked_targets.append(ranked)
        if goodput and (not group["domain"] or not group["linkedinUrl"]):
            follow_up_jobs.extend(follow_up_jobs_for(group))

    ranked_targets.sort(
        key=lambda item: (
            item["signalMatched"],
            item["confidence"] == "high",
            item["confidence"] == "moderate",
            len(item["evidence"]),
        ),
        reverse=True,
    )

    summary = {
        "queryCount": len(payload.get("jobs", [])),
        "seedCount": len(unique_results),
        "rawResults": len(raw_results),
        "datedEvidence": sum(1 for result in unique_results if result["observedDate"]),
        "candidateCompanies": len(groups),
        "goodputTargets": sum(1 for target in ranked_targets if target["signalMatched"]),
        "enrichedTargets": sum(
            1
            for target in ranked_targets
            if target["signalMatched"] and (target["domain"] or target["linkedinUrl"])
        ),
    }
    summary["primaryFailureMode"] = primary_failure_mode(
        summary["rawResults"],
        summary["seedCount"],
        summary["datedEvidence"],
        summary["candidateCompanies"],
        summary["goodputTargets"],
        publisher_ratio,
        summary["enrichedTargets"],
    )

    render_output(
        {
            "archetype": args.archetype,
            "windowStart": window_start.isoformat() if window_start else None,
            "summary": summary,
            "targets": ranked_targets,
            "followUpJobs": follow_up_jobs,
            "runLedger": build_run_ledger(payload, args.archetype, summary),
        },
        args.output,
    )


if __name__ == "__main__":
    main()
