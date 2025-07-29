import sys
import os
import pytest
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from runner import config
import unittest

class TestConfig(unittest.TestCase):
    def test_get_config_value_precedence(self):
        # ENV tem precedência
        with mock.patch.dict(os.environ, {"TEST_ENV": "env_value"}):
            self.assertEqual(config.get_config_value("TEST_ENV", "cli_value", "default"), "env_value")
        # CLI tem precedência se ENV não existe
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.get_config_value("TEST_ENV", "cli_value", "default"), "cli_value")
        # Default é usado se nenhum dos outros
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.get_config_value("TEST_ENV", None, "default"), "default")

    def test_config_dataclass_properties(self):
        c = config.Config(
            id_exec="run01",
            output_type="table",
            collection="col.json",
            environment="env.json",
            destination="/tmp/results",
            mailjet_api_key="key",
            mailjet_api_secret="secret",
            send_email_to=["a@b.com", "c@d.com"],
            interactive=False
        )
        base = os.path.abspath(os.path.join("/tmp/results", "run01"))
        self.assertEqual(str(c.base_dir), base)
        self.assertEqual(str(c.artifacts_html_dir), os.path.join(base, "artifacts", "html"))
        self.assertEqual(str(c.artifacts_json_dir), os.path.join(base, "artifacts", "json"))
        self.assertEqual(str(c.logs_dir), os.path.join(base, "logs"))
        self.assertEqual(str(c.log_file), os.path.join(base, "logs", "output.log"))

# Testes com monkeypatch devem ser funções livres para pytest

def test_parse_config_missing_id(monkeypatch):
    import sys
    test_args = ["prog", "--destination", "results"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit) as excinfo:
        config.parse_config()
    assert excinfo.value.code == 2

if __name__ == "__main__":
    unittest.main() 