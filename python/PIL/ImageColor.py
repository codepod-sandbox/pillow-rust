"""
PIL.ImageColor — color name/string to RGB conversion.
"""


colormap = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgreen": "#90ee90",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}


def getrgb(color):
    """Convert a color string to an (R, G, B) or (R, G, B, A) tuple.

    Accepts:
    - Named colors: "red", "blue", etc.
    - Hex: "#RGB", "#RRGGBB", "#RRGGBBAA"
    - rgb()/rgba(): "rgb(255, 0, 0)", "rgba(255, 0, 0, 128)"
    - hsl(): "hsl(0, 100%, 50%)"
    - hsv()/hsb(): "hsv(0, 100%, 100%)"
    """
    if not isinstance(color, str):
        raise ValueError("color must be a string")

    original = color

    # Named color — must be exact match (no extra spaces)
    lower = color.lower()
    if lower in colormap:
        return getrgb(colormap[lower])

    # Reject if it doesn't look like a valid format
    if color != color.strip():
        raise ValueError("unknown color specifier: %r" % original)

    # Hex
    if color.startswith("#"):
        h = color[1:]
        if len(h) in (3, 4, 6, 8):
            try:
                if len(h) == 3:
                    return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16))
                if len(h) == 4:
                    return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16), int(h[3] * 2, 16))
                if len(h) == 6:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
                if len(h) == 8:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
            except ValueError:
                pass
        raise ValueError("unknown color specifier: %r" % original)

    # Lowercase for function matching
    clower = color.lower()

    # rgb(r, g, b) / RGB(r, g, b) — with percent support
    if clower.startswith("rgb(") or clower.startswith("rgba("):
        return _parse_rgb(color, original)

    # hsl(h, s%, l%) / HSL(h, s%, l%)
    if clower.startswith("hsl("):
        return _parse_hsl(color, original)

    # hsv(h, s%, v%) / HSV(h, s%, v%) / hsb(h, s%, b%)
    if clower.startswith("hsv(") or clower.startswith("hsb("):
        return _parse_hsv(color, original)

    raise ValueError("unknown color specifier: %r" % original)


def _parse_inner(color):
    """Extract the inner part of a function call like 'rgb(1, 2, 3)'."""
    idx = color.index("(")
    inner = color[idx + 1:]
    if not inner.endswith(")"):
        raise ValueError("missing closing paren")
    return inner[:-1]


def _parse_rgb(color, original):
    """Parse rgb(...) or rgba(...) color strings."""
    try:
        inner = _parse_inner(color)
    except ValueError:
        raise ValueError("unknown color specifier: %r" % original)

    parts = [p.strip() for p in inner.split(",")]

    is_rgba = color.lower().startswith("rgba(")

    if is_rgba:
        if len(parts) != 4:
            raise ValueError("unknown color specifier: %r" % original)
    else:
        if len(parts) != 3:
            raise ValueError("unknown color specifier: %r" % original)

    # Check if percent format
    if parts[0].endswith("%"):
        # All non-alpha parts must be percent
        for i in range(3):
            if i >= len(parts):
                break
            if not parts[i].endswith("%"):
                raise ValueError("unknown color specifier: %r" % original)
        values = []
        for i in range(3):
            p = parts[i].rstrip("%")
            values.append(int(float(p) * 255 / 100 + 0.5))
        if is_rgba:
            if parts[3].endswith("%"):
                raise ValueError("unknown color specifier: %r" % original)
            values.append(int(parts[3]))
        return tuple(values)
    else:
        # Integer format
        try:
            values = [int(p) for p in parts]
        except ValueError:
            raise ValueError("unknown color specifier: %r" % original)
        return tuple(values)


def _parse_hsl(color, original):
    """Parse hsl(h, s%, l%) color strings."""
    try:
        inner = _parse_inner(color)
    except ValueError:
        raise ValueError("unknown color specifier: %r" % original)

    parts = [p.strip() for p in inner.split(",")]
    if len(parts) != 3:
        raise ValueError("unknown color specifier: %r" % original)

    # h must NOT end with %, s and l MUST end with %
    if parts[0].endswith("%"):
        raise ValueError("unknown color specifier: %r" % original)
    if not parts[1].endswith("%") or not parts[2].endswith("%"):
        raise ValueError("unknown color specifier: %r" % original)

    # Validate no spaces within percent values
    for p in parts[1:]:
        stripped = p.rstrip("%")
        if stripped != stripped.strip():
            raise ValueError("unknown color specifier: %r" % original)

    try:
        h_val = float(parts[0]) / 360.0
        s_val = float(parts[1].rstrip("%")) / 100.0
        l_val = float(parts[2].rstrip("%")) / 100.0
    except (ValueError, OverflowError):
        raise ValueError("unknown color specifier: %r" % original)

    # Reject absurdly long numbers
    for p in parts:
        clean = p.rstrip("%")
        if len(clean) > 20:
            raise ValueError("unknown color specifier: %r" % original)

    return _hsl_to_rgb(h_val, s_val, l_val)


