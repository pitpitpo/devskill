#!/usr/bin/env python3
"""Unit and integration test suite for DevSkill executable tooling.

Run via:
  python3 -m unittest discover -s scripts -p "test_*.py" -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr_wait = _load_module("pr_wait", REPO_ROOT / "scripts" / "pr-wait.py")
validate_skill = _load_module("validate_skill", REPO_ROOT / "scripts" / "validate-skill.py")


class TestPrWaitHelpers(unittest.TestCase):
    def test_bot_name_classification(self) -> None:
        self.assertEqual(pr_wait.bot_name("greptile-apps[bot]"), "greptile")
        self.assertEqual(pr_wait.bot_name("Macroscope Check"), "macroscope")
        self.assertEqual(pr_wait.bot_name("coderabbitai[bot]"), "coderabbit")
        self.assertIsNone(pr_wait.bot_name("alice-dev"))
        self.assertIsNone(pr_wait.bot_name(None))

    def test_plain_and_snippet(self) -> None:
        raw = "<!-- hidden --><div>Hello &amp; <b>world</b>   from   PR</div>"
        self.assertEqual(pr_wait.plain(raw).strip(), "Hello &  world    from   PR")
        self.assertEqual(pr_wait.snippet(raw, limit=20), "Hello & world fro...")
        self.assertEqual(pr_wait.snippet("short text", limit=50), "short text")

    def test_verdict_extraction(self) -> None:
        body = "Summary\n**Confidence Score: 5/5** — looks solid\nDetails..."
        self.assertEqual(pr_wait.verdict(body), "Confidence Score: 5/5 — looks solid")
        self.assertEqual(pr_wait.verdict("No summary marker here"), "")

    def test_digest_uses_sha256(self) -> None:
        sample = "<p>All   checks   passed</p>"
        normalized = " All checks passed "
        expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
        self.assertEqual(pr_wait.digest(sample), expected)
        self.assertEqual(len(pr_wait.digest(sample)), 12)

    def test_parse_target_accepts_url_and_number(self) -> None:
        completed = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout='{"number":42}', stderr="")
        with mock.patch.object(pr_wait, "gh", return_value=completed):
            repo, pr = pr_wait.parse_target("https://github.com/acme/widget/pull/42/files", None)
            self.assertEqual((repo, pr), ("acme/widget", 42))

            repo2, pr2 = pr_wait.parse_target("#99", "acme/widget")
            self.assertEqual((repo2, pr2), ("acme/widget", 99))

    def test_parse_target_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            pr_wait.parse_target("not-a-pr", "acme/widget")
        self.assertEqual(ctx.exception.code, 2)

        with self.assertRaises(SystemExit) as ctx2:
            pr_wait.parse_target("0", "acme/widget")
        self.assertEqual(ctx2.exception.code, 2)

        with self.assertRaises(SystemExit) as ctx3:
            pr_wait.parse_target("12", "invalid_repo_format")
        self.assertEqual(ctx3.exception.code, 2)


class TestPrWaitWatcherFetch(unittest.TestCase):
    def _make_watcher(self, tmpdir: str) -> pr_wait.Watcher:
        with mock.patch.object(pr_wait, "STATE_DIR", Path(tmpdir)):
            return pr_wait.Watcher("acme/widget", 42, "ready", 20)

    def test_fetch_pr_handles_graphql_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = self._make_watcher(tmpdir)
            err_payload = json.dumps({"errors": [{"message": "Resource not accessible by integration"}]})
            proc = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=err_payload, stderr="")
            with mock.patch.object(pr_wait, "gh", return_value=proc):
                with self.assertRaises(pr_wait.GhError) as ctx:
                    watcher.fetch_pr()
                self.assertIn("GraphQL error", str(ctx.exception))
                self.assertFalse(ctx.exception.transient)

    def test_fetch_pr_handles_null_pull_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = self._make_watcher(tmpdir)
            null_payload = json.dumps({"data": {"viewer": {"login": "bot"}, "repository": {"pullRequest": None}}})
            proc = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=null_payload, stderr="")
            with mock.patch.object(pr_wait, "gh", return_value=proc):
                with self.assertRaises(pr_wait.GhError) as ctx:
                    watcher.fetch_pr()
                self.assertIn("not found or inaccessible", str(ctx.exception))
                self.assertFalse(ctx.exception.transient)

    def test_fetch_pr_falls_back_to_rest_on_rate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = self._make_watcher(tmpdir)
            rest_pr = json.dumps(
                {
                    "html_url": "https://github.com/acme/widget/pull/42",
                    "state": "open",
                    "merged": False,
                    "mergeable_state": "clean",
                    "head": {"sha": "abc1234567890"},
                    "base": {"ref": "main", "sha": "def0987654321"},
                    "user": {"login": "alice"},
                }
            )

            def fake_gh(args: list[str], allow: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
                if args[:2] == ["api", "graphql"]:
                    raise pr_wait.GhError("gh: API rate limit exceeded for GraphQL", transient=True)
                if args == ["api", "repos/acme/widget/pulls/42"]:
                    return subprocess.CompletedProcess(args=args, returncode=0, stdout=rest_pr, stderr="")
                if args == ["api", "user", "--jq", ".login"]:
                    return subprocess.CompletedProcess(args=args, returncode=0, stdout="alice\n", stderr="")
                raise AssertionError(f"Unexpected gh call: {args}")

            with mock.patch.object(pr_wait, "gh", side_effect=fake_gh):
                pr = watcher.fetch_pr()
                self.assertEqual(pr["state"], "OPEN")
                self.assertEqual(pr["headRefOid"], "abc1234567890")
                self.assertEqual(pr["baseRefName"], "main")
                self.assertEqual(pr["mergeStateStatus"], "CLEAN")
                self.assertEqual(pr["viewer"], "alice")


class TestValidateSkillUnit(unittest.TestCase):
    def test_frontmatter_validation_accepts_valid_and_rejects_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            good = Path(tmpdir) / "GOOD.md"
            good.write_text(
                "---\n"
                "name: devskill\n"
                "description: Production software engineering skill.\n"
                "metadata:\n"
                '  version: "2.0.0"\n'
                "---\n# Title\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_skill.validate_skill_frontmatter(good), [])

            bad = Path(tmpdir) / "BAD.md"
            bad.write_text(
                "---\n"
                "name: Bad_Name!\n"
                "description: ok\n"
                "metadata:\n"
                "  count: 42\n"
                "  enabled: true\n"
                "---\n",
                encoding="utf-8",
            )
            errs = validate_skill.validate_skill_frontmatter(bad)
            self.assertEqual(len(errs), 3)

    def test_strip_code_from_markdown_skips_fences_and_inline(self) -> None:
        sample = (
            "Real [link](valid.md)\n"
            "Inline `[not-a-link](missing.md)` here\n"
            "```markdown\n"
            "[fenced](also-missing.md)\n"
            "```\n"
            "After [second](valid2.md)\n"
        )
        cleaned = validate_skill.strip_code_from_markdown(sample)
        self.assertIn("[link](valid.md)", cleaned)
        self.assertIn("[second](valid2.md)", cleaned)
        self.assertNotIn("missing.md", cleaned)
        self.assertNotIn("also-missing.md", cleaned)

    def test_strip_jsonc_comments_preserves_urls_in_strings(self) -> None:
        jsonc = (
            "{\n"
            '  // top comment\n'
            '  "$schema": "https://json.schemastore.org/tsconfig",\n'
            '  /* block comment */\n'
            '  "strict": true\n'
            "}\n"
        )
        parsed = json.loads(validate_skill.strip_jsonc_comments(jsonc))
        self.assertEqual(parsed["$schema"], "https://json.schemastore.org/tsconfig")
        self.assertTrue(parsed["strict"])

    def test_parse_rules_detects_duplicates_and_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_file = Path(tmpdir) / "RULES.md"
            rules_file.write_text(
                "- **R-001 [First Rule]**: body\n"
                "- **R-003 [First Rule]**: duplicate title and missing R-002\n",
                encoding="utf-8",
            )
            rules, errs = validate_skill.parse_rules(rules_file)
            self.assertEqual(set(rules.keys()), {"R-001", "R-003"})
            self.assertTrue(any("duplicate rule title" in e for e in errs))
            self.assertTrue(any("R-002" in e for e in errs))

    def test_find_broken_links_catches_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "exists.md").write_text("# Exists\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "Good: [ok](exists.md#section) and [ext](https://example.com)\n"
                "Bad: [broken](does-not-exist.md)\n",
                encoding="utf-8",
            )
            errs = validate_skill.find_broken_links(root, [doc, root / "exists.md"])
            self.assertEqual(len(errs), 1)
            self.assertIn("does-not-exist.md", errs[0])


class TestCiGateScript(unittest.TestCase):
    GATE = REPO_ROOT / "scripts" / "ci-gate.sh"

    def _init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "ci@example.org"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "CI"], cwd=root, check=True)

    def test_ci_gate_passes_on_clean_code_and_ignores_test_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_repo(root)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "math.ts").write_text(
                "export function add(a: number, b: number): number { return a + b; }\n",
                encoding="utf-8",
            )
            (root / "tests" / "math.test.ts").write_text(
                "const mockUser: any = { email: 'test@example.com' };\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            res = subprocess.run(["bash", str(self.GATE)], cwd=root, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_ci_gate_blocks_violations_in_repo_and_staged_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_repo(root)
            (root / "src").mkdir()
            marker = "TO" + "DO: implement"
            (root / "src" / "bad.ts").write_text(
                f"export function bad(x: any) {{ /* {marker} */ try {{ console.log(x); }} catch (e) {{}} }}\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)

            res_repo = subprocess.run(["bash", str(self.GATE)], cwd=root, capture_output=True, text=True)
            self.assertEqual(res_repo.returncode, 1)
            self.assertIn("FAIL [R-001]", res_repo.stderr)
            self.assertIn("FAIL [R-034]", res_repo.stderr)
            self.assertIn("FAIL [R-046]", res_repo.stderr)
            self.assertIn("FAIL [R-142]", res_repo.stderr)

            res_staged = subprocess.run(
                ["bash", str(self.GATE), "--staged"], cwd=root, capture_output=True, text=True
            )
            self.assertEqual(res_staged.returncode, 1)
            self.assertIn("FAIL [R-001]", res_staged.stderr)

    def test_ci_gate_fails_closed_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            res = subprocess.run(["bash", str(self.GATE)], cwd=tmpdir, capture_output=True, text=True)
            self.assertEqual(res.returncode, 2)


class TestReqLedgerScript(unittest.TestCase):
    SCRIPT = REPO_ROOT / "scripts" / "req-ledger.py"

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args],
            capture_output=True,
            text=True,
        )

    def test_full_lifecycle_recitation_and_fail_closed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = str(Path(tmpdir) / ".devskill" / "requirements.json")

            res_init = self._run("init", ledger, "--title", "Webhook Hardening")
            self.assertEqual(res_init.returncode, 0, res_init.stderr)

            self.assertEqual(
                self._run(
                    "add",
                    ledger,
                    "--id",
                    "REQ-001",
                    "--category",
                    "api",
                    "--type",
                    "functional",
                    "--description",
                    "Verify HMAC-SHA256 signature on raw body",
                    "--criteria",
                    "Invalid signature returns 400",
                ).returncode,
                0,
            )
            self.assertEqual(
                self._run(
                    "add",
                    ledger,
                    "--id",
                    "REQ-002",
                    "--category",
                    "security",
                    "--type",
                    "negative",
                    "--protected",
                    "--description",
                    "MUST NOT log raw customer PII or webhook secrets",
                    "--criteria",
                    "Zero secret or email substrings in test logs",
                ).returncode,
                0,
            )
            self.assertEqual(
                self._run(
                    "add",
                    ledger,
                    "--id",
                    "REQ-003",
                    "--category",
                    "reliability",
                    "--type",
                    "edge_case",
                    "--description",
                    "Duplicate event.id delivery is idempotent",
                    "--criteria",
                    "Second POST returns 200 without duplicate ledger rows",
                ).returncode,
                0,
            )
            self.assertEqual(
                self._run(
                    "add",
                    ledger,
                    "--id",
                    "REQ-004",
                    "--category",
                    "ux",
                    "--type",
                    "non_functional",
                    "--description",
                    "Optional latency metric dashboard link",
                    "--criteria",
                    "Optional link renders cleanly",
                    "--optional",
                ).returncode,
                0,
            )

            # Gate rejects unfrozen ledger when --require-frozen is specified
            res_unfrozen = self._run("gate", ledger, "--require-frozen")
            self.assertEqual(res_unfrozen.returncode, 1)
            self.assertIn("NOT frozen", res_unfrozen.stderr)

            # Freeze specification
            res_freeze = self._run("freeze", ledger)
            self.assertEqual(res_freeze.returncode, 0, res_freeze.stderr)

            # Recitation pins negative constraints before next item
            res_recite = self._run("recite", ledger)
            self.assertEqual(res_recite.returncode, 0, res_recite.stderr)
            self.assertIn("[ACTIVE NEGATIVE CONSTRAINTS - NEVER VIOLATE]:", res_recite.stdout)
            self.assertLess(
                res_recite.stdout.index("REQ-002"),
                res_recite.stdout.index("[NEXT REQUIREMENT TO COMPLETE]:"),
            )

            # Audit-prompt emits SatisFix Objective-Aligned Deviation Elicitation and USER-PROTECTED marker
            res_audit = self._run("audit-prompt", ledger)
            self.assertEqual(res_audit.returncode, 0, res_audit.stderr)
            self.assertIn("SATISFIX DEVIATION CHECK", res_audit.stdout)
            self.assertIn("USER-PROTECTED", res_audit.stdout)

            # Verify all 3 required items (leave optional REQ-004 open)
            for rid in ("REQ-001", "REQ-002", "REQ-003"):
                res_v = self._run(
                    "verify",
                    ledger,
                    "--id",
                    rid,
                    "--files",
                    "src/webhook.py,tests/test_webhook.py",
                    "--command",
                    "pytest tests/test_webhook.py",
                    "--exit-code",
                    "0",
                    "--evidence",
                    f"{rid} verified with 3/3 assertions passing",
                )
                self.assertEqual(res_v.returncode, 0, res_v.stderr)

            # Gate passes once 100% required items have valid proof
            res_gate = self._run("gate", ledger, "--require-frozen")
            self.assertEqual(res_gate.returncode, 0, res_gate.stderr)
            self.assertIn("3/3 required verified", res_gate.stdout)

    def test_verify_rejects_nonzero_exit_code_and_blank_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = str(Path(tmpdir) / "reqs.json")
            self._run("init", ledger, "--title", "Proof Enforcement")
            self._run(
                "add",
                ledger,
                "--id",
                "REQ-001",
                "--category",
                "core",
                "--type",
                "functional",
                "--description",
                "Reject invalid tokens",
                "--criteria",
                "401 returned",
            )
            self._run("freeze", ledger)

            res_bad_code = self._run(
                "verify",
                ledger,
                "--id",
                "REQ-001",
                "--command",
                "pytest",
                "--exit-code",
                "1",
                "--evidence",
                "1 failed",
            )
            self.assertEqual(res_bad_code.returncode, 1)
            self.assertIn("REFUSED", res_bad_code.stderr)

            res_blank_ev = self._run(
                "verify",
                ledger,
                "--id",
                "REQ-001",
                "--command",
                "pytest",
                "--exit-code",
                "0",
                "--evidence",
                "   ",
            )
            self.assertEqual(res_blank_ev.returncode, 1)
            self.assertIn("non-empty --evidence", res_blank_ev.stderr)

            # Gate must still fail closed because REQ-001 remains passes=false
            res_gate = self._run("gate", ledger, "--require-frozen")
            self.assertEqual(res_gate.returncode, 1)
            self.assertIn("[UNVERIFIED FUNCTIONAL] REQ-001", res_gate.stderr)

    def test_tamper_detection_and_audited_amendment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "reqs.json"
            ledger = str(ledger_path)
            self._run("init", ledger, "--title", "Anti-Tamper Test")
            self._run(
                "add",
                ledger,
                "--id",
                "REQ-001",
                "--category",
                "auth",
                "--type",
                "functional",
                "--description",
                "Enforce tenant isolation on all queries",
                "--criteria",
                "Cross-tenant query returns 403",
            )
            self._run("freeze", ledger)

            # Adding without --amend --reason is refused while frozen
            res_unamended = self._run(
                "add",
                ledger,
                "--id",
                "REQ-002",
                "--category",
                "auth",
                "--type",
                "negative",
                "--description",
                "MUST NOT expose stack traces",
                "--criteria",
                "RFC 9457 error payload only",
            )
            self.assertEqual(res_unamended.returncode, 1)
            self.assertIn("FROZEN", res_unamended.stderr)

            # Authorized amendment succeeds and records audit trail
            res_amended = self._run(
                "add",
                ledger,
                "--id",
                "REQ-002",
                "--category",
                "auth",
                "--type",
                "negative",
                "--description",
                "MUST NOT expose stack traces",
                "--criteria",
                "RFC 9457 error payload only",
                "--amend",
                "--reason",
                "User requested strict RFC 9457 error scrubbing",
            )
            self.assertEqual(res_amended.returncode, 0, res_amended.stderr)
            payload = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["amendments"]), 1)
            self.assertEqual(payload["amendments"][0]["action"], "add:REQ-002")

            # Mutating description directly on disk triggers SPEC TAMPERING DETECTED
            payload["requirements"][0]["description"] = "Weakened requirement"
            ledger_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            res_tampered_gate = self._run("gate", ledger, "--require-frozen")
            self.assertEqual(res_tampered_gate.returncode, 1)
            self.assertIn("SPEC TAMPERING DETECTED", res_tampered_gate.stderr)

            res_tampered_verify = self._run(
                "verify",
                ledger,
                "--id",
                "REQ-001",
                "--command",
                "pytest",
                "--exit-code",
                "0",
                "--evidence",
                "passed",
            )
            self.assertEqual(res_tampered_verify.returncode, 1)
            self.assertIn("SPEC TAMPERING DETECTED", res_tampered_verify.stderr)


class TestDevSkillRepositoryIntegrity(unittest.TestCase):
    def test_repository_validates_with_zero_errors(self) -> None:
        errors = validate_skill.validate_repo(REPO_ROOT, write_index=False)
        self.assertEqual(errors, [], "Repository validation failed:\n" + "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
