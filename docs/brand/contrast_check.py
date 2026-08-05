#!/usr/bin/env python3
"""Verify that the Atlas palette, as this product uses it, meets WCAG 2.2 AA.

Run from CI. Exits non-zero if any shipped pair regresses, so an
accessibility failure breaks the build rather than reaching a passenger.

The palette is read from the vendored token file the application actually
loads — frontend/src/design-system/tokens/tokens.css — so this cannot drift
from what is rendered. Atlas states 44px targets and a non-negotiable focus
ring as its own accessibility floor; this is the part of it a machine can
hold.

Colours here are hex and rgba(), not AF's OKLCH, so this is a hex/rgba ->
linear sRGB converter rather than an OKLCH one. Semantic aliases are `var()`
chains (--text-primary -> --slate-100), which are resolved before
conversion. Where a colour is translucent — Atlas's glass surfaces are
rgba() over the page ground by design — it is composited over --ground
before its luminance is taken, since an alpha value alone is not a
renderable colour.

Both themes are checked. Dark is Atlas's default (declared under a
":root, [data-theme=\"dark\"]" selector, so it is also what an unset
attribute renders); light is declared under "[data-theme=\"light\"]" and is
equally shippable, so a pair that passes in one and fails in the other is
still a failure.

    python docs/brand/contrast_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_DS = Path(__file__).resolve().parents[2] / "frontend/src/design-system"
# Read in load order: the vendored palette, then the product's corrections to
# it. Checking tokens.css alone would report failures the application does
# not actually ship — see overrides.css for what those were.
CSS_SOURCES = [_DS / "tokens/tokens.css", _DS / "overrides.css"]

AA_NORMAL = 4.5  # body text
AA_LARGE = 3.0  # >=24px or >=18.66px bold; also UI component boundaries

_DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;}]+)")
_HEX = re.compile(r"#([0-9a-f]{6})", re.I)
_RGBA = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", re.I
)
_VAR = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*\)", re.I)


def parse_themes(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Split the file into the dark (default) and light token sets.

    Atlas's tokens.css has four kinds of top-level block, told apart by which
    of "dark" / "light" appear in the selector:

      - neither  (plain ":root")                    — shared scale, both themes
      - "dark" only  (":root, [data-theme=dark]")    — dark primitives + semantic
      - "light" only ("[data-theme=light]")          — light primitives + semantic
      - both ("...[data-theme=dark], [data-theme=light]") — the short-alias
        block, which includes a bare ":root" in its selector list and so,
        like the shared scale, always applies regardless of theme

    This is tailored to that specific shape rather than a general cascade
    simulator — it would not handle an arbitrary stylesheet correctly.
    """
    dark: dict[str, str] = {}
    light_overrides: dict[str, str] = {}

    for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = block.group(1).strip(), block.group(2)
        if selector.startswith("@"):
            continue
        decls = dict(_DECL.findall(body))
        for k in decls:
            decls[k] = decls[k].strip()

        # Classify on the selector alone, with its leading comment stripped —
        # the divider comments are prose ("hairlines go dark") that can
        # contain either word incidentally, which previously misclassified
        # the light block as also applying to dark.
        bare_selector = re.sub(r"/\*.*?\*/", "", selector, flags=re.S)
        has_dark = "dark" in bare_selector
        has_light = "light" in bare_selector
        if has_dark and has_light:
            dark.update(decls)
            light_overrides.update(decls)
        elif has_light:
            light_overrides.update(decls)
        else:
            # Either "dark"-only or theme-agnostic (plain :root) — both are
            # part of the dark palette, and the agnostic ones are shared.
            dark.update(decls)

    light = {**dark, **light_overrides}
    return dark, light


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


def hex_to_linear_srgb(value: str) -> tuple[float, float, float]:
    h = value.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(  # type: ignore[return-value]
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    )


def to_linear(value: str) -> tuple[tuple[float, float, float], float] | None:
    """Return (linear rgb, alpha), or None if the value is not a colour."""
    match = _HEX.search(value)
    if match:
        return hex_to_linear_srgb(f"#{match.group(1)}"), 1.0
    match = _RGBA.search(value)
    if match:
        r, g, b = (float(match.group(i)) / 255 for i in (1, 2, 3))
        alpha = float(match.group(4)) if match.group(4) else 1.0
        srgb = (r, g, b)
        linear = tuple(
            c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb
        )
        return linear, alpha  # type: ignore[return-value]
    return None


