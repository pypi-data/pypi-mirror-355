# fa2svg/converter.py

import re
from functools import lru_cache
import base64
import requests
import difflib
from functools import lru_cache
from bs4 import BeautifulSoup
import cairosvg

from .constants import VALID_FA_ICONS

# Font Awesome version and CDN base (jsDelivr)
FA_VERSION = "6.7.2"
FA_CDN_BASE = (
    f"https://cdn.jsdelivr.net/npm/"
    f"@fortawesome/fontawesome-free@{FA_VERSION}/svgs"
)

# Map common legacy FA names to their modern equivalent
LEGACY_ICON_MAP = {
    "map-marker-alt": "map-marker",
    "long-arrow-alt-right": "long-arrow-right",
    "long-arrow-alt-left": "long-arrow-left",
    "long-arrow-alt-up": "long-arrow-up",
    "long-arrow-alt-down": "long-arrow-down",
    "external-link-alt": "external-link",
    "sign-in-alt": "sign-in",
    "sign-out-alt": "sign-out",
    "edit": "pencil-alt",
    "redo-alt": "redo",
    "sync-alt": "sync",
    "undo-alt": "undo",
    "trash-alt": "trash-can",
    "exclamation-triangle": "triangle-exclamation"
}

# Map prefix to sub-folder in CDN (support both old and new FA class names)
STYLE_MAP = {
    "fas": "solid", "fa-solid": "solid",
    "far": "regular", "fa-regular": "regular",
    "fab": "brands", "fa-brands": "brands"
}

# Regex for inline CSS props (e.g. font-size, color)
STYLE_PROP = re.compile(r"\s*([\w-]+)\s*:\s*([^;]+)\s*;?")

# Render at 10× pixel density for crispness
IMAGE_SCALE = 10

FA_MARKER = "__FA__"


@lru_cache(maxsize=256)
def _fetch_raw_svg(style_dir: str, icon_name: str) -> str:
    """
    Download (and cache) the raw SVG text for a given style/icon.
    Raises on 404 or other HTTP errors, which will be caught by caller.
    """
    url = f"{FA_CDN_BASE}/{style_dir}/{icon_name}.svg"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


@lru_cache(maxsize=256)
def _render_png_data_uri(style_dir: str, icon_name: str, size: int, color: str) -> str:
    """
    Take raw SVG, inject fill + aspect, render to PNG at high DPI,
    and return a base64 data URI. Cached by (style,icon,size,color).
    """
    raw_svg = _fetch_raw_svg(style_dir, icon_name)

    # strip any width/height attributes
    svg_txt = re.sub(
        r'\s(width|height)="[^"]*"',
        "",
        raw_svg,
        flags=re.IGNORECASE
    )

    # inject fill color + preserveAspectRatio
    svg_txt = re.sub(
        r"<svg\b",
        f'<svg fill="{color}" preserveAspectRatio="xMidYMid meet"',
        svg_txt,
        count=1
    )

    # extract viewBox to compute target width
    match = re.search(r'viewBox="([\d.\s]+)"', svg_txt)
    if match:
        nums = [float(n) for n in match.group(1).split()]
        vb_w, vb_h = nums[2], nums[3]
        target_w = int(size * (vb_w / vb_h))
    else:
        target_w = size

    # render PNG at IMAGE_SCALE×
    png_bytes = cairosvg.svg2png(
        bytestring=svg_txt.encode("utf-8"),
        output_width=target_w * IMAGE_SCALE,
        output_height=size * IMAGE_SCALE
    )
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def parse_css_size(size_str: str, parent_px: float = 16.0) -> float:
    """
    Convert a CSS size string (px, em, %) to absolute px.
    Defaults to parent_px if parsing fails.
    """
    s = size_str.strip()
    try:
        if s.endswith("px"):
            return float(s[:-2])
        if s.endswith("em"):
            return float(s[:-2]) * parent_px
        if s.endswith("%"):
            return float(s[:-1]) / 100.0 * parent_px
        return float(s)
    except Exception:
        return parent_px


def get_computed_font_size(el) -> float:
    """
    Walk up the tree to find a 'font-size' style and compute
    its absolute px value (default 16px).
    """
    DEFAULT = 16.0
    current = el
    while current:
        props = dict(STYLE_PROP.findall(current.get("style", "")))
        if "font-size" in props:
            parent = get_computed_font_size(current.parent) if current.parent else DEFAULT
            return parse_css_size(props["font-size"], parent)
        current = current.parent
    return DEFAULT


def get_inherited_color(el) -> str:
    """
    Walk up the tree to find a 'color' style. Defaults to black.
    """
    current = el
    while current:
        props = dict(STYLE_PROP.findall(current.get("style", "")))
        if "color" in props:
            return props["color"].strip()
        current = current.parent
    return "#000"


