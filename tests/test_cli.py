
from aiexpect import collector, expect
from aiexpect.cli import main
from aiexpect.report import write_json


def test_cli_check(capsys):
    assert main(["check", "Return within 30 days", "--contain", "30 days", "--no-pii"]) == 0
    assert main(["check", "hi", "--contain", "bye"]) == 1
    out = capsys.readouterr().out
    assert "PASS" in out and "FAIL" in out


def test_cli_report_and_summary(tmp_path, capsys):
    collector.clear()
    expect("x").to_not_be_empty()
    jp = tmp_path / "r.json"
    write_json(str(jp), collector.results())
    out_html = tmp_path / "r.html"
    assert main(["report", str(jp), "-o", str(out_html)]) == 0
    assert out_html.read_text().startswith("<!doctype html>")
    assert main(["summary", str(jp)]) == 0
    assert main(["summary", str(jp), "--min-trust", "101"]) == 1
    assert "Trust Score" in capsys.readouterr().out


def test_cli_markdown_summary(tmp_path, capsys):
    collector.clear()
    expect("x").to_not_be_empty()
    expect("x", soft=True).to_contain("zzz")
    jp = tmp_path / "r.json"
    write_json(str(jp), collector.results())
    assert main(["summary", str(jp), "--markdown", "--min-trust", "90"]) == 1
    out = capsys.readouterr().out
    assert "Trust Score" in out and "| Accuracy |" in out and "Failed checks" in out and "below" in out
