from pathlib import Path

import pikepdf

def unlock_pdf(path: Path, suffix="_unlocked"):
    with pikepdf.Pdf.open(path) as pdf:
        save_name = path.parent / f"{path.stem}{suffix}.pdf"
        pdf.save(save_name)
