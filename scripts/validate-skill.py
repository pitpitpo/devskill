#!/usr/bin/env python3
"""validate-skill.py: Self-validator and deterministic index.json builder for DevSkill.

Usage:
  python3 scripts/validate-skill.py                # Validate everything (exit 0 on pass, 1 on errors)
  python3 scripts/validate-skill.py --write-index  # Regenerate index.json, then validate everything

Checks enforced:
  1. SKILL.md YAML frontmatter compliance with the Agent Skills open standard (agentskills.io).
  2. Zero hardcoded machine-specific paths (file:///, /home/agy, /Users/...).
  3. Zero broken internal relative Markdown links across all repository .md files.
  4. RULES.md structural integrity: contiguous R-001..R-NNN IDs, zero duplicates, unique titles.
  5. ROUTING.md citation integrity: every cited R-NNN rule exists in RULES.md.
  6. JSON / JSONC / Python AST syntax validation for configs and scripts.
  7. Deterministic index.json v2.0.0 parity (titles, line counts, tags, archetypes, configs, scripts).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

INDEX_VERSION = "2.2.0"
INDEX_UPDATED = "2026-11-19"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RULE_DEF_RE = re.compile(r"^\s*-\s+\*\*(R-(\d{3}))\s+\[([^\]]+)\]\*\*:")
RULE_REF_RE = re.compile(r"\bR-(\d{3})\b")
ARCHETYPE_HEADING_RE = re.compile(r"^###\s+Archetype\s+(\d+):\s+(.+?)\s*$")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BACKTICK_EMPTY_PAREN_RE = re.compile(r"\(\s*\)$")

# Construct forbidden path regexes dynamically so this validator file itself never triggers false hits.
FORBIDDEN_PATH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("file:// URI", re.compile(r"file:" + r"///")),
    ("hardcoded /home/agy path", re.compile(r"/" + r"home/agy\b")),
    ("hardcoded /Users/ home path", re.compile(r"(?<![A-Za-z0-9_])/" + r"Users/[A-Za-z0-9._-]+/")),
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache"}
SELF_TEST_FILES = {"scripts/validate-skill.py", "scripts/test_devskill.py"}


def iter_repo_files(root: Path) -> list[Path]:
    """Return sorted relative-ordered files in the repository, excluding ignored directories."""
    results: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        results.append(path)
    return sorted(results, key=lambda p: p.relative_to(root).as_posix())


def _unquote_yaml_scalar(raw: str) -> tuple[str, bool]:
    """Return (value, is_explicitly_quoted) for a single-line YAML scalar."""
    val = raw.strip()
    if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
        quote = val[0]
        inner = val[1:-1]
        if quote == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner, True
    return val, False


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse minimal YAML frontmatter from SKILL.md without external dependencies."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing opening YAML frontmatter delimiter '---'")

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        raise ValueError("Missing closing YAML frontmatter delimiter '---'")

    fm_lines = lines[1:end_idx]
    data: dict[str, Any] = {}
    current_map: str | None = None
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        if line.startswith("  ") and current_map is not None:
            sub = line.strip()
            if ":" not in sub:
                raise ValueError(f"Invalid nested frontmatter line under '{current_map}': {line}")
            k, v = sub.split(":", 1)
            val, quoted = _unquote_yaml_scalar(v)
            data[current_map][k.strip()] = (val, quoted)
            i += 1
            continue

        current_map = None
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, rest = line.split(":", 1)
        key = key.strip()
        rest_stripped = rest.strip()

        if rest_stripped == "":
            data[key] = {}
            current_map = key
            i += 1
        elif rest_stripped in (">", "|", ">-", "|-"):
            block_lines: list[str] = []
            i += 1
            while i < len(fm_lines) and (fm_lines[i].startswith("  ") or fm_lines[i].strip() == ""):
                block_lines.append(fm_lines[i].strip())
                i += 1
            joiner = " " if rest_stripped.startswith(">") else "\n"
            data[key] = joiner.join(part for part in block_lines if part).strip()
        else:
            val, _ = _unquote_yaml_scalar(rest_stripped)
            data[key] = val
            i += 1

    return data


def validate_skill_frontmatter(skill_md_path: Path) -> list[str]:
    """Validate SKILL.md frontmatter against the agentskills.io specification."""
    errors: list[str] = []
    if not skill_md_path.exists():
        return ["SKILL.md does not exist"]

    try:
        fm = parse_frontmatter(skill_md_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"SKILL.md frontmatter parse error: {exc}"]

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append("SKILL.md frontmatter missing required 'name'")
    else:
        if len(name) > 64:
            errors.append(f"SKILL.md 'name' exceeds 64 chars ({len(name)})")
        if not SKILL_NAME_RE.fullmatch(name):
            errors.append(f"SKILL.md 'name' must match ^[a-z0-9]+(?:-[a-z0-9]+)*$, got {name!r}")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("SKILL.md frontmatter missing required 'description'")
    elif len(desc) > 1024:
        errors.append(f"SKILL.md 'description' exceeds 1024 chars ({len(desc)})")

    metadata = fm.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            errors.append("SKILL.md 'metadata' must be a key-value map of strings")
        else:
            for k, entry in metadata.items():
                val, quoted = entry
                if not quoted and val.lower() in ("true", "false", "null", "~"):
                    errors.append(f"SKILL.md metadata.{k} must be a quoted string, not boolean/null ({val})")
                elif not quoted and re.fullmatch(r"-?\d+(?:\.\d+)?", val):
                    errors.append(f"SKILL.md metadata.{k} must be a quoted string, not numeric ({val})")
                elif not quoted and (val.startswith("[") or val.startswith("{")):
                    errors.append(f"SKILL.md metadata.{k} must be a string, not a list/object ({val})")

    return errors


def strip_code_from_markdown(text: str) -> str:
    """Remove fenced code blocks and inline code spans while keeping line structure."""
    out_lines: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in text.splitlines():
        stripped = line.lstrip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_match:
            token = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_char = token[0]
                fence_len = len(token)
                out_lines.append("")
                continue
            if token[0] == fence_char and len(token) >= fence_len and stripped[len(token):].strip() == "":
                in_fence = False
                out_lines.append("")
                continue
        if in_fence:
            out_lines.append("")
        else:
            # Replace inline code spans (`...`) with spaces to avoid false link matches
            cleaned = re.sub(r"`[^`]*`", " ", line)
            out_lines.append(cleaned)

    return "\n".join(out_lines)


def find_broken_links(root: Path, md_files: list[Path]) -> list[str]:
    """Verify every internal relative markdown link resolves to an existing repo path."""
    errors: list[str] = []
    root_resolved = root.resolve()

    for md_path in md_files:
        rel_doc = md_path.relative_to(root).as_posix()
        text = md_path.read_text(encoding="utf-8")
        cleaned = strip_code_from_markdown(text)

        for lineno, line in enumerate(cleaned.splitlines(), start=1):
            for match in MD_LINK_RE.finditer(line):
                raw_target = match.group(1).strip()
                if not raw_target:
                    continue
                if raw_target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                    continue
                if raw_target.startswith("file:"):
                    errors.append(f"{rel_doc}:{lineno}: forbidden file:// link {raw_target!r}")
                    continue

                target_no_frag = raw_target.split("#", 1)[0].split("?", 1)[0]
                if not target_no_frag:
                    continue

                if target_no_frag.startswith("/"):
                    resolved = (root_resolved / target_no_frag.lstrip("/")).resolve()
                else:
                    resolved = (md_path.parent / target_no_frag).resolve()

                try:
                    resolved.relative_to(root_resolved)
                except ValueError:
                    errors.append(f"{rel_doc}:{lineno}: link escapes repository root: {raw_target!r}")
                    continue

                if not resolved.exists():
                    errors.append(f"{rel_doc}:{lineno}: broken relative link -> {raw_target!r}")

    return errors


def find_forbidden_paths(root: Path, files: list[Path]) -> list[str]:
    """Ensure zero hardcoded machine-specific paths remain in the repository."""
    errors: list[str] = []
    scan_exts = {".md", ".json", ".yml", ".yaml", ".toml", ".sh", ".py"}

    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in SELF_TEST_FILES:
            continue
        if path.suffix not in scan_exts and path.name != "pr-wait":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, pattern in FORBIDDEN_PATH_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{rel}:{lineno}: contains {label}")

    return errors


def parse_rules(rules_md_path: Path) -> tuple[dict[str, str], list[str]]:
    """Parse RULES.md and validate contiguous numbering, unique IDs, and unique titles."""
    errors: list[str] = []
    rules: dict[str, str] = {}
    seen_titles: dict[str, str] = {}

    if not rules_md_path.exists():
        return {}, ["RULES.md does not exist"]

    for lineno, line in enumerate(rules_md_path.read_text(encoding="utf-8").splitlines(), start=1):
        m = RULE_DEF_RE.match(line)
        if not m:
            continue
        rule_id, _num_str, title = m.group(1), m.group(2), m.group(3).strip()
        if rule_id in rules:
            errors.append(f"RULES.md:{lineno}: duplicate rule ID {rule_id}")
        else:
            rules[rule_id] = title

        norm_title = re.sub(r"\s+", " ", title.lower())
        if norm_title in seen_titles:
            errors.append(
                f"RULES.md:{lineno}: duplicate rule title [{title}] "
                f"(already used by {seen_titles[norm_title]})"
            )
        else:
            seen_titles[norm_title] = rule_id

    if not rules:
        errors.append("RULES.md: parsed 0 rules")
        return rules, errors

    nums = sorted(int(rid.split("-")[1]) for rid in rules)
    expected = list(range(1, nums[-1] + 1))
    missing = sorted(set(expected) - set(nums))
    if missing:
        missing_str = ", ".join(f"R-{n:03d}" for n in missing)
        errors.append(f"RULES.md: non-contiguous rule numbering; missing {missing_str}")

    return rules, errors


def validate_routing_citations(routing_md_path: Path, rules: dict[str, str]) -> list[str]:
    """Ensure every R-NNN reference in ROUTING.md exists in RULES.md."""
    errors: list[str] = []
    if not routing_md_path.exists():
        return ["ROUTING.md does not exist"]

    text = strip_code_from_markdown(routing_md_path.read_text(encoding="utf-8"))
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in RULE_REF_RE.finditer(line):
            rid = f"R-{match.group(1)}"
            if rid not in rules:
                errors.append(f"ROUTING.md:{lineno}: cites unknown rule {rid}")

    return errors


def parse_archetypes(routing_md_path: Path) -> list[dict[str, Any]]:
    """Extract deterministic archetype metadata from ROUTING.md."""
    if not routing_md_path.exists():
        return []

    archetypes: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in routing_md_path.read_text(encoding="utf-8").splitlines():
        heading = ARCHETYPE_HEADING_RE.match(line)
        if heading:
            if current is not None:
                archetypes.append(current)
            current = {
                "id": int(heading.group(1)),
                "name": heading.group(2).strip(),
                "files": [],
                "rules": [],
            }
            continue

        if current is None:
            continue

        if "**Mandatory Reading List" in line:
            for m in MD_LINK_RE.finditer(line):
                target = m.group(1).split("#", 1)[0].strip()
                if target and not target.startswith(("http://", "https://")) and target not in current["files"]:
                    current["files"].append(target)

        if "**Key Invariant Rules**" in line:
            for m in RULE_REF_RE.finditer(line):
                rid = f"R-{m.group(1)}"
                if rid not in current["rules"]:
                    current["rules"].append(rid)

    if current is not None:
        archetypes.append(current)

    return archetypes


def strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments outside of JSON strings for JSONC files (e.g., tsconfig)."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escaped = False

    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1

    return "".join(out)


def validate_structured_files(root: Path) -> list[str]:
    """Validate JSON, JSONC, and Python AST syntax across configs and scripts."""
    errors: list[str] = []

    for json_path in sorted(root.rglob("*.json")):
        if any(part in SKIP_DIRS for part in json_path.relative_to(root).parts):
            continue
        rel = json_path.relative_to(root).as_posix()
        raw = json_path.read_text(encoding="utf-8")
        try:
            if json_path.name.startswith("tsconfig"):
                json.loads(strip_jsonc_comments(raw))
            else:
                json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON syntax ({exc})")

    for py_path in sorted((root / "scripts").glob("*.py")):
        rel = py_path.relative_to(root).as_posix()
        try:
            ast.parse(py_path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            errors.append(f"{rel}:{exc.lineno}: Python syntax error ({exc.msg})")

    return errors


def extract_markdown_title(text: str, fallback: str) -> str:
    """Extract the first H1 title outside YAML frontmatter and code fences."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                start = idx + 1
                break

    in_fence = False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if BACKTICK_EMPTY_PAREN_RE.search(title):
                title = BACKTICK_EMPTY_PAREN_RE.sub("", title).strip()
            return title

    return fallback


