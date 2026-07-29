#!/usr/bin/env python3
"""Verify that the brand palette meets WCAG 2.2 AA.

Run from CI. Exits non-zero if any shipped colour pair regresses below its
required ratio, so an accessibility failure breaks the build rather than
reaching a passenger.

The palette is read from frontend/src/index.css — the same tokens the
application uses — so this cannot drift from what is actually rendered.

    python docs/brand/contrast_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "index.css"

AA_NORMAL = 4.5  # body text
AA_LARGE = 3.0  # >=24px, or >=18.66px bold; also UI component boundaries


def parse_palette(css: str) -> dict[str, str]:
    return {
        name: value
        for name, value in re.findall(
            r"--color-([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", css
        )
    }


def relative_luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(a: str, b: str) -> float:
    lighter, darker = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# (foreground token, background token, minimum, description)
REQUIRED: list[tuple[str, str, float, str]] = [
    ("dark", "surface", AA_NORMAL, "Body copy on cards"),
    ("dark", "accent", AA_NORMAL, "Body copy on page background"),
    ("primary", "surface", AA_NORMAL, "Headings on cards"),
    ("surface", "primary", AA_NORMAL, "Nav and hero text on navy"),
    ("surface", "secondary", AA_NORMAL, "Text on secondary buttons"),
    ("surface", "signal", AA_NORMAL, "Text on the primary call to action"),
    ("signal-light", "primary", AA_NORMAL, "Ochre on navy surfaces"),
    ("danger", "surface", AA_NORMAL, "Error text"),
    ("success", "surface", AA_NORMAL, "Confirmation text"),
    ("warning", "surface", AA_NORMAL, "Warning text"),
    ("secondary", "surface", AA_LARGE, "Focus ring against a card"),
]


def main() -> int:
    if not CSS.exists():
        print(f"error: palette source not found at {CSS}", file=sys.stderr)
        return 2

    palette = parse_palette(CSS.read_text(encoding="utf-8"))
    failures = 0

    print(f"Brand palette contrast — {len(REQUIRED)} pairs, WCAG 2.2 AA\n")
    for fg, bg, minimum, description in REQUIRED:
        if fg not in palette or bg not in palette:
            missing = fg if fg not in palette else bg
            print(f"  MISSING  --color-{missing} is not defined in index.css")
            failures += 1
            continue

        ratio = contrast_ratio(palette[fg], palette[bg])
        ok = ratio >= minimum
        failures += not ok
        print(
            f"  {'ok  ' if ok else 'FAIL'}  {ratio:5.2f}:1  (min {minimum})  "
            f"{fg} on {bg} — {description}"
        )

    if failures:
        print(f"\n{failures} pair(s) below the required ratio.", file=sys.stderr)
        return 1

    print("\nAll pairs pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
