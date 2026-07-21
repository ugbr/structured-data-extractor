"""Load receipts from the SROIE dataset.

Each receipt id (like "000") has three files under data/documents/sroie/:
  img/000.jpg   the scanned photo
  box/000.csv   OCR output, one line per text region: 8 coords then the text
  key/000.json  the label: company, date, address, total
"""

import json
from pathlib import Path

# project root is three parents up from this file (src/extractor/sroie.py)
DATA_DIR = Path(__file__).parents[2] / "data" / "documents" / "sroie"


def load_label(receipt_id: str) -> dict:
    """Read key/<id>.json and return the label as a dict."""
    path = DATA_DIR / "key" / f"{receipt_id}.json"
    s = path.read_text()
    data = json.loads(s)
    return data


def load_text(receipt_id: str) -> str:
    """Read box/<id>.csv and return the OCR text as one string.

    Each line is: x1,y1,x2,y2,x3,y3,x4,y4,<the recognized text>
    We want just the text from each line, joined top to bottom.
    """
    path = DATA_DIR / "box" / f"{receipt_id}.csv"
    lines = path.read_text().splitlines()
    texts = []
    for line in lines:
        parts = line.split(",")
        s = ",".join(parts[8:])
        texts.append(s)
    return "\n".join(texts)
