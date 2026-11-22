import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from participants import read_participants


def main():
    parser = argparse.ArgumentParser(description="Generate participant certificates.")
    parser.add_argument("--inputs", type=Path, default=Path("private"))
    parser.add_argument("--output", type=Path, default=Path("output_certificates"))
    args = parser.parse_args()

    participants = read_participants(args.inputs / "participants.xlsx")
    layout = json.loads((args.inputs / "layout.json").read_text(encoding="utf-8"))
    font_size = layout["font_size"]
    font = layout.get("font")
    font = (ImageFont.truetype(str(args.inputs / font), font_size)
            if font else ImageFont.load_default(size=font_size))
    with Image.open(args.inputs / "template.png") as image:
        template = image.convert("RGB")

    signatures = []
    for placement in layout["signatures"]:
        with Image.open(args.inputs / placement["file"]) as image:
            signature = image.convert("RGBA")
        if placement.get("remove_white_background"):
            signature.putdata([
                (r, g, b, 0 if min(r, g, b) > 245 else alpha)
                for r, g, b, alpha in signature.getdata()
            ])
        signatures.append((signature.resize(tuple(placement["size"])),
                           tuple(placement["position"])))

    # The workbook stays with the batch so each attachment keeps its recipient.
    args.output.mkdir(parents=True, exist_ok=False)
    for number, (name, _) in enumerate(participants, start=1):
        certificate = template.copy()
        ImageDraw.Draw(certificate).text(
            tuple(layout["name_position"]), name, fill="black", anchor="mm", font=font
        )
        for signature, position in signatures:
            certificate.paste(signature, position, signature)
        certificate.save(args.output / f"{number:04d}.pdf", resolution=300)

    manifest = [
        {"name": name, "email": email, "file": f"{number:04d}.pdf"}
        for number, (name, email) in enumerate(participants, start=1)
    ]
    (args.output / "recipients.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(manifest)} certificate(s) in {args.output}.")


if __name__ == "__main__":
    main()