def infer_tags(rel_path: str, title: str) -> list[str]:
    """Deterministically infer concise, searchable tags from file path and title."""
    stop_words = {
        "the", "and", "for", "with", "from", "into", "guide", "mastery", "standard",
        "standards", "production", "enterprise", "readme", "md", "overview", "patterns",
        "best", "practices", "core", "system", "systems", "vs", "level", "index",
    }
    raw_tokens: list[str] = []
    path_parts = Path(rel_path).with_suffix("").parts
    for part in path_parts:
        raw_tokens.extend(re.split(r"[-_.\s]+", part.lower()))
    title_clean = re.sub(r"[^a-zA-Z0-9+#-]+", " ", title.lower())
    raw_tokens.extend(title_clean.split())

    tags: list[str] = []
    for tok in raw_tokens:
        tok = tok.strip("-")
        if len(tok) < 2 or tok in stop_words or tok.isdigit():
            continue
        if tok not in tags:
            tags.append(tok)
        if len(tags) >= 8:
            break
    return tags


def classify_module(rel_path: str) -> str:
    """Map a markdown document path into its logical module bucket."""
    parts = Path(rel_path).parts
    if len(parts) == 1:
        return "core"
    top = parts[0]
    if top == "scaffolding":
        return "scaffolding"
    return top


