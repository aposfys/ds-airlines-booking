#!/usr/bin/env python3
"""Verify that the AF palette, as this product uses it, meets WCAG 2.2 AA.

Run from CI. Exits non-zero if any shipped pair regresses, so an
accessibility failure breaks the build rather than reaching a passenger.

The palette is read from the vendored token file the application actually
loads — frontend/src/design-system/tokens/color.css — so this cannot drift
from what is rendered. AF states its accessibility standard as
non-negotiable; this is the part of it a machine can hold.

Colours are OKLCH, so this converts OKLCH -> OKLab -> linear sRGB and takes
the WCAG relative luminance from the linear values. Semantic aliases are
`var()` chains (--text-strong -> --ink-0), which are resolved before
conversion.

Both themes are checked. The dark theme is AF's default; the light theme is
declared under [data-theme="light"] and is equally shippable, so a pair that
passes in one and fails in the other is still a failure.

    python docs/brand/contrast_check.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

_DS = Path(__file__).resolve().parents[2] / "frontend/src/design-system"
# Read in load order: the vendored palette, then the product's corrections to
# it. Checking color.css alone would report failures the application does not
# actually ship.
CSS_SOURCES = [_DS / "tokens/color.css", _DS / "overrides.css"]

AA_NORMAL = 4.5  # body text
AA_LARGE = 3.0  # >=24px or >=18.66px bold; also UI component boundaries

_DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;}]+)")
_OKLCH = re.compile(
    r"oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*(?:/\s*([\d.]+)\s*)?\)", re.I
)
_VAR = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*\)", re.I)


def parse_themes(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Split the file into the dark (default) and light token sets.

    AF declares the dark theme across two :root blocks — base ramps, then
    semantic aliases — and the light theme under a [data-theme] selector.
    Later declarations win, matching the cascade.
    """
    dark: dict[str, str] = {}
    light: dict[str, str] = {}

    # Split on top-level selectors; keep it simple because the file is flat.
    for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = block.group(1).strip(), block.group(2)
        target = light if "data-theme" in selector and "light" in selector else dark
        if "data-theme" in selector and "light" not in selector:
            continue
        for name, value in _DECL.findall(body):
            target[name] = value.strip()

    # The light theme overrides only the aliases it restates; everything else
    # falls through to the base ramps.
    merged_light = {**dark, **light}
    return dark, merged_light


def resolve(token: str, palette: dict[str, str], depth: int = 0) -> str | None:
    """Follow var() chains to a literal colour."""
    if depth > 12:
        return None
    value = palette.get(token.lstrip("-"))
    if value is None:
        return None
    match = _VAR.search(value)
    if match:
        return resolve(match.group(1), palette, depth + 1)
    return value


def oklch_to_linear_srgb(L: float, C: float, H: float) -> tuple[float, float, float]:
    h = math.radians(H)
    a, b = C * math.cos(h), C * math.sin(h)

    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3

    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    # Clamp out-of-gamut values, as a display would.
    return tuple(min(1.0, max(0.0, c)) for c in (r, g, bl))  # type: ignore[return-value]


def hex_to_linear_srgb(value: str) -> tuple[float, float, float]:
    h = value.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(  # type: ignore[return-value]
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    )


def to_linear(value: str) -> tuple[tuple[float, float, float], float] | None:
    """Return (linear rgb, alpha), or None if the value is not a colour."""
    match = _OKLCH.search(value)
    if match:
        L, C, H = (float(match.group(i)) for i in (1, 2, 3))
        alpha = float(match.group(4)) if match.group(4) else 1.0
        return oklch_to_linear_srgb(L, C, H), alpha
    if value.strip().startswith("#"):
        return hex_to_linear_srgb(value.strip()), 1.0
    return None


