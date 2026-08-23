#!/usr/bin/env python3
"""Verify that the Airy Sky palette, as this product uses it, meets WCAG 2.2 AA.

Run from CI. Exits non-zero if any shipped pair regresses, so an
accessibility failure breaks the build rather than reaching a passenger.

The palette is read from the vendored token file the application actually
loads — frontend/src/design-system/tokens/tokens.css — so this cannot drift
from what is rendered. Atlas states 44px targets and a non-negotiable focus
ring as its own accessibility floor; this is the part of it a machine can
hold.

Colours here are hex and rgba(), so this is a hex/rgba -> linear sRGB
converter rather than an OKLCH one. Semantic aliases are `var()`
chains (--text-primary -> --slate-100), which are resolved before
conversion. Where a colour is translucent — Atlas's glass surfaces are
rgba() over the page ground by design — it is composited over --ground
before its luminance is taken, since an alpha value alone is not a
renderable colour.

Both themes are checked. LIGHT is Airy Sky's default — declared on a bare
":root", so it is also what an unset attribute renders — and dark is the
remap under "[data-theme=\"dark\"]". This is the reverse of Atlas, which it
replaced, and parse_themes() below was flipped to match. A pair that passes
in one theme and fails in the other is still a failure.

Text set over photography is checked too, and differently: a scrim is
composited over --photo-highlight (white) rather than over --ground, because
the backdrop there is an image, and the brightest thing an image can put
under the scrim is a blown-out highlight. That is the case that has to hold.

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

tokens.css has three kinds of top-level block, told apart by which of
    "dark" / "light" appear in the selector:

      - neither  (plain ":root")                     — shared scale AND the
        light palette, since light is the default theme
      - "dark" only  ("[data-theme=dark]")           — the dark remap
      - both ("...[data-theme=dark], [data-theme=light]") — the short-alias
        block, which includes a bare ":root" in its selector list and so
        always applies regardless of theme

    This is tailored to that specific shape rather than a general cascade
    simulator — it would not handle an arbitrary stylesheet correctly.
    """
    light: dict[str, str] = {}
    dark_overrides: dict[str, str] = {}

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
            light.update(decls)
            dark_overrides.update(decls)
        elif has_dark:
            dark_overrides.update(decls)
        else:
            # Either theme-agnostic (plain ":root") or the light palette —
            # light is the default, so a bare ":root" is both.
            light.update(decls)

    dark = {**light, **dark_overrides}
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


def to_srgb(value: str) -> tuple[tuple[float, float, float], float] | None:
    """Return (sRGB 0-1, alpha), or None if the value is not a colour."""
    match = _HEX.search(value)
    if match:
        h = match.group(1)
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)), 1.0  # type: ignore[return-value]
    match = _RGBA.search(value)
    if match:
        rgb = tuple(float(match.group(i)) / 255 for i in (1, 2, 3))
        alpha = float(match.group(4)) if match.group(4) else 1.0
        return rgb, alpha  # type: ignore[return-value]
    return None


