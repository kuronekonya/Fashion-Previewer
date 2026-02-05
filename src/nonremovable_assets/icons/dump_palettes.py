# dump_palettes.py
# Double-click to run. No args. No prompts.
#
# OUTPUT: palettes_dump_icon.md
#
# FORMAT:
#   # Chr001
#   ## Hoodie
#   Index 112
#   Icon: 255, 238, 180
#
# - Groups by Chr### (found in folder path OR filename)
# - Sorts by chr numeric (Chr001, Chr002, ...)
# - Ignores keyed-out colors (exact + range)
# - Does NOT group by parent folder name like "PAL"

from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import re

OUTPUT_NAME = "palettes_dump_icon.md"

# ----- keyed-out rules -----
EXACT_KEYED = {
    (255, 0, 255),
    (0, 255, 0),
    (184, 219, 184),
}

def is_keyed_out(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    if rgb in EXACT_KEYED:
        return True
    # Range keyed-out: 0~32, 255, 0~32
    if 0 <= r <= 32 and g == 255 and 0 <= b <= 32:
        return True
    return False

# Find chr### in folder names or filenames
CHR_RE = re.compile(r"\bchr\s*0*(\d{1,3})\b", re.IGNORECASE)

def find_chr_group(p: Path) -> tuple[int, str]:
    """
    Returns (chr_number, 'Chr###') for grouping/sorting.
    Looks in:
      1) every directory name in the path
      2) the filename
    If not found, returns (999999, 'ChrUNKNOWN')
    """
    # 1) scan path parts first (best signal)
    for part in p.parts:
        m = CHR_RE.search(part)
        if m:
            n = int(m.group(1))
            return n, f"Chr{n:03d}"

    # 2) scan filename
    m = CHR_RE.search(p.stem)
    if m:
        n = int(m.group(1))
        return n, f"Chr{n:03d}"

    return 999999, "ChrUNKNOWN"

def natural_name_key(name: str):
    """
    Natural-ish sort so names like w2 < w10.
    If no numbers, falls back to lowercase.
    """
    parts = re.split(r"(\d+)", name.lower())
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key

# ---------------------------
# PAL parsing (supports RIFF PAL, JASC-PAL, raw 768)
# ---------------------------

def parse_jasc_pal(data: bytes):
    text = data.decode("ascii", errors="strict").replace("\r\n", "\n").strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines or lines[0] != "JASC-PAL":
        raise ValueError
    count = int(lines[2])
    colors = []
    for ln in lines[3:]:
        r, g, b = map(int, ln.split()[:3])
        colors.append((r, g, b))
        if len(colors) == count:
            break
    return colors

def parse_riff_pal(data: bytes):
    if len(data) < 24 or data[0:4] != b"RIFF" or data[8:12] != b"PAL ":
        raise ValueError
    i = 12
    pal = None
    while i + 8 <= len(data):
        cid = data[i:i+4]
        size = int.from_bytes(data[i+4:i+8], "little")
        i += 8
        if i + size > len(data):
            raise ValueError
        if cid == b"data":
            pal = data[i:i+size]
            break
        i += size + (size % 2)
    if pal is None or len(pal) < 4:
        raise ValueError

    n = int.from_bytes(pal[2:4], "little")
    colors = []
    for k in range(n):
        r = pal[4 + k*4 + 0]
        g = pal[4 + k*4 + 1]
        b = pal[4 + k*4 + 2]
        colors.append((r, g, b))
    return colors

def parse_raw_768(data: bytes):
    if len(data) != 768:
        raise ValueError
    return [(data[i], data[i+1], data[i+2]) for i in range(0, 768, 3)]

def parse_pal(path: Path):
    data = path.read_bytes()
    for fn in (parse_riff_pal, parse_jasc_pal, parse_raw_768):
        try:
            return fn(data)
        except Exception:
            pass
    raise ValueError("Unknown PAL format")

# ---------------------------
# Main
# ---------------------------

def main():
    root = Path(__file__).parent.resolve()
    out_path = root / OUTPUT_NAME

    # chr_number -> (chr_label, list of (item_name, colors))
    groups: dict[int, tuple[str, list[tuple[str, list[tuple[int,int,int]]]]]] = {}

    tmp: dict[int, list[tuple[str, list[tuple[int,int,int]]]]] = defaultdict(list)
    labels: dict[int, str] = {}

    for pal_path in root.rglob("*.pal"):
        try:
            colors = parse_pal(pal_path)
        except Exception:
            continue

        chr_num, chr_label = find_chr_group(pal_path)
        labels[chr_num] = chr_label

        # clothing/item name: just the filename stem (hoodie, gloves, etc.)
        item_name = pal_path.stem

        tmp[chr_num].append((item_name, colors))

    # Write output
    lines: list[str] = []
    for chr_num in sorted(tmp.keys()):
        chr_label = labels.get(chr_num, "ChrUNKNOWN")
        lines.append(f"# {chr_label}\n")

        # Sort items naturally (not dumb alphabetic w10 before w2)
        for item_name, colors in sorted(tmp[chr_num], key=lambda t: natural_name_key(t[0])):
            lines.append(f"## {item_name}\n")

            for idx, rgb in enumerate(colors):
                if is_keyed_out(rgb):
                    continue
                r, g, b = rgb
                lines.append(f"Index {idx}")
                lines.append(f"Icon: {r}, {g}, {b}\n")

        lines.append("")

    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
