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
    """
    if not isinstance(color, str):
        raise ValueError("color must be a string")

    original = color
    color = color.strip()

    # Named color
    lower = color.lower()
    if lower in colormap:
        return getrgb(colormap[lower])

    # Hex
    if color.startswith("#"):
        h = color[1:]
        if len(h) == 3:
            r = int(h[0] * 2, 16)
            g = int(h[1] * 2, 16)
            b = int(h[2] * 2, 16)
            return (r, g, b)
        if len(h) == 4:
            r = int(h[0] * 2, 16)
            g = int(h[1] * 2, 16)
            b = int(h[2] * 2, 16)
            a = int(h[3] * 2, 16)
            return (r, g, b, a)
        if len(h) == 6:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            return (r, g, b)
        if len(h) == 8:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            a = int(h[6:8], 16)
            return (r, g, b, a)

    # rgb(r, g, b) / rgba(r, g, b, a)
    if color.startswith("rgb"):
        inner = color.split("(", 1)
        if len(inner) == 2:
            inner = inner[1].rstrip(")")
            parts = [p.strip() for p in inner.split(",")]
            if len(parts) == 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            if len(parts) == 4:
                return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))

    # hsl(h, s%, l%)
    if color.startswith("hsl"):
        inner = color.split("(", 1)
        if len(inner) == 2:
            inner = inner[1].rstrip(")")
            parts = [p.strip().rstrip("%") for p in inner.split(",")]
            if len(parts) == 3:
                h = float(parts[0]) / 360.0
                s = float(parts[1]) / 100.0
                l = float(parts[2]) / 100.0
                return _hsl_to_rgb(h, s, l)

    raise ValueError("unknown color specifier: %r" % original)


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


def getcolor(color, mode):
    """Convert a color string to a value appropriate for the given *mode*.

    Returns an integer for 'L', a tuple for 'RGB'/'RGBA'.
    """
    rgb = getrgb(color)
    if mode == "L":
        # ITU-R 601-2 luma
        r, g, b = rgb[0], rgb[1], rgb[2]
        return int(0.299 * r + 0.587 * g + 0.114 * b + 0.5)
    if mode == "RGB":
        return rgb[:3]
    if mode == "RGBA":
        if len(rgb) == 4:
            return rgb
        return rgb[:3] + (255,)
    return rgb
