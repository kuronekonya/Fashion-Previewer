# dump_palettes_ultimate.py
# Double-click to run. No args.
#
# INPUT:  palettes_dump_icon.md (from dump_palettes.py)
# OUTPUT: palettes_dump_icon_with_base.md
#
# For each section (# Chr### -> ## ClothingItem):
# - Find ONE best-matching base .pal from a user-chosen directory (recursive)
# - Compare ONLY indices listed in the icon MD (no extra indices)
# - Enforce ~95% closeness before accepting a base pal

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import tkinter as tk
from tkinter import filedialog, messagebox

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
    if 0 <= r <= 32 and g == 255 and 0 <= b <= 32:
        return True
    return False

# ----- matching strictness -----
# "Close enough" per index: max channel delta <= this tolerance
TOL = 12
# Need at least this fraction of indices to be "close"
REQUIRED_CLOSE_RATIO = 0.95
# Also require at least N indices compared, to avoid weak matches
MIN_COMPARED = 8

# ---------------------------
# PAL parsing (same 3 formats)
# ---------------------------

def parse_jasc_pal(data: bytes) -> List[Tuple[int, int, int]]:
    text = data.decode("ascii", errors="strict").replace("\r\n", "\n").strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines or lines[0] != "JASC-PAL":
        raise ValueError
    count = int(lines[2])
    colors: List[Tuple[int, int, int]] = []
    for ln in lines[3:]:
        parts = ln.split()
        if len(parts) < 3:
            continue
        r, g, b = map(int, parts[:3])
        colors.append((r, g, b))
        if len(colors) >= count:
            break
    if len(colors) != count:
        raise ValueError
    return colors

def parse_riff_pal(data: bytes) -> List[Tuple[int, int, int]]:
    if len(data) < 24 or data[0:4] != b"RIFF" or data[8:12] != b"PAL ":
        raise ValueError

    i = 12
    pal_chunk = None
    while i + 8 <= len(data):
        cid = data[i:i+4]
        size = int.from_bytes(data[i+4:i+8], "little")
        i += 8
        if i + size > len(data):
            raise ValueError
        if cid == b"data":
            pal_chunk = data[i:i+size]
            break
        i += size + (size % 2)

    if pal_chunk is None or len(pal_chunk) < 4:
        raise ValueError

    n = int.from_bytes(pal_chunk[2:4], "little")
    need = 4 + n * 4
    if len(pal_chunk) < need:
        raise ValueError

    colors: List[Tuple[int, int, int]] = []
    for k in range(n):
        r = pal_chunk[4 + k*4 + 0]
        g = pal_chunk[4 + k*4 + 1]
        b = pal_chunk[4 + k*4 + 2]
        colors.append((r, g, b))
    return colors

def parse_raw_768(data: bytes) -> List[Tuple[int, int, int]]:
    if len(data) != 768:
        raise ValueError
    return [(data[i], data[i+1], data[i+2]) for i in range(0, 768, 3)]

def parse_pal_file(path: Path) -> List[Tuple[int, int, int]]:
    data = path.read_bytes()
    for fn in (parse_riff_pal, parse_jasc_pal, parse_raw_768):
        try:
            return fn(data)
        except Exception:
            pass
    raise ValueError("Unknown .pal format")

# ---------------------------
# Parse icon markdown (new format)
# ---------------------------

CHR_RE = re.compile(r"\bchr\s*0*(\d{1,3})\b", re.IGNORECASE)
INDEX_RE = re.compile(r"^Index\s+(\d+)\s*$", re.IGNORECASE)
ICON_RE  = re.compile(r"^Icon:\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*$", re.IGNORECASE)

@dataclass
class Section:
    chr_heading: str        # "# Chr001"
    item_name: str          # "## Gloves"
    icon_indices: Dict[int, Tuple[int,int,int]]  # idx -> rgb

def extract_chr_prefix(h: str) -> Optional[str]:
    m = CHR_RE.search(h)
    if not m:
        return None
    return f"chr{int(m.group(1)):03d}"

def parse_icon_md(md_text: str) -> List[Section]:
    lines = md_text.splitlines()
    out: List[Section] = []

    current_chr: Optional[str] = None
    current_item: Optional[str] = None
    indices: Dict[int, Tuple[int,int,int]] = {}
    pending_idx: Optional[int] = None

    def flush():
        nonlocal current_chr, current_item, indices, pending_idx
        if current_chr and current_item and indices:
            out.append(Section(current_chr, current_item, dict(indices)))
        current_item = None
        indices = {}
        pending_idx = None

    for raw in lines:
        line = raw.strip()

        if line.startswith("# "):
            flush()
            current_chr = line[2:].strip()
            continue

        if line.startswith("## "):
            flush()
            current_item = line[3:].strip()
            continue

        m = INDEX_RE.match(line)
        if m:
            pending_idx = int(m.group(1))
            continue

        m = ICON_RE.match(line)
        if m and pending_idx is not None:
            r, g, b = map(int, m.groups())
            rgb = (r, g, b)
            if not is_keyed_out(rgb):
                indices[pending_idx] = rgb
            pending_idx = None
            continue

    flush()
    return out

# ---------------------------
# Scoring + selection
# ---------------------------

def max_channel_delta(a: Tuple[int,int,int], b: Tuple[int,int,int]) -> int:
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

@dataclass
class Match:
    pal_path: Path
    compared: int
    close_count: int
    close_ratio: float
    total_max_delta: int  # tie-breaker: smaller is better

