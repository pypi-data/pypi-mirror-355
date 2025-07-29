import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from runner import reporting
import unittest
import tempfile
import csv
import pytest

class TestReporting(unittest.TestCase):
    def setUp(self):
        self.results = [
            {
                'collection': 'col1',
                'status': 'OK',
                'metrics': {
                    'total_requests': 10,
                    'failed_requests': 1,
                    'total_assertions': 20,
                    'failed_assertions': 2,
                    'success_rate': 90.0,
                    'assertion_success_rate': 95.0
                },
                'html_report': 'col1.html',
                'json_report': 'col1.json'
            }
        ]

    def test_write_csv_report(self):
        with tempfile.NamedTemporaryFile(mode='r+', delete=False, suffix='.csv') as tmp:
            reporting.write_csv_report(self.results, tmp.name)
            tmp.seek(0)
            reader = csv.DictReader(tmp)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['collection'], 'col1')
            self.assertEqual(rows[0]['status'], 'OK')
            self.assertEqual(rows[0]['total_requests'], '10')
            self.assertEqual(rows[0]['failed_requests'], '1')
            self.assertEqual(rows[0]['total_assertions'], '20')
            self.assertEqual(rows[0]['failed_assertions'], '2')
            self.assertEqual(rows[0]['success_rate'], '90.0')
            self.assertEqual(rows[0]['assertion_success_rate'], '95.0')
            self.assertEqual(rows[0]['html_report'], 'col1.html')
            self.assertEqual(rows[0]['json_report'], 'col1.json')
        os.unlink(tmp.name)

    def test_write_plaintext_table(self):
        with tempfile.NamedTemporaryFile(mode='r+', delete=False, suffix='.txt') as tmp:
            reporting.write_plaintext_table(self.results, tmp.name)
            tmp.seek(0)
            content = tmp.read()
            self.assertIn('Collection', content)
            self.assertIn('col1', content)
            self.assertIn('OK', content)
            self.assertIn('10', content)
            self.assertIn('1', content)
            self.assertIn('20', content)
            self.assertIn('2', content)
            self.assertIn('90.0%', content)
            self.assertIn('95.0%', content)
        os.unlink(tmp.name)

    def test_write_csv_report_permission_error(self):
        # Simula erro de permissão ao abrir arquivo
        import builtins
        original_open = builtins.open
        def raise_permission(*a, **kw):
            raise PermissionError("Permissão negada")
        try:
            builtins.open = raise_permission
            with self.assertRaises(PermissionError):
                reporting.write_csv_report(self.results, '/tmp/forbidden.csv')
        finally:
            builtins.open = original_open

    def test_write_plaintext_table_permission_error(self):
        import builtins
        original_open = builtins.open
        def raise_permission(*a, **kw):
            raise PermissionError("Permissão negada")
        try:
            builtins.open = raise_permission
            with self.assertRaises(PermissionError):
                reporting.write_plaintext_table(self.results, '/tmp/forbidden.txt')
        finally:
            builtins.open = original_open

if __name__ == "__main__":
    unittest.main() 