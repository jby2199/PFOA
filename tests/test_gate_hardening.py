from pathlib import Path


ROOT = Path(__file__).parents[1]
SETTINGS = (ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
GATE = (ROOT / "tools" / "gate.ps1").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github" / "workflows" / "stage-gates.yml").read_text(encoding="utf-8")


def test_session_hook_uses_explicit_stage_variable():
    assert "-File tools/gate-check.ps1" in SETTINGS
    assert "-Upstream docs" not in SETTINGS
    checker = (ROOT / "tools" / "gate-check.ps1").read_text(encoding="utf-8")
    assert "[string]$Upstream = $env:GATE_STAGE" in checker
    assert "if ([string]::IsNullOrWhiteSpace($Upstream)) { $Upstream = 'docs' }" in checker


def test_drift_filter_accepts_nested_requirement_documents():
    assert "$_ -match '^docs/.*(PRD|SRS|SDD|SAD)[^/]*\\.md$'" in GATE
    assert "$_ -cmatch '^docs/[^/]*(PRD|SRS|SDD|SAD)[^/]*\\.md$'" not in GATE


def test_vv_gate_checks_requirement_drift():
    vv_block = GATE.split("if ($Stage -eq 'vv')", 1)[1]
    assert vv_block.index("Test-UpstreamChain @('docs', 'impl')") < vv_block.index("Test-UpstreamDrift")


def test_impl_ci_detection_requires_docs_only():
    impl_block = WORKFLOW.split("\n  gate-impl:", 1)[1].split("\n  gate-vv:", 1)[0]
    assert "d=$(find docs" in impl_block
    assert 'echo "ran=$([ "$d" -gt 0 ] && echo true || echo false)"' in impl_block


def test_docs_detection_and_gate_are_separate_steps():
    docs_block = WORKFLOW.split("\n  gate-impl:", 1)[0]
    assert "- name: Detect work artifacts" in docs_block
    assert "- name: Run docs gate" in docs_block


def test_vv_ci_detection_requires_docs_and_tests():
    vv_block = WORKFLOW.split("\n  gate-vv:", 1)[1]
    assert '[ "$d" -gt 0 ] && [ "$t" -gt 0 ]' in vv_block