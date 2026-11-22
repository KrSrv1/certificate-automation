# Workshop Certificate Automation

Turn an Excel participant list into personalized PDF certificates and optionally email one attachment to each recipient.

## Run the demo

From the repository root, use Python 3.10 or later.

```sh
python -m pip install -r requirements.txt
python make_demo.py
python Bulk_Generate.py --inputs demo --output demo/certificates
python Bulk_Send.py --output demo/certificates
```

Open the two PDFs in `demo/certificates`. Preview checks the attachments and prints the batch count without connecting to an email provider. The demo uses fictional names, reserved addresses, and a generic certificate template.

## Use your own materials

Create a local `private/` directory. Add a `participants.xlsx` workbook with `Name` and `Email` headers on its first sheet, a `template.png` image, and any signature images you have permission to use. Copy `demo/layout.json` into `private/` and adjust it for the new template.

- `name_position` gives the center of the name in pixels, measured from the top-left of the template.
- `font_size` sets the name size in pixels. An optional `font` key can point to a local font file relative to `private/`.
- Each `signatures` entry gives a filename, top-left position, and image size in pixels. Set `remove_white_background` to `true` for images with white backgrounds. Use an empty list for unsigned certificates.

```sh
python Bulk_Generate.py
python Bulk_Send.py
```

Use a new output directory for each batch via `--output`, and pass the same location to both commands. Each batch stores numbered PDFs and a private `recipients.json` that preserves the mapping to names and email addresses. Keep the entire batch directory private.

## Send certificates

Set these environment variables locally.

| Variable | Value |
| --- | --- |
| `CERT_SMTP_HOST` | Your provider's implicit TLS SMTP host |
| `CERT_SMTP_PORT` | Optional port, defaults to 465 |
| `CERT_EMAIL` | Sender address and SMTP login |
| `CERT_EMAIL_PASS` | The SMTP or app password accepted by your provider |

```sh
python Bulk_Send.py --send
```

Use `--subject` to customize the subject. The batch's `delivery_log.csv` records successful and failed sends. A rerun skips attachments recorded as sent. After an interrupted connection, check with your mail provider before retrying an unlogged message, since it may already have been accepted.

## Share the repository

The ignore rules allow only the listed source files and documentation at the repository root. Run `git status --short` and `git ls-files` here before pushing.
