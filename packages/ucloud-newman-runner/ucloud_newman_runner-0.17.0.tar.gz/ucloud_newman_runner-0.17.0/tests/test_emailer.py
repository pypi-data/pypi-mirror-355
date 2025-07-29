import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from runner import emailer
import unittest
from unittest import mock
import tempfile
import json
from pathlib import Path

class TestEmailer(unittest.TestCase):
    def setUp(self):
        self.summary = {
            'total_metrics': {
                'total_requests': 10,
                'failed_requests': 1,
                'total_assertions': 20,
                'failed_assertions': 2,
                'overall_success_rate': 90.0,
                'assertion_success_rate': 95.0
            },
            'results': [{'status': 'SUCCESS'}],
            'timestamp': '2024-01-01T12:00:00',
            'environment': 'staging'
        }
        self.tmp_summary = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        json.dump(self.summary, self.tmp_summary)
        self.tmp_summary.close()
        self.tmp_template = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html')
        self.tmp_template.write('<html>${STATUS_TEXT}</html>')
        self.tmp_template.close()

    def tearDown(self):
        os.unlink(self.tmp_summary.name)
        os.unlink(self.tmp_template.name)

    @mock.patch('runner.emailer.requests.post')
    def test_send_email_report_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = emailer.send_email_report(
            mailjet_api_key='key',
            mailjet_api_secret='secret',
            recipients=['a@b.com'],
            summary_path=Path(self.tmp_summary.name),
            template_path=Path(self.tmp_template.name)
        )
        self.assertTrue(result)
        self.assertTrue(mock_post.called)

    def test_send_email_report_no_credentials(self):
        result = emailer.send_email_report(
            mailjet_api_key=None,
            mailjet_api_secret=None,
            recipients=['a@b.com'],
            summary_path=Path(self.tmp_summary.name),
            template_path=Path(self.tmp_template.name)
        )
        self.assertFalse(result)

    def test_send_email_report_no_recipients(self):
        result = emailer.send_email_report(
            mailjet_api_key='key',
            mailjet_api_secret='secret',
            recipients=[],
            summary_path=Path(self.tmp_summary.name),
            template_path=Path(self.tmp_template.name)
        )
        self.assertFalse(result)

    def test_send_email_report_template_missing(self):
        result = emailer.send_email_report(
            mailjet_api_key='key',
            mailjet_api_secret='secret',
            recipients=['a@b.com'],
            summary_path=Path(self.tmp_summary.name),
            template_path=Path('nonexistent.html')
        )
        self.assertFalse(result)

    def test_send_email_report_corrupted_summary(self):
        # Cria arquivo JSON inválido
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
            tmp.write('{corrupted json')
            tmp.close()
            result = emailer.send_email_report(
                mailjet_api_key='key',
                mailjet_api_secret='secret',
                recipients=['a@b.com'],
                summary_path=Path(tmp.name),
                template_path=Path(self.tmp_template.name)
            )
            self.assertFalse(result)
        os.unlink(tmp.name)

    def test_send_email_report_summary_missing(self):
        result = emailer.send_email_report(
            mailjet_api_key='key',
            mailjet_api_secret='secret',
            recipients=['a@b.com'],
            summary_path=Path('nonexistent.json'),
            template_path=Path(self.tmp_template.name)
        )
        self.assertFalse(result)

    @mock.patch('runner.emailer.requests.post')
    def test_send_email_report_http_error(self, mock_post):
        mock_post.side_effect = Exception("Erro HTTP")
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_summary, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html') as tmp_template:
            tmp_summary.write(json.dumps({"timestamp": "2024-01-01T12:00:00", "results": [{"status": "SUCCESS"}]}))
            tmp_summary.close()
            tmp_template.write('<html>${STATUS_TEXT}</html>')
            tmp_template.close()
            result = emailer.send_email_report(
                mailjet_api_key='key',
                mailjet_api_secret='secret',
                recipients=['a@b.com'],
                summary_path=Path(tmp_summary.name),
                template_path=Path(tmp_template.name)
            )
            self.assertFalse(result)
        os.unlink(tmp_summary.name)
        os.unlink(tmp_template.name)

if __name__ == "__main__":
    unittest.main() 