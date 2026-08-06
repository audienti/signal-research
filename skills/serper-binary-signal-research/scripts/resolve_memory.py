#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


SKILL_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = SKILL_DIR / "memory"
OFFER_DIR = MEMORY_DIR / "offers"
SIGNAL_DIR = MEMORY_DIR / "signals"
OFFER_SIGNAL_DIR = MEMORY_DIR / "offer_signals"
SEED_PACK_DIR = MEMORY_DIR / "seed_packs"
RUN_LEDGER_DIR = MEMORY_DIR / "run_ledgers"
TEMPLATE_DIR = MEMORY_DIR / "templates"
OFFER_TEMPLATE = TEMPLATE_DIR / "offer-note-template.md"
SIGNAL_TEMPLATE = TEMPLATE_DIR / "signal-note-template.md"
OFFER_SIGNAL_TEMPLATE = TEMPLATE_DIR / "offer-signal-note-template.md"
SEED_PACK_TEMPLATE = TEMPLATE_DIR / "seed-pack-template.md"
RUN_LEDGER_TEMPLATE = TEMPLATE_DIR / "run-ledger-template.md"


def normalize_host(host: str) -> str:
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def path_slug(path: str) -> str:
    trimmed = path.strip().strip("/")
    if not trimmed:
        return ""
    return trimmed.replace("/", "--")


def slugify(text: str, *, max_length: int = 96) -> str:
    cleaned = text.lower().strip()
    chars: list[str] = []
    last_was_dash = False
    for char in cleaned:
        if char.isalnum():
            chars.append(char)
            last_was_dash = False
            continue
        if not last_was_dash:
            chars.append("-")
            last_was_dash = True
    slug = "".join(chars).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug or "general"


def parse_offer(offer: str) -> tuple[str, str, str]:
    candidate = offer.strip()
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    if parsed.netloc:
        host = normalize_host(parsed.netloc)
        path = parsed.path or "/"
        host_key = host.replace(".", "-")
        path_key = path_slug(path)
        offer_key = f"{host_key}__{path_key}" if path_key else host_key
        return "url", host, offer_key
    offer_key = slugify(candidate, max_length=80)
    return "text", candidate, offer_key


def write_from_template(target: Path, template: Path, title: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    content = template.read_text()
    content = content.replace("# example-offer-signal", f"# {title}")
    content = content.replace("# example-signal", f"# {title}")
    content = content.replace("# example-offer", f"# {title}")
    target.write_text(content)


def resolve_paths(offer: str, signal: str) -> dict:
    offer_kind, normalized_offer, offer_key = parse_offer(offer)
    signal_key = slugify(signal, max_length=96)
    combined_key = f"{offer_key}__{signal_key}"

    offer_note = OFFER_DIR / f"{offer_key}.md"
    signal_note = SIGNAL_DIR / f"{signal_key}.md"
    offer_signal_note = OFFER_SIGNAL_DIR / f"{combined_key}.md"
    seed_pack_note = SEED_PACK_DIR / f"{combined_key}.md"
    run_ledger_note = RUN_LEDGER_DIR / f"{combined_key}.md"

    return {
        "input_offer": offer,
        "input_signal": signal,
        "offer_kind": offer_kind,
        "normalized_offer": normalized_offer,
        "offer_key": offer_key,
        "signal_key": signal_key,
        "offer_signal_key": combined_key,
        "offer_note": str(offer_note),
        "signal_note": str(signal_note),
        "offer_signal_note": str(offer_signal_note),
        "seed_pack_note": str(seed_pack_note),
        "run_ledger_note": str(run_ledger_note),
        "offer_exists": offer_note.exists(),
        "signal_exists": signal_note.exists(),
        "offer_signal_exists": offer_signal_note.exists(),
        "seed_pack_exists": seed_pack_note.exists(),
        "run_ledger_exists": run_ledger_note.exists(),
    }


def scaffold(paths: dict) -> dict:
    created = []

    offer_note = Path(paths["offer_note"])
    if not offer_note.exists():
        write_from_template(offer_note, OFFER_TEMPLATE, paths["offer_key"])
        created.append(str(offer_note))
        paths["offer_exists"] = True

    signal_note = Path(paths["signal_note"])
    if not signal_note.exists():
        write_from_template(signal_note, SIGNAL_TEMPLATE, paths["signal_key"])
        created.append(str(signal_note))
        paths["signal_exists"] = True

    offer_signal_note = Path(paths["offer_signal_note"])
    if not offer_signal_note.exists():
        write_from_template(offer_signal_note, OFFER_SIGNAL_TEMPLATE, paths["offer_signal_key"])
        created.append(str(offer_signal_note))
        paths["offer_signal_exists"] = True

    seed_pack_note = Path(paths["seed_pack_note"])
    if not seed_pack_note.exists():
        write_from_template(seed_pack_note, SEED_PACK_TEMPLATE, paths["offer_signal_key"])
        created.append(str(seed_pack_note))
        paths["seed_pack_exists"] = True

    run_ledger_note = Path(paths["run_ledger_note"])
    if not run_ledger_note.exists():
        write_from_template(run_ledger_note, RUN_LEDGER_TEMPLATE, paths["offer_signal_key"])
        created.append(str(run_ledger_note))
        paths["run_ledger_exists"] = True

    paths["created"] = created
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve and optionally scaffold memory notes for an offer plus signal pair."
    )
    parser.add_argument("--offer", required=True, help="Offer URL or offer label.")
    parser.add_argument("--signal", required=True, help="Binary signal question.")
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Create missing note files from templates.",
    )
    args = parser.parse_args()

    paths = resolve_paths(args.offer, args.signal)
    if args.scaffold:
        paths = scaffold(paths)
    else:
        paths["created"] = []

    print(json.dumps(paths, indent=2))


if __name__ == "__main__":
    main()
