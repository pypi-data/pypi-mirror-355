import random
from enum import Enum
from typing import Self

from pryttier.math import Vector3
from pryttier.tools import chunks, hex2Dec


class RGB:
    def __init__(self, r, g, b):
        self.rgb = (r, g, b)
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def random(cls):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return RGB(r, g, b)

    def get(self):
        return self.rgb

    def __repr__(self):
        return f"({self.r}, {self.g}, {self.b})"

    def __mul__(self, other: int | float | Self):
        if isinstance(other, int) or isinstance(other, float):
            return RGB(int(self.r * other), int(self.g * other), int(self.b * other))
        if isinstance(other, RGB):
            return RGB(int(self.r * other.r), int(self.g * other.g), int(self.b * other.b))

    def __truediv__(self, other: int | float | Self):
        if isinstance(other, int) or isinstance(other, float):
            return RGB(self.r / other, self.g / other, self.b / other)
        if isinstance(other, RGB):
            return RGB(int(self.r / other.r), int(self.g / other.g), int(self.b / other.b))

    def complement(self):
        return RGB(255 - self.r, 255 - self.g, 255 - self.b)

    def toVector(self):
        return Vector3(self.r, self.g, self.b)

    def toInt(self):
        return RGB(int(self.r), int(self.g), int(self.b))

def colorInterpolate(colorA: RGB, colorB: RGB, t: float):
    ca = colorA.toVector()
    cb = colorB.toVector()

    v = Vector3.interpolate(ca, cb, t).toInt()
    return RGB(v.x, v.y, v.z)

def rgbColorGradient(colorA: RGB, colorB: RGB, num: int):
    colors = []
    ca = colorA
    cb = colorB

    for i in range(num+1):
        t = i/num
        c = Vector3.interpolate(ca.toVector(), cb.toVector(), t).toInt()
        colors.append(RGB(*c))

    return colors

def rgb2hsl(rgb: RGB | tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = (rgb/255).rgb if type(rgb) == RGB else (rgb[0]/255, rgb[1]/255, rgb[2]/255)

    mx = max(r, g, b)
    mn = min(r, g, b)

    H: float
    S: float
    L = (mx + mn) / 2

    if mx == mn:
        H = 0
        S = 0
    else:
        c = mx - mn
        S = c / (1 - abs(2 * L - 1))

        if mx == r:
            H = ((g - b) / c) % 6
        elif mx == g:
            H = ((b - r) / c) + 2
        elif mx == b:
            H = ((r - g) / c) + 4

    H = round(H * 60)
    S = round(S * 100)
    L = round(L * 100)
    return H, S, L


def hsl2rgb(hsl: tuple[int, int, int]) -> tuple[int, int, int]:
    h, s, l = hsl
    s /= 100
    l /= 100
    c = (1 - abs((2 * l) - 1)) * s
    x = c * (1 - abs(((h / 60) % 2) - 1))
    m = l - c/2
    rgb = (0, 0, 0)
    if 0 <= h < 60:
        rgb = (c, x, 0)
    elif 60 <= h < 120:
        rgb = (x, c, 0)
    elif 120 <= h < 180:
        rgb = (0, c, x)
    elif 180 <= h < 240:
        rgb = (0, x, c)
    elif 240 <= h < 300:
        rgb = (x, 0, c)
    elif 300 <= h < 360:
        rgb = (c, 0, x)

    return round((rgb[0] + m) * 255), round((rgb[1] + m) * 255), round((rgb[2] + m) * 255)


def rgb2cmyk(rgb: tuple[int, int, int] | RGB) -> tuple[int, int, int, int]:
    r, g, b = rgb.rgb if type(rgb) == RGB else rgb
    r, g, b = r/255, g/255, b/255
    k = min(1-r, 1-g, 1-b)
    c = (1-r-k)/(1-k)
    m = (1-g-k)/(1-k)
    y = (1-b-k)/(1-k)
    return int(c*100), int(m*100), int(y*100), int(k*100)

def cmyk2rgb(cmyk: tuple[int, int, int, int]) -> RGB:
    c, m, y, k = cmyk
    c, m, y, k = c/100, m/100, y/100, k/100
    r = 255 * (1-c) * (1-k)
    g = 255 * (1-m) * (1-k)
    b = 255 * (1-y) * (1-k)
    return RGB(int(r), int(g), int(b))

def hex2RGB(col: str):
    col = col.replace("#", "")
    hexes = ["".join([a[0], a[1]]) for a in chunks(list(col), 2)]
    if len(hexes) != 3:
        raise ValueError("Invalid Color. Format:- #RRGGBB")
    res = [hex2Dec(a) for a in hexes]
    return RGB(*res)

def rgb2Hex(col: RGB | tuple[int, int, int]):
    r, g, b = col.rgb if type(col) == RGB else col
    r, g, b = hex(r).replace("0x", ""), hex(g).replace("0x", ""), hex(b).replace("0x", "")
    r = ("0" * (2-len(r)))+r
    g = ("0" * (2-len(g)))+g
    b = ("0" * (2-len(b)))+b
    return f"#{r}{g:2}{b:2}"

class AnsiColor:
    def __init__(self, colorCode: int):
        self.code = f"\033[{colorCode}m"

    @property
    def value(self):
        return self.code


class AnsiRGB:
    def __init__(self, rgb: RGB | tuple[int, int, int]):
        if isinstance(rgb, RGB):
            self.code = f"\u001b[38;2;{rgb.r};{rgb.g};{rgb.b}m"
        elif isinstance(rgb, tuple):
            self.code = f"\u001b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

    @property
    def value(self):
        return self.code


class AnsiRGB_BG:
    def __init__(self, rgb: RGB | tuple[int, int, int]):
        if isinstance(rgb, RGB):
            self.code = f"\u001b[48;2;{rgb.r};{rgb.g};{rgb.b}m"
        elif isinstance(rgb, tuple):
            self.code = f"\u001b[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

    @property
    def value(self):
        return self.code


class AnsiColors(Enum):
    BLACK = AnsiColor(30)
    RED = AnsiColor(31)
    GREEN = AnsiColor(32)
    YELLOW = AnsiColor(33)  # orange on some systems
    BLUE = AnsiColor(34)
    MAGENTA = AnsiColor(35)
    CYAN = AnsiColor(36)
    LIGHT_GRAY = AnsiColor(37)
    DARK_GRAY = AnsiColor(90)
    BRIGHT_RED = AnsiColor(91)
    BRIGHT_GREEN = AnsiColor(92)
    BRIGHT_YELLOW = AnsiColor(93)
    BRIGHT_BLUE = AnsiColor(94)
    BRIGHT_MAGENTA = AnsiColor(95)
    BRIGHT_CYAN = AnsiColor(96)
    WHITE = AnsiColor(97)

    RESET = '\033[0m'  # called to return to standard terminal text color


def coloredText(text: str, color: AnsiColors | AnsiColor | AnsiRGB | AnsiRGB_BG, reset: bool = True) -> str:
    if reset:
        text = color.value + text + AnsiColors.RESET.value
    elif not reset:
        text = color.value + text

    return text