def to_inline_png_img(html: str) -> str:
    """
    Same behavior as before, but:
     - scans only once for <i>/<span> with fa-*
     - caches data-URIs per unique key in a local dict
     - uses faster find_all+filter instead of select()
     - aliases globals to locals for speed
    """
    soup = BeautifulSoup(html, "lxml")

    # alias for speed
    get_font = get_computed_font_size
    get_col  = get_inherited_color
    render   = _render_png_data_uri
    SM, VI   = STYLE_MAP, VALID_FA_ICONS
    marker   = FA_MARKER

    # local cache so each unique URI is rendered exactly once
    local_cache: dict[tuple, str] = {}

    # grab only the tags we care about
    candidates = [
        el for el in soup.find_all(["i", "span"])
        if any(c.startswith("fa-") for c in el.get("class", []))
    ]

    STYLE_CLASSES = {"fa-solid", "fa-regular", "fa-brands", "fas", "far", "fab"}

    for el in candidates:
        classes = el.get("class", [])
        # extract icon name, skipping style classes
        icon = next((c.split("fa-")[1]
                     for c in classes
                     if c.startswith("fa-") and c != "fa" and c not in STYLE_CLASSES),
                    None)
        if not icon:
            continue

        # check for legacy names
        icon = LEGACY_ICON_MAP.get(icon, icon)

        # find style folder, validate/fuzzy-match
        style_dir = next((SM[c] for c in classes if c in SM), "solid")
        allowed   = VI.get(style_dir, ())
        if icon not in allowed:
            m = difflib.get_close_matches(icon, allowed, n=1, cutoff=0.6)
            if not m:
                continue
            icon = m[0]

        # compute size/color
        size_px = int(get_font(el))
        color   = get_col(el)

        key = (style_dir, icon, size_px, color)
        data_uri = local_cache.get(key)
        if data_uri is None:
            try:
                data_uri = render(style_dir, icon, size_px, color)
            except Exception:
                continue
            local_cache[key] = data_uri

        # build the <img>
        img = soup.new_tag("img", src=data_uri)
        # stash original info in alt/title exactly as before
        orig_style = el.get("style", "").replace("|", ";")
        parts = [el.name, " ".join(classes)]
        if orig_style:
            parts.append(orig_style)
        payload = "|".join(parts)

        img["alt"]   = marker + payload
        img["title"] = img["alt"]
        img["style"] = f"height:{size_px}px;width:auto;vertical-align:-0.125em;"

        el.replace_with(img)

    return str(soup)


def revert_to_original_fa(html: str,
                          remove_other_inline_img: bool = False) -> str:
    soup = BeautifulSoup(html, "lxml")

    for img in list(soup.find_all("img")):
        alt = img.get("alt", "")
        if alt.startswith(FA_MARKER):
            # strip marker, then split into at most 3 parts
            payload = alt[len(FA_MARKER):]
            tag_name, cls_str, *rest = payload.split("|", 2)
            classes = cls_str.split()
            original_style = rest[0] if rest else None

            new_el = soup.new_tag(tag_name)
            new_el["class"] = classes
            if original_style:
                new_el["style"] = original_style

            img.replace_with(new_el)

        else:
            if remove_other_inline_img:
                img.decompose()
            # else: leave untouched

    return str(soup)


def to_inline_svg(html: str) -> str:
    """Replace Font Awesome <i>/<span> tags with inline SVG preserving CSS-like sizing/color."""
    soup = BeautifulSoup(html, "lxml")

    for el in soup.select(ICON_SELECTOR):
        classes = el.get("class", [])
        # find the 'fa-xyz' part, skipping style classes
        icon = next(
            (c.split("fa-")[1] for c in classes if c.startswith("fa-") and c != "fa" and c not in {"fa-solid", "fa-regular", "fa-brands", "fas", "far", "fab"}),
            None
        )
        if not icon:
            continue

        # pick solid/regular/brands
        style_dir = next((STYLE_MAP[c] for c in classes if c in STYLE_MAP), "solid")

        # parse any inline overrides
        styles = dict(STYLE_PROP.findall(el.get("style", "")))
        size  = styles.get("font-size")  # e.g. "1.5em" or "24px"
        color = styles.get("color")      # e.g. "#c60" or "red"

        # fetch and parse the SVG
        raw_svg = _fetch_raw_svg(style_dir, icon)
        svg     = BeautifulSoup(raw_svg, "lxml").find("svg")

        # extract viewBox dimensions for aspect ratio
        vb = svg.get("viewBox", "").split()
        if len(vb) == 4:
            vb_w, vb_h = float(vb[2]), float(vb[3])
            aspect = vb_w / vb_h
        else:
            aspect = 1.0

        # SIZE: if override, honor it; else use height=1em & proportional width
        if size:
            svg["width"]  = size
            svg["height"] = size
        else:
            svg["height"] = "1em"
            svg["width"]  = f"{aspect:.3f}em"

        # COLOR: override or inherit
        svg["fill"] = color if color else "currentColor"

        # VERTICAL ALIGN: mimic FA's -0.125em baseline shift
        existing_style = svg.get("style", "").rstrip(";")
        svg["style"] = (
            (existing_style + ";" if existing_style else "")
            + "vertical-align:-0.125em"
        )

        # replace the original tag with our enriched SVG
        el.replace_with(svg)

    return str(soup)