def build_index(root: Path) -> dict[str, Any]:
    """Deterministically compute the complete index.json v2.0.0 payload from repository state."""
    all_files = iter_repo_files(root)
    md_files = [p for p in all_files if p.suffix == ".md"]

    modules: dict[str, list[dict[str, Any]]] = {}
    total_lines = 0

    for md_path in md_files:
        rel = md_path.relative_to(root).as_posix()
        text = md_path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        total_lines += line_count
        title = extract_markdown_title(text, fallback=md_path.stem)
        bucket = classify_module(rel)
        modules.setdefault(bucket, []).append(
            {
                "path": rel,
                "title": title,
                "lines": line_count,
                "tags": infer_tags(rel, title),
            }
        )

    ordered_keys = [
        "core",
        "agents",
        "workflows",
        "frameworks",
        "languages",
        "sections",
        "pipelines",
        "scaffolding",
        "_coordination",
    ]
    ordered_modules: dict[str, list[dict[str, Any]]] = {}
    for key in ordered_keys:
        if key in modules:
            ordered_modules[key] = sorted(modules[key], key=lambda item: item["path"])
    for key in sorted(modules):
        if key not in ordered_modules:
            ordered_modules[key] = sorted(modules[key], key=lambda item: item["path"])

    rules, _ = parse_rules(root / "RULES.md")
    rule_nums = sorted(int(rid.split("-")[1]) for rid in rules)
    rule_range = f"R-{rule_nums[0]:03d}..R-{rule_nums[-1]:03d}" if rule_nums else "none"

    archetypes = parse_archetypes(root / "ROUTING.md")

    scaffolding_configs = [
        {
            "path": p.relative_to(root).as_posix(),
            "lines": len(p.read_text(encoding="utf-8", errors="replace").splitlines()),
        }
        for p in all_files
        if p.relative_to(root).as_posix().startswith("scaffolding/configs/")
    ]

    scripts = [
        {
            "path": p.relative_to(root).as_posix(),
            "lines": len(p.read_text(encoding="utf-8", errors="replace").splitlines()),
        }
        for p in all_files
        if p.relative_to(root).as_posix().startswith(("scripts/", "workflows/scripts/"))
    ]

    return {
        "name": "devskill",
        "version": INDEX_VERSION,
        "updated": INDEX_UPDATED,
        "spec_standard": "agentskills.io + AAIF AGENTS.md",
        "description": (
            "Production-grade software engineering standards, OWASP 2025 & Agentic AI security, "
            "deterministic agent routing, MCP/A2A protocols, framework/language guides, and CI gates."
        ),
        "stats": {
            "total_documents": len(md_files),
            "total_lines": total_lines,
            "total_rules": len(rules),
            "rule_range": rule_range,
            "total_archetypes": len(archetypes),
            "total_configs": len(scaffolding_configs),
            "total_scripts": len(scripts),
        },
        "modules": ordered_modules,
        "archetypes": archetypes,
        "scaffolding_configs": scaffolding_configs,
        "scripts": scripts,
    }


