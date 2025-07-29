import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import unittest
from unittest import mock
from runner.run import run_newman
from runner.config import Config
from pathlib import Path
import tempfile
import json

class TestRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            id_exec="run01",
            output_type="csv,plaintext",
            collection=None,
            environment=None,
            destination=tempfile.mkdtemp(),
            mailjet_api_key="key",
            mailjet_api_secret="secret",
            send_email_to=["a@b.com"],
            interactive=False
        )
        # Cria uma coleção fake
        self.collection_path = Path(self.config.destination) / "fake_collection.postman_collection.json"
        with open(self.collection_path, "w") as f:
            f.write("{}")
        # Cria um json de resultado fake
        self.json_report_path = Path(self.config.destination) / "artifacts" / "json"
        self.json_report_path.mkdir(parents=True, exist_ok=True)
        self.json_report = self.json_report_path / "fake_collection_20240101_000000.json"
        with open(self.json_report, "w") as f:
            json.dump({
                "run": {
                    "executions": [
                        {"response": {"code": 200}, "assertions": [{"passed": True}, {"passed": False}]},
                        {"response": {"code": 500}, "assertions": [{"passed": True}]}
                    ]
                }
            }, f)

    @mock.patch("runner.run.send_email_report")
    @mock.patch("runner.run.subprocess.Popen")
    @mock.patch("runner.run.parse_config")
    def test_main_success(self, mock_parse_config, mock_popen, mock_send_email):
        # Mock config
        mock_parse_config.return_value = self.config
        # Mock subprocess
        process_mock = mock.Mock()
        process_mock.stdout = ["output line 1\n", "output line 2\n"]
        process_mock.wait.return_value = 0
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        # Mock email
        mock_send_email.return_value = True
        # Mock collections
        with mock.patch("runner.run.Path.glob", return_value=[self.collection_path]):
            import runner.run
            exit_code = runner.run.main()
        self.assertEqual(exit_code, 0)
        self.assertTrue(mock_send_email.called)

    @mock.patch("runner.run.send_email_report")
    @mock.patch("runner.run.subprocess.Popen")
    @mock.patch("runner.run.parse_config")
    def test_main_failure(self, mock_parse_config, mock_popen, mock_send_email):
        mock_parse_config.return_value = self.config
        process_mock = mock.Mock()
        process_mock.stdout = ["output line 1\n"]
        process_mock.wait.return_value = 1
        process_mock.returncode = 1
        mock_popen.return_value = process_mock
        mock_send_email.return_value = True
        with mock.patch("runner.run.Path.glob", return_value=[self.collection_path]):
            import runner.run
            exit_code = runner.run.main()
        self.assertEqual(exit_code, 1)
        self.assertTrue(mock_send_email.called)

    @mock.patch("runner.run.send_email_report")
    @mock.patch("runner.run.subprocess.Popen")
    @mock.patch("runner.run.parse_config")
    def test_main_no_email(self, mock_parse_config, mock_popen, mock_send_email):
        config_no_email = self.config
        config_no_email.mailjet_api_key = None
        mock_parse_config.return_value = config_no_email
        process_mock = mock.Mock()
        process_mock.stdout = ["output line 1\n"]
        process_mock.wait.return_value = 0
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        with mock.patch("runner.run.Path.glob", return_value=[self.collection_path]):
            import runner.run
            exit_code = runner.run.main()
        self.assertEqual(exit_code, 0)
        self.assertFalse(mock_send_email.called)

if __name__ == "__main__":
    unittest.main() 