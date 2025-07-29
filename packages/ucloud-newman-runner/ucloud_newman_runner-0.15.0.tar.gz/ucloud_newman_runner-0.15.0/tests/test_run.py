import sys
import os
import tempfile
import pytest
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from runner.run import process_newman_results, run_newman, check_newman_interactive
from runner.config import Config

def test_process_newman_results_invalid_json(tmp_path):
    file = tmp_path / "invalid.json"
    file.write_text("{invalid json")
    result = process_newman_results(str(file))
    assert result == {}

def test_run_newman_collection_not_found(tmp_path):
    config = Config(
        id_exec="run01",
        output_type="table",
        collection=str(tmp_path / "notfound.json"),
        environment=None,
        destination=str(tmp_path),
        mailjet_api_key=None,
        mailjet_api_secret=None,
        send_email_to=[],
        interactive=False
    )
    result = run_newman(config)
    assert result is False

def test_run_newman_no_collections(tmp_path, monkeypatch):
    config = Config(
        id_exec="run01",
        output_type="table",
        collection=None,
        environment=None,
        destination=str(tmp_path),
        mailjet_api_key=None,
        mailjet_api_secret=None,
        send_email_to=[],
        interactive=False
    )
    monkeypatch.setattr("runner.run.Path.glob", lambda self, pat: [])
    result = run_newman(config)
    assert result is False

def test_run_newman_exception(monkeypatch, tmp_path):
    config = Config(
        id_exec="run01",
        output_type="table",
        collection=None,
        environment=None,
        destination=str(tmp_path),
        mailjet_api_key=None,
        mailjet_api_secret=None,
        send_email_to=[],
        interactive=False
    )
    monkeypatch.setattr("runner.run.Path.glob", lambda self, pat: 1/0)  # Força erro
    result = run_newman(config)
    assert result is False

def test_check_newman_interactive_no_install(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    result = check_newman_interactive()
    assert result is False

def test_check_newman_interactive_install_fail(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    monkeypatch.setattr("builtins.input", lambda _: "s")
    monkeypatch.setattr("subprocess.check_call", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail")))
    result = check_newman_interactive()
    assert result is False 