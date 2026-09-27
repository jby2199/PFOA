"""Document-validator ID regression checks: python -B tools/check_validate_ids.py."""
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SECTIONS = {
    "prd": "개요|사용자 및 환경|사용자 스토리|기능 요구사항|비기능 요구사항|범위 외",
    "srs": "개요|범위|정의 및 약어|참조 문서|전체 설명|기능 요구사항|비기능 요구사항|인터페이스 요구사항|제약사항|부록",
    "sdd": "구조|상세|ADR",
    "sad": "개요|이해관계자와 관심사|뷰포인트|뷰|뷰 간 일관성|아키텍처 근거|추적성",
}
ITEMS = {
    "prd": "UAFN",
    "srs": "FN",
    "sdd": "MIDC",
    "sad": "SKVWXCIQR",
}


def document(kind):
    text = "\n".join(f"## {section}\n설명입니다.\n" for section in SECTIONS[kind].split("|"))
    for letter in ITEMS[kind]:
        text += f"\n### [{kind.upper()}-{letter}001] 항목 제목\n"
        if kind == "sad" and letter == "V":
            text += "대상 이해관계자: [SAD-S001]\n대상 관심사: [SAD-K001]\n언어: Mermaid\n출처: 자체 정의\n"
        elif kind == "sad" and letter == "W":
            text += "대응 뷰포인트: [SAD-V001]\n"
        elif kind == "sdd" or (kind == "sad" and letter in "CIQR"):
            text += "구현요건: [SRS-F001], [SRS-N001]\n"
        else:
            text += "요약: 항목의 내용입니다.\n"
    if kind in ("sdd", "sad"):
        text += "\n비책임: 외부 시스템 관리.\n```mermaid\nflowchart LR\n  A --> B\n```\n"
    return text


class ValidatorIds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = []
        for tree in (".claude", ".codex"):
            for kind in ITEMS:
                path = ROOT / tree / "skills" / f"by-{kind}-writer" / "scripts" / "validate.py"
                cls.validators.append((tree, kind, runpy.run_path(str(path))["check"]))

    def check_text(self, check, text):
        with tempfile.TemporaryDirectory(prefix="validate-ids-", dir=ROOT / "tools") as directory:
            path = pathlib.Path(directory) / "document.md"
            path.write_text(text, encoding="utf-8")
            return check(str(path))

    def test_current_definitions_and_repeated_references(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                rid = f"{kind.upper()}-{ITEMS[kind][0]}001"
                text = document(kind) + f"\n참조: [{rid}], [{rid}].\n| [{rid}] | 설명 |\n본문 참조: {rid}.\n"
                self.assertEqual([], self.check_text(check, text))

    def test_indented_headings(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                self.assertEqual([], self.check_text(check, document(kind).replace("### [", "  ### [")))

    def test_duplicate_definition(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                rid = f"{kind.upper()}-{ITEMS[kind][0]}001"
                issues = self.check_text(check, document(kind) + f"\n### [{rid}] 중복 제목\n설명\n")
                self.assertTrue(any("중복" in issue for issue in issues), issues)

    def test_malformed_extra_id(self):
        for tree, kind, check in self.validators:
            for suffix in ("01", "0001", "００１", "001x"):
                with self.subTest(tree=tree, kind=kind, suffix=suffix):
                    bad = f"{kind.upper()}-{ITEMS[kind][0]}{suffix}"
                    self.assertTrue(self.check_text(check, document(kind) + f"\n### [{bad}] 잘못된 항목\n설명\n"))
            with self.subTest(tree=tree, kind=kind, unknown_type=True):
                self.assertTrue(self.check_text(check, document(kind) + f"\n### [{kind.upper()}-Z001] 잘못된 유형\n설명\n"))
            with self.subTest(tree=tree, kind=kind, missing_bracket=True):
                bad = f"{kind.upper()}-{ITEMS[kind][0]}002"
                self.assertTrue(self.check_text(check, document(kind) + f"\n### [{bad} 닫는 괄호 누락\n설명\n"))

    def test_brackets_in_definition_title(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                text = document(kind).replace("항목 제목", "항목 [별도 제목]", 1)
                self.assertTrue(self.check_text(check, text))

    def test_standalone_definitions(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                # SAD views retain their required H3 heading; other IDs may stand alone.
                text = document(kind).replace(" 항목 제목", "")
                if kind != "sad":
                    text = text.replace("### [", "[")
                self.assertEqual([], self.check_text(check, text))

    def test_prd_legacy_ids_and_comment_only_ids(self):
        for tree, kind, check in self.validators:
            if kind != "prd":
                continue
            with self.subTest(tree=tree):
                sections = "\n".join(f"## {s}\n내용" for s in SECTIONS[kind].split("|"))
                self.assertTrue(self.check_text(check, sections + "\nUS-01 F-01 NF-01\n"))
                self.assertTrue(self.check_text(check, sections + "\n<!--\n" + document(kind) + "\n-->"))

    def test_sad_titled_viewpoint_still_requires_metadata(self):
        for tree, kind, check in self.validators:
            if kind == "sad":
                with self.subTest(tree=tree):
                    text = document(kind).replace("출처: 자체 정의\n", "")
                    self.assertTrue(any("출처" in issue for issue in self.check_text(check, text)))

    def test_required_definitions_cannot_be_replaced_by_references(self):
        for tree, kind, check in self.validators:
            with self.subTest(tree=tree, kind=kind):
                text = document(kind).replace("### [", "참조: [")
                self.assertTrue(self.check_text(check, text))

    def test_prd_acceptance_criteria_required(self):
        for tree, kind, check in self.validators:
            if kind == "prd":
                with self.subTest(tree=tree):
                    text = document(kind).replace("### [PRD-A001] 항목 제목\n요약: 항목의 내용입니다.\n", "")
                    self.assertTrue(self.check_text(check, text))

    def test_cli_exit_codes_and_mirror_parity(self):
        for kind in ITEMS:
            relative = pathlib.Path("skills") / f"by-{kind}-writer" / "scripts" / "validate.py"
            self.assertEqual((ROOT / ".claude" / relative).read_bytes(), (ROOT / ".codex" / relative).read_bytes())
        with tempfile.TemporaryDirectory(prefix="validate-cli-", dir=ROOT / "tools") as directory:
            path = pathlib.Path(directory) / "document.md"
            for tree, kind, _ in self.validators:
                validator = ROOT / tree / "skills" / f"by-{kind}-writer" / "scripts" / "validate.py"
                command = [sys.executable, "-X", "utf8", "-B", str(validator)]
                for expected, content in ((0, document(kind)), (1, "# 미완성 문서\n")):
                    with self.subTest(tree=tree, kind=kind, exit_code=expected):
                        path.write_text(content, encoding="utf-8")
                        result = subprocess.run(command + [str(path)], capture_output=True, text=True, encoding="utf-8")
                        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
                with self.subTest(tree=tree, kind=kind, usage=True):
                    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(2, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