def validate_repo(root: Path, write_index: bool = False) -> list[str]:
    """Run all repository integrity checks and optionally regenerate index.json."""
    errors: list[str] = []
    all_files = iter_repo_files(root)
    md_files = [p for p in all_files if p.suffix == ".md"]

    errors.extend(validate_skill_frontmatter(root / "SKILL.md"))
    errors.extend(find_forbidden_paths(root, all_files))
    errors.extend(find_broken_links(root, md_files))

    rules, rule_errors = parse_rules(root / "RULES.md")
    errors.extend(rule_errors)
    errors.extend(validate_routing_citations(root / "ROUTING.md", rules))

    expected_index = build_index(root)
    index_path = root / "index.json"
    if write_index:
        index_path.write_text(
            json.dumps(expected_index, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        if not index_path.exists():
            errors.append("index.json does not exist (run with --write-index)")
        else:
            try:
                actual_index = json.loads(index_path.read_text(encoding="utf-8"))
                if actual_index != expected_index:
                    errors.append(
                        "index.json is out of sync with repository files "
                        "(run `python3 scripts/validate-skill.py --write-index`)"
                    )
            except json.JSONDecodeError as exc:
                errors.append(f"index.json is invalid JSON: {exc}")

    errors.extend(validate_structured_files(root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate-skill",
        description="Validate DevSkill repository integrity and manage index.json.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root directory (default: parent of scripts/)",
    )
    parser.add_argument(
        "--write-index",
        action="store_true",
        help="Deterministically regenerate index.json before running validation.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    errors = validate_repo(root, write_index=args.write_index)

    if errors:
        print(f"FAIL: {len(errors)} validation error(s) found:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    index_data = json.loads((root / "index.json").read_text(encoding="utf-8"))
    stats = index_data["stats"]
    print(
        f"PASS: DevSkill v{index_data['version']} validated cleanly "
        f"({stats['total_documents']} docs, {stats['total_rules']} rules [{stats['rule_range']}], "
        f"{stats['total_archetypes']} archetypes, {stats['total_configs']} configs, "
        f"{stats['total_scripts']} scripts, 0 errors)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
