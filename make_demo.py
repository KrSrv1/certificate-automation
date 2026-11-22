import json
from pathlib import Path

from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont


def main():
    demo = Path("demo")
    demo.mkdir(exist_ok=False)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Participants"
    sheet.append(("Name", "Email"))
    sheet.append(("Alex Example", "alex@example.invalid"))
    sheet.append(("Jamie Sample", "jamie@example.invalid"))
    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 28
    workbook.save(demo / "participants.xlsx")

    template = Image.new("RGB", (1500, 1000), "#f8f5eb")
    draw = ImageDraw.Draw(template)
    draw.rectangle((40, 40, 1460, 960), outline="#344d62", width=5)
    for y, label, size in (
        (220, "Certificate of Participation", 72),
        (350, "Presented to", 36),
        (575, "For completing the Example Workshop", 38),
        (870, "DEMO", 30),
    ):
        draw.text((750, y), label, anchor="mm", fill="#344d62",
                  font=ImageFont.load_default(size=size))
    template.save(demo / "template.png")

    signature = Image.new("RGBA", (250, 70))
    ImageDraw.Draw(signature).text(
        (125, 35), "Demo signature", anchor="mm", fill="#344d62",
        font=ImageFont.load_default(size=29)
    )
    signature.save(demo / "demo-signature.png")
    layout = {
        "name_position": [750, 460],
        "font_size": 62,
        "signatures": [
            {"file": "demo-signature.png", "position": [625, 725], "size": [250, 70]}
        ],
    }
    (demo / "layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