def score_candidate(section: Section, base_colors: List[Tuple[int,int,int]]) -> Match:
    compared = 0
    close_count = 0
    total_max_delta = 0

    for idx, icon_rgb in section.icon_indices.items():
        if 0 <= idx < len(base_colors):
            base_rgb = base_colors[idx]
            if is_keyed_out(base_rgb):
                continue
            compared += 1
            d = max_channel_delta(base_rgb, icon_rgb)
            total_max_delta += d
            if d <= TOL:
                close_count += 1

    ratio = (close_count / compared) if compared else 0.0
    return compared, close_count, ratio, total_max_delta

def pick_best_base(section: Section, candidates: List[Path]) -> Optional[Match]:
    best: Optional[Match] = None

    for p in candidates:
        try:
            base_colors = parse_pal_file(p)
        except Exception:
            continue

        compared, close_count, ratio, total_max_delta = score_candidate(section, base_colors)
        if compared < MIN_COMPARED:
            continue

        m = Match(p, compared, close_count, ratio, total_max_delta)

        if best is None:
            best = m
            continue

        # Primary: higher close ratio
        if m.close_ratio > best.close_ratio:
            best = m
            continue

        # Secondary: if same ratio, smaller total delta
        if m.close_ratio == best.close_ratio and m.total_max_delta < best.total_max_delta:
            best = m
            continue

        # Tertiary: stable by name
        if (m.close_ratio == best.close_ratio
            and m.total_max_delta == best.total_max_delta
            and m.pal_path.name.lower() < best.pal_path.name.lower()):
            best = m

    # Enforce 95% rule
    if best and best.close_ratio >= REQUIRED_CLOSE_RATIO:
        return best
    return best  # still return best so you can see the nearest, but we’ll label it if under threshold

# ---------------------------
# Output
# ---------------------------

def build_output(sections: List[Section], base_dir: Path) -> str:
    all_base = sorted(base_dir.rglob("*.pal"))
    if not all_base:
        raise RuntimeError("No .pal files found in base directory.")

    out_lines: List[str] = []
    current_chr: Optional[str] = None

    # preserve section order from icon MD (no resorting!)
    for sec in sections:
        if sec.chr_heading != current_chr:
            current_chr = sec.chr_heading
            out_lines.append(f"# {current_chr}")
            out_lines.append("")

        out_lines.append(f"## {sec.item_name}")

        chr_prefix = extract_chr_prefix(sec.chr_heading)  # e.g. chr001
        candidates = all_base
        if chr_prefix:
            filtered = [p for p in all_base if chr_prefix in p.name.lower()]
            if filtered:
                candidates = filtered

        best = pick_best_base(sec, candidates)
        chosen_name = "(no match)"
        base_colors: Optional[List[Tuple[int,int,int]]] = None

        if best:
            chosen_name = best.pal_path.name
            try:
                base_colors = parse_pal_file(best.pal_path)
            except Exception:
                base_colors = None

            # If under threshold, mark it clearly
            if best.close_ratio < REQUIRED_CLOSE_RATIO:
                out_lines.append(f"_Best base guess: {chosen_name} (ONLY {best.close_ratio*100:.1f}% within tol={TOL})_")
            else:
                out_lines.append(f"_Base pal: {chosen_name} ({best.close_ratio*100:.1f}% within tol={TOL})_")

        out_lines.append("")

        # print only indices listed in the icon MD
        for idx in sorted(sec.icon_indices.keys()):
            icon_rgb = sec.icon_indices[idx]

            out_lines.append(f"Index {idx}")

            if base_colors and 0 <= idx < len(base_colors):
                b_rgb = base_colors[idx]
                if is_keyed_out(b_rgb):
                    # if base has a keyed-out at this index, show N/A
                    out_lines.append("Base: N/A")
                else:
                    out_lines.append(f"Base: {b_rgb[0]}, {b_rgb[1]}, {b_rgb[2]}")
            else:
                out_lines.append("Base: N/A")

            out_lines.append(f"Icon: {icon_rgb[0]}, {icon_rgb[1]}, {icon_rgb[2]}")
            out_lines.append("")

        out_lines.append("")

    return "\n".join(out_lines).rstrip() + "\n"

def main():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    icon_md_path = filedialog.askopenfilename(
        title="Select palettes_dump_icon.md (from dump_palettes.py)",
        filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
    )
    if not icon_md_path:
        return

    base_dir = filedialog.askdirectory(
        title="Select BASE palette folder to search recursively (.pal)"
    )
    if not base_dir:
        return

    icon_md_path = Path(icon_md_path)
    base_dir = Path(base_dir)

    try:
        md_text = icon_md_path.read_text(encoding="utf-8")
    except Exception as e:
        messagebox.showerror("Error", f"Could not read icon MD:\n{e}")
        return

    sections = parse_icon_md(md_text)
    if not sections:
        messagebox.showerror("Error", "No sections found in the icon MD. Make sure it was generated by dump_palettes.py.")
        return

    try:
        out_text = build_output(sections, base_dir)
    except Exception as e:
        messagebox.showerror("Error", f"Failed:\n{e}")
        return

    out_path = icon_md_path.with_name(icon_md_path.stem + "_with_base.md")
    try:
        out_path.write_text(out_text, encoding="utf-8")
    except Exception as e:
        messagebox.showerror("Error", f"Could not write output:\n{e}")
        return

    messagebox.showinfo("Done", f"Created:\n{out_path}")

if __name__ == "__main__":
    main()