def luminance(rgb: tuple[float, float, float]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def contrast(fg: str, bg: str, palette: dict[str, str]) -> float | None:
    fg_value, bg_value = resolve(fg, palette), resolve(bg, palette)
    if fg_value is None or bg_value is None:
        return None

    fg_colour, bg_colour = to_linear(fg_value), to_linear(bg_value)
    if fg_colour is None or bg_colour is None:
        return None

    (fr, fg_, fb), alpha = fg_colour
    (br, bg_, bb), _ = bg_colour

    # A translucent foreground composites over its background before the
    # contrast is meaningful.
    if alpha < 1.0:
        fr = fr * alpha + br * (1 - alpha)
        fg_ = fg_ * alpha + bg_ * (1 - alpha)
        fb = fb * alpha + bb * (1 - alpha)

    lighter, darker = sorted(
        (luminance((fr, fg_, fb)), luminance((br, bg_, bb))), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


# (foreground, background, minimum, what it is on screen)
REQUIRED: list[tuple[str, str, float, str]] = [
    ("text-strong", "bg-base", AA_NORMAL, "Headings on the page ground"),
    ("text-body", "bg-base", AA_NORMAL, "Body copy on the page ground"),
    ("text-muted", "bg-base", AA_NORMAL, "Secondary copy on the page ground"),
    ("text-strong", "surface-card", AA_NORMAL, "Flight and booking panels"),
    ("text-body", "surface-card", AA_NORMAL, "Body copy in panels"),
    ("text-muted", "surface-card", AA_NORMAL, "Timestamps and metadata in panels"),
    ("text-strong", "bg-sunken", AA_NORMAL, "Search header and editorial panel"),
    ("text-muted", "bg-sunken", AA_NORMAL, "Search hints"),
    (
        "action-primary-fg",
        "action-primary-bg",
        AA_NORMAL,
        "Label on the primary action — Signal",
    ),
    ("text-editorial", "bg-base", AA_NORMAL, "Brass links and editorial accents"),
    ("text-link", "bg-base", AA_NORMAL, "Links"),
    ("status-positive-fg", "status-positive-bg", AA_NORMAL, "Confirmed booking badge"),
    ("status-critical-fg", "status-critical-bg", AA_NORMAL, "Cancelled badge, errors"),
    ("status-warning-fg", "status-warning-bg", AA_NORMAL, "Low-seat warning"),
    # SC 1.4.11 applies to the boundary of a control, not to decorative
    # dividers — so this tests --action-secondary-border (the outline that
    # marks where a transparent button is) and deliberately not
    # --border-strong, which carries panel edges and separators.
    (
        "action-secondary-border",
        "bg-base",
        AA_LARGE,
        "Secondary button outline",
    ),
    ("focus-ring", "bg-base", AA_LARGE, "Focus ring against the ground"),
    ("focus-ring", "surface-card", AA_LARGE, "Focus ring against a panel"),
]


def main() -> int:
    missing = [p for p in CSS_SOURCES if not p.exists()]
    if missing:
        print(f"error: palette source not found: {missing[0]}", file=sys.stderr)
        return 2

    css = "\n".join(p.read_text(encoding="utf-8") for p in CSS_SOURCES)
    themes = dict(zip(("dark", "light"), parse_themes(css)))

    failures = 0
    print(f"AF palette contrast — {len(REQUIRED)} pairs x 2 themes, WCAG 2.2 AA")

    for theme_name, palette in themes.items():
        print(f"\n  {theme_name} theme")
        for fg, bg, minimum, description in REQUIRED:
            ratio = contrast(fg, bg, palette)
            if ratio is None:
                print(f"    SKIP        --{fg} on --{bg} — not resolvable")
                failures += 1
                continue
            ok = ratio >= minimum
            failures += not ok
            print(
                f"    {'ok  ' if ok else 'FAIL'}  {ratio:5.2f}:1  (min {minimum})  "
                f"{fg} on {bg} — {description}"
            )

    if failures:
        print(f"\n{failures} pair(s) below the required ratio.", file=sys.stderr)
        return 1

    print("\nAll pairs pass in both themes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
