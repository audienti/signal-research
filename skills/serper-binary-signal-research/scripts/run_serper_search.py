#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


BASE_URL = "https://google.serper.dev"
CONFIG_PATH = Path.home() / ".codex" / "config.toml"
ALLOWED_ENDPOINTS = {"search", "news"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Serper search jobs.")
    parser.add_argument("--jobs", help="Path to a JSON file containing a list of search jobs.")
    parser.add_argument("--query", help="Single query to run when --jobs is omitted.")
    parser.add_argument("--label", help="Optional label for a single-query run.")
    parser.add_argument("--type", default="search", help="Endpoint type: search or news.")
    parser.add_argument("--gl", default="us", help="Country code passed to Serper.")
    parser.add_argument("--hl", default="en", help="Language code passed to Serper.")
    parser.add_argument("--tbs", help="Optional recency helper, for example d, w, m, y, or qdr:m.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results to keep per job.")
    parser.add_argument(
        "--page-count-limit",
        type=int,
        default=1,
        help="Maximum number of Serper pages to fetch per job.",
    )
    parser.add_argument("--output", help="Optional path to write JSON output.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print normalized jobs without making API calls.",
    )
    args = parser.parse_args()
    if not args.jobs and not args.query:
        parser.error("Provide either --jobs or --query.")
    return args


def load_jobs_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.jobs:
        payload = json.loads(Path(args.jobs).read_text())
        if not isinstance(payload, list):
            raise ValueError("--jobs must point to a JSON array.")
        raw_jobs = payload
    else:
        raw_jobs = [
            {
                "id": "job-1",
                "label": args.label or "single_query",
                "query": args.query,
                "type": args.type,
                "gl": args.gl,
                "hl": args.hl,
                "tbs": args.tbs,
                "limit": args.limit,
                "page_count_limit": args.page_count_limit,
            }
        ]
    normalized = []
    for index, raw in enumerate(raw_jobs, start=1):
        normalized.append(
            normalize_job(
                raw,
                index=index,
                default_type=args.type,
                default_gl=args.gl,
                default_hl=args.hl,
                default_tbs=args.tbs,
                default_limit=args.limit,
                default_page_count_limit=args.page_count_limit,
            )
        )
    return normalized


def normalize_job(
    raw: dict[str, Any],
    *,
    index: int,
    default_type: str,
    default_gl: str,
    default_hl: str,
    default_tbs: str | None,
    default_limit: int,
    default_page_count_limit: int,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Job {index} is not a JSON object.")

    query = str(raw.get("q") or raw.get("query") or "").strip()
    if not query:
        raise ValueError(f"Job {index} is missing `query`.")

    endpoint = str(raw.get("endpoint") or raw.get("type") or default_type or "search").strip().lower()
    if endpoint not in ALLOWED_ENDPOINTS:
        raise ValueError(f"Job {index} has unsupported endpoint `{endpoint}`.")

    page_count_limit = int(raw.get("page_count_limit") or raw.get("pageCountLimit") or default_page_count_limit or 1)
    limit = int(raw.get("limit") or default_limit or 10)

    if page_count_limit <= 0:
        raise ValueError(f"Job {index} has invalid page_count_limit `{page_count_limit}`.")
    if limit <= 0:
        raise ValueError(f"Job {index} has invalid limit `{limit}`.")

    tbs = normalize_tbs(raw.get("tbs") or default_tbs)

    return {
        "id": str(raw.get("id") or f"job-{index}"),
        "label": str(raw.get("label") or raw.get("family") or f"job_{index}"),
        "query": query,
        "endpoint": endpoint,
        "gl": str(raw.get("gl") or default_gl or "us"),
        "hl": str(raw.get("hl") or default_hl or "en"),
        "tbs": tbs,
        "limit": limit,
        "pageCountLimit": page_count_limit,
        "metadata": raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {},
    }


def normalize_tbs(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("qdr:"):
        return text
    if text in {"h", "d", "w", "m", "y"}:
        return f"qdr:{text}"
    return text


def load_api_key() -> tuple[str | None, str]:
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if key:
        return key, "env"
    if tomllib is None or not CONFIG_PATH.is_file():
        return None, "missing"
    try:
        payload = tomllib.loads(CONFIG_PATH.read_text())
    except Exception:
        return None, "config_unreadable"
    key = find_config_key(payload)
    if key:
        return key, "config"
    return None, "missing"


def find_config_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() == "serper_api_key" and isinstance(child, str) and child.strip():
                return child.strip()
            found = find_config_key(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_config_key(child)
            if found:
                return found
    return None


def build_body(job: dict[str, Any], page: int) -> dict[str, Any]:
    body = {
        "q": job["query"],
        "gl": job["gl"],
        "hl": job["hl"],
        "page": page,
    }
    if job["tbs"]:
        body["tbs"] = job["tbs"]
    return body


def request_json(path: str, body: dict[str, Any], api_key: str) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Serper HTTP {exc.code} for {path}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Serper request failed for {path}: {exc.reason}") from exc
    return json.loads(text)


def extract_results(response: dict[str, Any], endpoint: str) -> list[dict[str, Any]]:
    items = response.get("organic") if endpoint == "search" else response.get("news")
    if not isinstance(items, list):
        return []

    extracted: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        extracted.append(
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "date": item.get("date"),
                "source": item.get("source"),
                "position": item.get("position"),
            }
        )
    return extracted


def run_job(job: dict[str, Any], api_key: str) -> dict[str, Any]:
    path = "/search" if job["endpoint"] == "search" else "/news"
    results: list[dict[str, Any]] = []
    pages_fetched = 0
    page_summaries: list[dict[str, Any]] = []
    credits_used = 0

    for page in range(1, job["pageCountLimit"] + 1):
        body = build_body(job, page)
        response = request_json(path, body, api_key)
        page_results = extract_results(response, job["endpoint"])
        page_summaries.append(
            {
                "page": page,
                "resultCount": len(page_results),
                "searchParameters": response.get("searchParameters"),
                "credits": response.get("credits"),
            }
        )
        credits_used += int(response.get("credits") or 0)
        pages_fetched += 1
        results.extend(page_results)
        if len(results) >= job["limit"]:
            results = results[: job["limit"]]
            break
        if len(page_results) < 10:
            break

    return {
        **job,
        "pagesFetched": pages_fetched,
        "resultCount": len(results),
        "creditsUsed": credits_used,
        "pageSummaries": page_summaries,
        "results": results,
    }


def emit_output(payload: dict[str, Any], output_path: str | None) -> None:
    rendered = json.dumps(payload, indent=2)
    if output_path:
        Path(output_path).write_text(rendered)
    print(rendered)


def main() -> None:
    args = parse_args()
    jobs = load_jobs_from_args(args)

    if args.dry_run:
        emit_output(
            {
                "runner": "run_serper_search.py",
                "mode": "dry_run",
                "jobs": jobs,
            },
            args.output,
        )
        return

    api_key, auth_source = load_api_key()
    if not api_key:
        print(
            "Missing SERPER_API_KEY. Set it in the environment or add SERPER_API_KEY to ~/.codex/config.toml.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    ran_at = datetime.now(timezone.utc).isoformat()
    job_runs = [run_job(job, api_key) for job in jobs]
    emit_output(
        {
            "runner": "run_serper_search.py",
            "baseUrl": BASE_URL,
            "ranAt": ran_at,
            "authSource": auth_source,
            "jobs": job_runs,
        },
        args.output,
    )


if __name__ == "__main__":
    main()
