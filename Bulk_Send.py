import argparse
import csv
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Preview or email a certificate batch.")
    parser.add_argument("--output", type=Path, default=Path("output_certificates"))
    parser.add_argument("--send", action="store_true", help="Deliver via SMTP.")
    parser.add_argument("--subject", default="Your certificate of participation")
    args = parser.parse_args()
    recipients = json.loads((args.output / "recipients.json").read_text(encoding="utf-8"))
    for recipient in recipients:
        filename = recipient["file"]
        if Path(filename).name != filename or not (args.output / filename).is_file():
            parser.error("The batch contains a missing or invalid attachment.")

    if not args.send:
        print(f"Previewed {len(recipients)} certificate email(s).")
        return

    if any(recipient["email"].lower().endswith(".invalid") for recipient in recipients):
        parser.error("This batch contains fictional recipient addresses. Use preview mode.")

    settings = [os.getenv(key) for key in ("CERT_SMTP_HOST", "CERT_EMAIL", "CERT_EMAIL_PASS")]
    if not all(settings):
        parser.error("Set CERT_SMTP_HOST, CERT_EMAIL, and CERT_EMAIL_PASS to send.")
    host, sender, password = settings
    port = int(os.getenv("CERT_SMTP_PORT", "465"))
    log_path = args.output / "delivery_log.csv"
    sent = set()
    if log_path.exists():
        with log_path.open(newline="", encoding="utf-8") as stream:
            sent = {row["file"] for row in csv.DictReader(stream) if row["status"] == "SENT"}

    failures = 0
    with smtplib.SMTP_SSL(host, port, timeout=30, context=ssl.create_default_context()) as smtp:
        smtp.login(sender, password)
        with log_path.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            if stream.tell() == 0:
                writer.writerow(("file", "status"))
            for recipient in recipients:
                filename = recipient["file"]
                if filename in sent:
                    continue
                message = EmailMessage()
                message["From"] = sender
                message["To"] = recipient["email"]
                message["Subject"] = args.subject
                message.set_content(
                    f"Dear {recipient['name']},\n\nPlease find your certificate attached.\n"
                )
                message.add_attachment((args.output / filename).read_bytes(),
                                       maintype="application", subtype="pdf", filename=filename)
                try:
                    smtp.send_message(message)
                except (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused):
                    writer.writerow((filename, "FAILED"))
                    failures += 1
                else:
                    writer.writerow((filename, "SENT"))
                stream.flush()
    if failures:
        raise SystemExit(f"Delivery failed for {failures} certificate(s). See the batch log.")


if __name__ == "__main__":
    main()