def _parse_hsv(color, original):
    """Parse hsv(h, s%, v%) or hsb(h, s%, b%) color strings."""
    try:
        inner = _parse_inner(color)
    except ValueError:
        raise ValueError("unknown color specifier: %r" % original)

    parts = [p.strip() for p in inner.split(",")]
    if len(parts) != 3:
        raise ValueError("unknown color specifier: %r" % original)

    if parts[0].endswith("%"):
        raise ValueError("unknown color specifier: %r" % original)
    if not parts[1].endswith("%") or not parts[2].endswith("%"):
        raise ValueError("unknown color specifier: %r" % original)

    for p in parts[1:]:
        stripped = p.rstrip("%")
        if stripped != stripped.strip():
            raise ValueError("unknown color specifier: %r" % original)

    try:
        h_val = float(parts[0]) / 360.0
        s_val = float(parts[1].rstrip("%")) / 100.0
        v_val = float(parts[2].rstrip("%")) / 100.0
    except (ValueError, OverflowError):
        raise ValueError("unknown color specifier: %r" % original)

    for p in parts:
        clean = p.rstrip("%")
        if len(clean) > 20:
            raise ValueError("unknown color specifier: %r" % original)

    return _hsv_to_rgb(h_val, s_val, v_val)


def _hsl_to_rgb(h, s, l):
    """Convert HSL (0-1 range) to (R, G, B) tuple (0-255)."""
    if s == 0:
        v = int(l * 255 + 0.5)
        return (v, v, v)

    if l < 0.5:
        q = l * (1 + s)
    else:
        q = l + s - l * s
    p = 2 * l - q

    def hue2rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    r = int(hue2rgb(p, q, h + 1 / 3) * 255 + 0.5)
    g = int(hue2rgb(p, q, h) * 255 + 0.5)
    b = int(hue2rgb(p, q, h - 1 / 3) * 255 + 0.5)
    return (r, g, b)


def _hsv_to_rgb(h, s, v):
    """Convert HSV (0-1 range) to (R, G, B) tuple (0-255)."""
    if s == 0:
        val = int(v * 255 + 0.5)
        return (val, val, val)

    i = int(h * 6.0)
    f = (h * 6.0) - i
    p_val = v * (1.0 - s)
    q_val = v * (1.0 - s * f)
    t_val = v * (1.0 - s * (1.0 - f))

    i = i % 6
    if i == 0:
        r, g, b = v, t_val, p_val
    elif i == 1:
        r, g, b = q_val, v, p_val
    elif i == 2:
        r, g, b = p_val, v, t_val
    elif i == 3:
        r, g, b = p_val, q_val, v
    elif i == 4:
        r, g, b = t_val, p_val, v
    else:
        r, g, b = v, p_val, q_val

    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def getcolor(color, mode):
    """Convert a color string to a value appropriate for the given *mode*.

    Returns an integer for 'L'/'1', a tuple for 'RGB'/'RGBA'/'LA'/'HSV'.
    """
    rgb = getrgb(color)
    if mode == "L" or mode == "1":
        # ITU-R 601-2 luma
        r, g, b = rgb[0], rgb[1], rgb[2]
        return int(0.299 * r + 0.587 * g + 0.114 * b + 0.5)
    if mode == "LA":
        r, g, b = rgb[0], rgb[1], rgb[2]
        l = int(0.299 * r + 0.587 * g + 0.114 * b + 0.5)
        a = rgb[3] if len(rgb) == 4 else 255
        return (l, a)
    if mode == "RGB":
        return rgb[:3]
    if mode == "RGBA":
        if len(rgb) == 4:
            return rgb
        return rgb[:3] + (255,)
    if mode == "HSV":
        r, g, b = rgb[0], rgb[1], rgb[2]
        maxc = max(r, g, b)
        minc = min(r, g, b)
        v = maxc
        if maxc == minc:
            return (0, 0, v)
        s = int((maxc - minc) / maxc * 255 + 0.5)
        diff = maxc - minc
        if maxc == r:
            h = (g - b) / diff
        elif maxc == g:
            h = 2.0 + (b - r) / diff
        else:
            h = 4.0 + (r - g) / diff
        h = int((h / 6.0) * 256 + 0.5) % 256
        return (h, s, v)
    return rgb