def luminance(rgb: tuple[float, float, float]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def opaque_rgb(
    token: str, palette: dict[str, str], ground: tuple[float, float, float]
) -> tuple[float, float, float] | None:
    """Resolve a token to a fully opaque linear-sRGB colour.

    Atlas's glass surfaces are rgba() overlays by design — a panel's actual
    rendered colour depends on what is behind it. This composites over
    --ground once, which is where most of this product's panels sit; it is
    an approximation (the real backdrop is the bloom gradient, which is
    brighter, so this is the more conservative of the two), not a renderer.
    """
    value = resolve(token, palette)
    if value is None:
        return None
    parsed = to_linear(value)
    if parsed is None:
        return None
    (r, g, b), alpha = parsed
    if alpha >= 1.0:
        return (r, g, b)
    gr, gg, gb = ground
    return (r * alpha + gr * (1 - alpha), g * alpha + gg * (1 - alpha), b * alpha + gb * (1 - alpha))


def contrast(fg: str, bg: str, palette: dict[str, str]) -> float | None:
    ground_value = resolve("ground", palette)
    ground_parsed = to_linear(ground_value) if ground_value else None
    ground_rgb = ground_parsed[0] if ground_parsed else (0.0, 0.0, 0.0)

    fg_rgb = opaque_rgb(fg, palette, ground_rgb)
    bg_rgb = opaque_rgb(bg, palette, ground_rgb)
    if fg_rgb is None or bg_rgb is None:
        return None

    lighter, darker = sorted((luminance(fg_rgb), luminance(bg_rgb)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# (foreground, background, minimum, what it is on screen)
REQUIRED: list[tuple[str, str, float, str]] = [
    ("text-primary", "ground", AA_NORMAL, "Headings and the nav wordmark on the page ground"),
    ("text-secondary", "ground", AA_NORMAL, "Body copy on the page ground"),
    ("text-tertiary", "ground", AA_NORMAL, "Index labels and captions on the page ground"),
    ("text-primary", "surface", AA_NORMAL, "Flight codes and figures on a glass panel"),
    ("text-secondary", "surface", AA_NORMAL, "Body copy, metadata and index labels on a glass panel"),
    ("text-warning", "surface", AA_NORMAL, "Low-seat warning on a flight card"),
    ("text-on-accent", "fill-accent", AA_NORMAL, "Label on the primary action — chartreuse"),
    ("text-link", "ground", AA_NORMAL, "Links — Create one, Log in"),
    ("text-success", "tint-success", AA_NORMAL, "Confirmed booking badge"),
    ("text-danger", "tint-danger", AA_NORMAL, "Cancelled badge and error banners"),
    ("text-info", "tint-info", AA_NORMAL, "Demonstration notice in the booking dialog"),
    # SC 1.4.11 applies to the boundary of a control, not to decorative
    # dividers — this is the selected-fare-card border and the focus ring,
    # deliberately not --border-subtle, which carries panel edges.
    # --border-accent is tested against "surface", not "ground": the only
    # place it renders is the selected-fare card inside the booking dialog,
    # itself a glass panel, and that background is the more fragile of the
    # two (see overrides.css).
    ("border-accent", "surface", AA_LARGE, "Selected fare card border"),
    ("focus-ring", "ground", AA_LARGE, "Focus ring against the page ground"),
    ("focus-ring", "surface", AA_LARGE, "Focus ring against a glass panel"),
]


def main() -> int:
    missing = [p for p in CSS_SOURCES if not p.exists()]
    if missing:
        print(f"error: palette source not found: {missing[0]}", file=sys.stderr)
        return 2

    css = "\n".join(p.read_text(encoding="utf-8") for p in CSS_SOURCES)
    themes = dict(zip(("dark", "light"), parse_themes(css)))

    failures = 0
    print(f"Atlas palette contrast — {len(REQUIRED)} pairs x 2 themes, WCAG 2.2 AA")

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
