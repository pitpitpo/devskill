#!/usr/bin/env python3
"""req-ledger.py: Tamper-evident Requirements Traceability Ledger & Fail-Closed Completion Gate.

Prevents AI coding agents from dropping requirements, forgetting negative constraints,
or declaring premature victory on multi-detail tasks.

Usage:
  python3 scripts/req-ledger.py init <ledger.json> --title "Task Title"
  python3 scripts/req-ledger.py add <ledger.json> --id REQ-001 --category api --type functional \
      --description "..." --criteria "..." [--optional] [--protected] [--amend --reason "..."]
  python3 scripts/req-ledger.py freeze <ledger.json>
  python3 scripts/req-ledger.py recite <ledger.json>
  python3 scripts/req-ledger.py audit-prompt <ledger.json>
  python3 scripts/req-ledger.py verify <ledger.json> --id REQ-001 --files "a.py,b.py" \
      --command "pytest" --exit-code 0 --evidence "12 passed"
  python3 scripts/req-ledger.py gate <ledger.json> [--require-frozen]
  python3 scripts/req-ledger.py status <ledger.json> [--json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
VALID_TYPES = ("functional", "negative", "edge_case", "non_functional")
REQ_ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]{1,31}$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_spec_hash(requirements: list[dict[str, Any]]) -> str:
    """Compute canonical SHA-256 digest over immutable specification fields."""
    canonical = [
        {
            "id": r["id"],
            "category": r["category"],
            "type": r["type"],
            "description": r["description"],
            "criteria": r["criteria"],
            "optional": bool(r.get("optional", False)),
            "protected": bool(r.get("protected", False)),
        }
        for r in sorted(requirements, key=lambda item: item["id"])
    ]
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"req-ledger: ledger file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"req-ledger: invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("requirements"), list):
        raise SystemExit(f"req-ledger: malformed ledger structure in {path}")
    return data


def save_ledger(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = utc_now()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_integrity(data: dict[str, Any]) -> list[str]:
    """Verify schema invariants and tamper-evident spec_hash when frozen."""
    errors: list[str] = []
    reqs = data.get("requirements", [])
    seen_ids: set[str] = set()
    for idx, req in enumerate(reqs):
        if not isinstance(req, dict):
            errors.append(f"requirements[{idx}] is not an object")
            continue
        rid = req.get("id")
        if not isinstance(rid, str) or not REQ_ID_RE.match(rid):
            errors.append(f"requirements[{idx}] has invalid id: {rid!r}")
        elif rid in seen_ids:
            errors.append(f"duplicate requirement id: {rid}")
        else:
            seen_ids.add(rid)
        if req.get("type") not in VALID_TYPES:
            errors.append(f"{rid}: invalid type {req.get('type')!r} (expected one of {VALID_TYPES})")
        for field in ("category", "description", "criteria"):
            val = req.get(field)
            if not isinstance(val, str) or not val.strip():
                errors.append(f"{rid}: missing or empty '{field}'")
    if data.get("frozen"):
        recorded = data.get("spec_hash")
        actual = compute_spec_hash(reqs)
        if recorded != actual:
            errors.append(
                "SPEC TAMPERING DETECTED: requirements were modified or deleted after freeze "
                f"(recorded={str(recorded)[:12]}, actual={actual[:12]}). "
                "Use '--amend --reason ...' for authorized scope changes."
            )
    return errors


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    if path.exists() and not args.force:
        print(f"req-ledger: {path} already exists (pass --force to overwrite)", file=sys.stderr)
        return 1
    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "title": args.title.strip(),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "frozen": False,
        "spec_hash": None,
        "amendments": [],
        "requirements": [],
    }
    save_ledger(path, ledger)
    print(f"Initialized requirement ledger: {path}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load_ledger(path)

    if not REQ_ID_RE.match(args.id):
        print(f"req-ledger: invalid --id {args.id!r} (must match {REQ_ID_RE.pattern})", file=sys.stderr)
        return 2

    if data.get("frozen"):
        if not args.amend or not (args.reason and args.reason.strip()):
            print(
                "req-ledger: ledger is FROZEN. Pass --amend --reason '<authorized scope change>' "
                "to add a requirement after freeze.",
                file=sys.stderr,
            )
            return 1
        integrity_errs = check_integrity(data)
        if integrity_errs:
            for err in integrity_errs:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1

    if any(r.get("id") == args.id for r in data["requirements"]):
        print(f"req-ledger: duplicate requirement id '{args.id}'", file=sys.stderr)
        return 1

    entry: dict[str, Any] = {
        "id": args.id,
        "category": args.category.strip(),
        "type": args.type,
        "description": args.description.strip(),
        "criteria": args.criteria.strip(),
        "optional": bool(args.optional),
        "protected": bool(args.protected),
        "passes": False,
        "verification": None,
    }
    data["requirements"].append(entry)

    if data.get("frozen"):
        data["spec_hash"] = compute_spec_hash(data["requirements"])
        data.setdefault("amendments", []).append(
            {
                "timestamp": utc_now(),
                "action": f"add:{args.id}",
                "reason": args.reason.strip(),
                "new_spec_hash": data["spec_hash"],
            }
        )

    save_ledger(path, data)
    print(f"Added {args.id} [{args.type}] ({'optional' if args.optional else 'required'})")
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load_ledger(path)
    reqs = data["requirements"]
    if not reqs:
        print("req-ledger: cannot freeze an empty ledger (add at least one requirement)", file=sys.stderr)
        return 1
    data["frozen"] = False  # Temporarily clear to validate schema before sealing
    errs = check_integrity(data)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    data["frozen"] = True
    data["spec_hash"] = compute_spec_hash(reqs)
    save_ledger(path, data)
    print(f"Frozen {len(reqs)} requirements (spec_hash={data['spec_hash'][:16]}...)")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load_ledger(path)
    errs = check_integrity(data)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.exit_code != 0:
        print(
            f"req-ledger: REFUSED to mark {args.id} passing with non-zero exit code ({args.exit_code})",
            file=sys.stderr,
        )
        return 1
    if not args.evidence or not args.evidence.strip():
        print(f"req-ledger: REFUSED to mark {args.id} passing without non-empty --evidence", file=sys.stderr)
        return 1
    if not args.command or not args.command.strip():
        print(f"req-ledger: REFUSED to mark {args.id} passing without --command", file=sys.stderr)
        return 1

    target = next((r for r in data["requirements"] if r.get("id") == args.id), None)
    if target is None:
        print(f"req-ledger: requirement '{args.id}' not found", file=sys.stderr)
        return 1

    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    target["passes"] = True
    target["verification"] = {
        "verified_at": utc_now(),
        "files": files,
        "command": args.command.strip(),
        "exit_code": args.exit_code,
        "evidence": args.evidence.strip(),
    }
    save_ledger(path, data)
    print(f"Verified {args.id} -> passes=true")
    return 0


def cmd_recite(args: argparse.Namespace) -> int:
    """Emit compact, high-attention recitation block for the tail of an agent context."""
    path = Path(args.ledger)
    data = load_ledger(path)
    errs = check_integrity(data)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    reqs = data["requirements"]
    required = [r for r in reqs if not r.get("optional")]
    passed_req = [r for r in required if r.get("passes")]
    open_req = [r for r in required if not r.get("passes")]
    open_neg = [r for r in open_req if r.get("type") == "negative"]

    print(f"=== REQUIREMENT RECITATION: {data.get('title', 'Untitled')} ===")
    print(
        f"Progress: {len(passed_req)}/{len(required)} required verified | "
        f"Frozen: {'YES' if data.get('frozen') else 'NO (run freeze before coding!)'}"
    )

    if open_neg:
        print("\n[ACTIVE NEGATIVE CONSTRAINTS - NEVER VIOLATE]:")
        for r in open_neg:
            print(f"  ! {r['id']}: {r['description']} | Proof: {r['criteria']}")

    if not open_req:
        print("\nAll required items verified. Run 'req-ledger.py gate' to confirm ship readiness.")
        return 0

    next_item = open_req[0]
    print("\n[NEXT REQUIREMENT TO COMPLETE]:")
    print(f"  -> {next_item['id']} [{next_item['type']}/{next_item['category']}]: {next_item['description']}")
    print(f"     Acceptance Criteria: {next_item['criteria']}")

    remaining_others = [r for r in open_req[1:] if r.get("type") != "negative"]
    if remaining_others:
        print(f"\n[REMAINING QUEUE ({len(remaining_others)})]:")
        for r in remaining_others[:10]:
            print(f"  - {r['id']} [{r['type']}]: {r['description']}")
        if len(remaining_others) > 10:
            print(f"  ... (+{len(remaining_others) - 10} more)")
    return 0


def cmd_audit_prompt(args: argparse.Namespace) -> int:
    """Emit Fresh-Context Read-Only Evaluator & SatisFix Deviation Elicitation prompt."""
    path = Path(args.ledger)
    data = load_ledger(path)
    errs = check_integrity(data)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    reqs = data["requirements"]
    print(f"=== FRESH-CONTEXT READ-ONLY AUDIT & SATISFIX DEVIATION CHECK: {data.get('title', 'Untitled')} ===")
    print("INSTRUCTIONS FOR EVALUATOR (Read-Only Context, Zero Write Tools):")
    print("1. Inspect ONLY `git diff`, actual executed test logs, and the frozen requirements below.")
    print("2. Objective-Aligned Deviation Elicitation (SatisFix, R-266):")
    print("   List EVERY place the implementation diverged from, approximated, simplified, or")
    print("   rationalized a shortcut compared to the exact wording of each requirement.")
    print("3. Spec Compliance Before Code Quality (R-248, R-265):")
    print("   Verify every negative/protected constraint and edge case directly against code lines.")
    print("")
    for r in reqs:
        tags = [r["type"]]
        if r.get("protected"):
            tags.append("USER-PROTECTED")
        if r.get("optional"):
            tags.append("optional")
        status = "PASS" if r.get("passes") else "OPEN"
        print(f"- [{status}] {r['id']} ({', '.join(tags)}): {r['description']}")
        print(f"  Acceptance Criteria: {r['criteria']}")
        ver = r.get("verification")
        if isinstance(ver, dict):
            print(
                f"  Claimed Proof: cmd=`{ver.get('command', '')}` exit={ver.get('exit_code')} "
                f"evidence=`{ver.get('evidence', '')}`"
            )
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    """Fail-closed completion gate. Exits 0 ONLY when 100% required items are verified with proof."""
    path = Path(args.ledger)
    data = load_ledger(path)
    errors = check_integrity(data)

    reqs = data.get("requirements", [])
    if not reqs:
        errors.append("Ledger contains zero requirements.")

    if args.require_frozen and not data.get("frozen"):
        errors.append("Ledger is NOT frozen (run 'req-ledger.py freeze' to lock specification integrity).")

    missing: list[dict[str, Any]] = []
    for r in reqs:
        is_optional = bool(r.get("optional", False))
        passes = bool(r.get("passes", False))
        ver = r.get("verification")
        valid_proof = (
            isinstance(ver, dict)
            and ver.get("exit_code") == 0
            and isinstance(ver.get("evidence"), str)
            and bool(ver["evidence"].strip())
            and isinstance(ver.get("command"), str)
            and bool(ver["command"].strip())
        )
        if passes and not valid_proof:
            errors.append(f"{r['id']}: marked passes=true but lacks valid verification proof (command/exit_code=0/evidence)")
        if not is_optional and (not passes or not valid_proof):
            missing.append(r)

    if errors or missing:
        print(f"FAIL: Requirement Completion Gate BLOCKED for '{data.get('title', path.name)}'", file=sys.stderr)
        for err in errors:
            print(f"  [INTEGRITY ERROR] {err}", file=sys.stderr)
        for r in missing:
            print(f"  [UNVERIFIED {r['type'].upper()}] {r['id']}: {r['description']}", file=sys.stderr)
        print(
            f"Summary: {len(missing)} required item(s) unverified, {len(errors)} integrity error(s).",
            file=sys.stderr,
        )
        return 1

    required_count = sum(1 for r in reqs if not r.get("optional"))
    optional_passed = sum(1 for r in reqs if r.get("optional") and r.get("passes"))
    print(
        f"PASS: Requirement Completion Gate cleared for '{data.get('title', path.name)}' "
        f"({required_count}/{required_count} required verified, {optional_passed} optional verified, "
        f"frozen={bool(data.get('frozen'))})."
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load_ledger(path)
    errs = check_integrity(data)
    reqs = data["requirements"]
    by_type: dict[str, dict[str, int]] = {t: {"passed": 0, "open": 0} for t in VALID_TYPES}
    for r in reqs:
        t = r.get("type", "functional")
        bucket = by_type.setdefault(t, {"passed": 0, "open": 0})
        bucket["passed" if r.get("passes") else "open"] += 1

    summary = {
        "title": data.get("title"),
        "frozen": bool(data.get("frozen")),
        "spec_hash": data.get("spec_hash"),
        "integrity_errors": errs,
        "total": len(reqs),
        "required_total": sum(1 for r in reqs if not r.get("optional")),
        "required_passed": sum(1 for r in reqs if not r.get("optional") and r.get("passes")),
        "by_type": by_type,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"{summary['title']} | required: {summary['required_passed']}/{summary['required_total']} "
            f"| frozen: {summary['frozen']} | errors: {len(errs)}"
        )
    return 0 if not errs else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tamper-evident Requirement Ledger & Completion Gate")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_init = sub.add_parser("init", help="Initialize a new requirements ledger JSON file")
    p_init.add_argument("ledger")
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="Add an atomic requirement to the ledger")
    p_add.add_argument("ledger")
    p_add.add_argument("--id", required=True)
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--type", choices=VALID_TYPES, default="functional")
    p_add.add_argument("--description", required=True)
    p_add.add_argument("--criteria", required=True)
    p_add.add_argument("--optional", action="store_true")
    p_add.add_argument("--protected", action="store_true")
    p_add.add_argument("--amend", action="store_true")
    p_add.add_argument("--reason", default="")
    p_add.set_defaults(func=cmd_add)

    p_freeze = sub.add_parser("freeze", help="Lock specification with a SHA-256 anti-tamper hash")
    p_freeze.add_argument("ledger")
    p_freeze.set_defaults(func=cmd_freeze)

    p_recite = sub.add_parser("recite", help="Print compact high-attention recitation of open requirements")
    p_recite.add_argument("ledger")
    p_recite.set_defaults(func=cmd_recite)

    p_audit = sub.add_parser(
        "audit-prompt",
        help="Emit Fresh-Context Read-Only Evaluator & SatisFix deviation elicitation checklist",
    )
    p_audit.add_argument("ledger")
    p_audit.set_defaults(func=cmd_audit_prompt)

    p_verify = sub.add_parser("verify", help="Record execution proof and mark requirement passing")
    p_verify.add_argument("ledger")
    p_verify.add_argument("--id", required=True)
    p_verify.add_argument("--files", default="")
    p_verify.add_argument("--command", required=True)
    p_verify.add_argument("--exit-code", type=int, required=True)
    p_verify.add_argument("--evidence", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_gate = sub.add_parser("gate", help="Fail-closed ship gate requiring 100% verified required items")
    p_gate.add_argument("ledger")
    p_gate.add_argument("--require-frozen", action="store_true")
    p_gate.set_defaults(func=cmd_gate)

    p_status = sub.add_parser("status", help="Show summary counts by requirement type")
    p_status.add_argument("ledger")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
