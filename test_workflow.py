import csv
import json
import os
import smtplib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import Bulk_Send


ROOT = Path(__file__).resolve().parent


class WorkflowTest(unittest.TestCase):
    def run_script(self, directory, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / script), *args],
            cwd=directory, text=True, capture_output=True, check=False,
        )

    def test_demo_generates_and_previews_without_sending(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script(directory, "make_demo.py")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = Path(directory) / "batch"
            result = self.run_script(
                directory, "Bulk_Generate.py", "--inputs", "demo", "--output", str(output)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            recipients = json.loads((output / "recipients.json").read_text(encoding="utf-8"))
            self.assertEqual([row["name"] for row in recipients], ["Alex Example", "Jamie Sample"])
            self.assertEqual([row["file"] for row in recipients], ["0001.pdf", "0002.pdf"])
            for recipient in recipients:
                self.assertTrue((output / recipient["file"]).read_bytes().startswith(b"%PDF-"))

            result = self.run_script(directory, "Bulk_Send.py", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Previewed 2", result.stdout)
            result = self.run_script(directory, "Bulk_Send.py", "--output", str(output), "--send")
            self.assertEqual(result.returncode, 2)
            self.assertIn("fictional recipient addresses", result.stderr)
            self.assertFalse((output / "delivery_log.csv").exists())

    def test_send_pairs_attachments_and_retries_only_failed_deliveries(self):
        settings = {
            "CERT_SMTP_HOST": "smtp.example.invalid",
            "CERT_EMAIL": "sender@example.com",
            "CERT_EMAIL_PASS": "test-only-password",
        }
        recipients = [
            {"name": "Same Name", "email": "first@example.com", "file": "0001.pdf"},
            {"name": "Same Name", "email": "second@example.com", "file": "0002.pdf"},
        ]

        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            for index, recipient in enumerate(recipients, start=1):
                (batch / recipient["file"]).write_bytes(f"attachment {index}".encode())
            (batch / "recipients.json").write_text(json.dumps(recipients), encoding="utf-8")
            with (
                patch.dict(os.environ, settings, clear=True),
                patch.object(sys, "argv", ["Bulk_Send.py", "--output", directory, "--send"]),
                patch.object(Bulk_Send.smtplib, "SMTP_SSL") as smtp_ssl,
            ):
                send_message = smtp_ssl.return_value.__enter__.return_value.send_message
                send_message.side_effect = [None, smtplib.SMTPDataError(451, b"test failure")]
                with self.assertRaisesRegex(SystemExit, "Delivery failed for 1"):
                    Bulk_Send.main()
                send_message.side_effect = None
                Bulk_Send.main()

                messages = [call.args[0] for call in send_message.call_args_list]
                self.assertEqual(
                    [str(message["To"]) for message in messages],
                    ["first@example.com", "second@example.com", "second@example.com"],
                )
                self.assertEqual(
                    [next(message.iter_attachments()).get_payload(decode=True) for message in messages],
                    [b"attachment 1", b"attachment 2", b"attachment 2"],
                )

            with (batch / "delivery_log.csv").open(newline="", encoding="utf-8") as stream:
                self.assertEqual(
                    list(csv.reader(stream)),
                    [["file", "status"], ["0001.pdf", "SENT"], ["0002.pdf", "FAILED"],
                     ["0002.pdf", "SENT"]],
                )


if __name__ == "__main__":
    unittest.main()