def srgb_to_linear(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(  # type: ignore[return-value]
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb
    )


def luminance(rgb: tuple[float, float, float]) -> float:
    """Relative luminance from LINEAR rgb."""
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def opaque_srgb(
    token: str, palette: dict[str, str], backdrop: tuple[float, float, float]
) -> tuple[float, float, float] | None:
    """Resolve a token to an opaque sRGB colour, compositing any alpha.

    The glass surfaces and every scrim are rgba() overlays by design, so a
    panel's rendered colour depends on what is behind it.

    Compositing is done in gamma-encoded sRGB, NOT in linear light, because
    that is what browsers actually do for ordinary sRGB content. Blending in
    linear space instead makes a dark scrim over a bright backdrop resolve
    far darker than it renders — for the card scrim, 3.0:1 rather than the
    6.2:1 a browser produces — which would have driven the scrims much
    heavier than the design needs to clear AA.
    """
    value = resolve(token, palette)
    if value is None:
        return None
    parsed = to_srgb(value)
    if parsed is None:
        return None
    (r, g, b), alpha = parsed
    if alpha >= 1.0:
        return (r, g, b)
    br, bg_, bb = backdrop
    return (
        r * alpha + br * (1 - alpha),
        g * alpha + bg_ * (1 - alpha),
        b * alpha + bb * (1 - alpha),
    )


def contrast(
    fg: str, bg: str, palette: dict[str, str], over: str = "ground"
) -> float | None:
    """Ratio for fg on bg, compositing any translucency over `over`.

    `over` is almost always --ground. It is --photo-highlight for the scrims,
    where the backdrop is an image rather than the page.
    """
    backdrop_value = resolve(over, palette)
    backdrop_parsed = to_srgb(backdrop_value) if backdrop_value else None
    backdrop = backdrop_parsed[0] if backdrop_parsed else (0.0, 0.0, 0.0)

    fg_rgb = opaque_srgb(fg, palette, backdrop)
    bg_rgb = opaque_srgb(bg, palette, backdrop)
    if fg_rgb is None or bg_rgb is None:
        return None

    lighter, darker = sorted(
        (luminance(srgb_to_linear(fg_rgb)), luminance(srgb_to_linear(bg_rgb))),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


# (foreground, background, minimum, backdrop, what it is on screen)
# `backdrop` is what a translucent colour is composited over — the page ground
# for everything that sits on the page, --photo-highlight for anything set
# over an image.
REQUIRED: list[tuple[str, str, float, str, str]] = [
    ("text-primary", "ground", AA_NORMAL, "ground", "Headings and the nav wordmark on the page ground"),
    ("text-secondary", "ground", AA_NORMAL, "ground", "Body copy on the page ground"),
    ("text-tertiary", "ground", AA_NORMAL, "ground", "Index labels and captions on the page ground"),
    ("text-primary", "surface", AA_NORMAL, "ground", "Flight codes and figures on a glass panel"),
    ("text-secondary", "surface", AA_NORMAL, "ground", "Body copy, metadata and index labels on a glass panel"),
    ("text-warning", "surface", AA_NORMAL, "ground", "Low-seat warning on a flight card"),
    ("text-on-accent", "fill-accent", AA_NORMAL, "ground", "Label on the primary action — deep sky in light, sky in dark"),
    ("text-link", "ground", AA_NORMAL, "ground", "Links — Create one, Log in"),
    ("text-success", "tint-success", AA_NORMAL, "ground", "Confirmed booking badge"),
    ("text-danger", "tint-danger", AA_NORMAL, "ground", "Cancelled badge and error banners"),
    ("text-info", "tint-info", AA_NORMAL, "ground", "Demonstration notice in the booking dialog"),
    # SC 1.4.11 applies to the boundary of a control, not to decorative
    # dividers — this is the selected-fare-card border and the focus ring,
    # deliberately not --border-subtle, which carries panel edges.
    ("border-accent", "surface", AA_LARGE, "ground", "Selected fare card border"),
    ("focus-ring", "ground", AA_LARGE, "ground", "Focus ring against the page ground"),
    ("focus-ring", "surface", AA_LARGE, "ground", "Focus ring against a glass panel"),
    # ---- over photography ----------------------------------------------
    # New surface area for Airy Sky: the destination cards, the hero and the
    # auth split panels all set text over an image. The rule is that no text
    # ever sits on bare photography, so what is actually measured is the
    # scrim — composited over a blown-out highlight, the worst a photograph
    # can do to it. If these hold, the design rule holds for any image.
    ("text-on-photo", "scrim-card", AA_NORMAL, "photo-highlight", "Destination name and IATA code on a card image"),
    ("text-on-photo", "scrim-hero", AA_NORMAL, "photo-highlight", "Hero headline over the carousel image"),
    ("text-on-photo", "scrim-panel", AA_NORMAL, "photo-highlight", "Editorial copy on the auth split panel"),
]


def main() -> int:
    missing = [p for p in CSS_SOURCES if not p.exists()]
    if missing:
        print(f"error: palette source not found: {missing[0]}", file=sys.stderr)
        return 2

    css = "\n".join(p.read_text(encoding="utf-8") for p in CSS_SOURCES)
    themes = dict(zip(("dark", "light"), parse_themes(css)))

    failures = 0
    print(f"Airy Sky palette contrast — {len(REQUIRED)} pairs x 2 themes, WCAG 2.2 AA")

    for theme_name, palette in themes.items():
        print(f"\n  {theme_name} theme")
        for fg, bg, minimum, backdrop, description in REQUIRED:
            ratio = contrast(fg, bg, palette, over=backdrop)
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
