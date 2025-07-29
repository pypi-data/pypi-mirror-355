from enum import Enum, IntEnum

ESC = '\033['
RESET = f'{ESC}0m'


class Fg(Enum):
    """ANSI escape codes for foreground colors.
    """
    DEFAULT = 39
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    GRAY = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MANGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class Bg(Enum):
    """ANSI escape codes for background colors.
    """
    DEFAULT = 49
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47
    GRAY = 100
    BRIGHT_RED = 101
    BRIGHT_GREEN = 102
    BRIGHT_YELLOW = 103
    BRIGHT_BLUE = 104
    BRIGHT_MANGENTA = 105
    BRIGHT_CYAN = 106
    BRIGHT_WHITE = 107


class Frmt(IntEnum):
    """ANSI escape codes for text formatting.
    """
    DEFAULT = 0
    BOLD = 1
    FAINT = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK_SLOW = 5
    BLINK_FAST = 6
    INVERT = 7
    HIDE = 8
    STRIKETHROUGH = 9
    DOUBLE_UNDERLINE = 21
    OVERLINE = 53


def fg_rgb(rgb_color: tuple[int, int, int]) -> str:
    """Converts an RGB tuple to an ANSI escape code for foreground color.

    Args:
        rgb_color (tuple[int, int, int]): Tuple of RGB values as integers.

    Returns:
        str: ANSI escape code for foreground color.
    """
    return f'38;2;{rgb_color[0]};{rgb_color[1]};{rgb_color[2]}'


def fg_hex(hex_color: str) -> str:
    """Converts a hex color string to an ANSI escape code for foreground color.

    Args:
        hex_color (str): Hex color string.

    Returns:
        str: ANSI escape code for foreground color.
    """
    return fg_rgb(hex2rgb(hex_color))


def bg_rgb(rgb_color: tuple[int, int, int]) -> str:
    """Converts an RGB tuple to an ANSI escape code for background color.

    Args:
        rgb_color (tuple[int, int, int]): Tuple of RGB values as integers.

    Returns:
        str: ANSI escape code for background color.
    """
    return f'48;2;{rgb_color[0]};{rgb_color[1]};{rgb_color[2]}'


def bg_hex(hex_color: str):
    """Converts a hex color string to an ANSI escape code for background color.

    Args:
        hex_color (str): Hex color string.

    Returns:
        str: ANSI escape code for background color.
    """
    return bg_rgb(hex2rgb(hex_color))


def hex2rgb(hex_color: str) -> tuple[int, int, int]:
    """Converts a hex color string to an RGB tuple of integers.

    Args:
        hex_color (str): Hex color string.

    Returns:
        tuple[int, int, int]: RGB tuple of integers.
    """

    def hex2dec(hex_str: str) -> int:
        """Converts a hex string to an base 10 integer.

        Args:
            hex_str (str): Hex string.

        Returns:
            int: Base 10 integer.
        """
        return int(hex_str, 16)

    if hex_color[0] == '#':
        hex_color = hex_color[1:]

    r = hex2dec(hex_color[0:2])
    g = hex2dec(hex_color[2:4])
    b = hex2dec(hex_color[4:6])

    return (r, g, b)


def print_styles(ansi_type: type[Fg] | type[Bg] | type[Frmt]) -> None:
    """Prints all common ANSI escape codes for a given type.
    """

    for style in ansi_type:
        print(f'{ESC}{style.value}mExample Text\t{RESET}({style.name}) ')


def print_styles_all() -> None:
    """Prints all common ANSI escape codes.
    """
    print_styles(Fg)
    print()
    print_styles(Bg)
    print()
    print_styles(Frmt)
