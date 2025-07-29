from typing import Any

from .constants import NEWLINE
from .style import style

DEFAULT_SYNTAX_HIGHLIGHT_COLORS = {
    'key': '#e06c75',
    'arr': '#ffd700',
    'dict': '#ffd700',
    'str': '#98c379',
    'num': '#d19a58',
    'bool': '#d19a66',
}


def highlight(value: Any,
              indent: int = 2,
              curr_indent: int = 0,
              *,
              trailing_comma: bool = False,
              pre_indent: bool = True,
              colors: dict[str, str] | None = None):
    """Converts a value to a string with syntax highlighting.

    Args:
        val (any): Value to highlight. Can be a dict, list, str, int, bool, etc.
        indent (int, optional): Amount of spaces to indent.
        curr_indent (int, optional): Current indent level.
        trailing_comma (bool, optional): Whether to add a trailing comma to the last item in a list or dict.
        pre_indent (bool, optional): Whether to indent the first line of a list or dict.
        colors (dict[str, str], optional): Colors to use for syntax highlighting.
            Uses `DEFAULT_SYNTAX_HIGHLIGHT_COLORS` if None.

    Returns:
        str: Values as a string with syntax highlighting.
    """
    if colors is None:
        colors = DEFAULT_SYNTAX_HIGHLIGHT_COLORS
    if isinstance(value, dict):
        return pretty_dict(value,
                           indent=indent,
                           curr_indent=curr_indent,
                           trailing_comma=trailing_comma,
                           pre_indent=pre_indent,
                           colors=colors)
    if isinstance(value, list):
        return pretty_list(value,
                           indent=indent,
                           curr_indent=curr_indent,
                           trailing_comma=trailing_comma,
                           pre_indent=pre_indent,
                           colors=colors)
    if isinstance(value, str):
        return style(repr(value), fg=colors['str'])
    if isinstance(value, int) or isinstance(value, float):
        return style(repr(value), fg=colors['num'])
    if isinstance(value, bool):
        return style(repr(value), fg=colors['bool'])
    return repr(value)


def pretty_dict(dictionary: dict,
                indent: int = 2,
                curr_indent: int = 0,
                *,
                trailing_comma: bool = False,
                pre_indent: bool = True,
                colors: dict[str, str] | None = None):
    """Converts a dict to a string with syntax highlighting.

    Args:
        dictionary (dict): Dictionary to syntax highlight.
        indent (int, optional): Amount of spaces to indent.
        curr_indent (int, optional): Current indent level.
        trailing_comma (bool, optional): Whether to add a trailing comma to the last item in a list or dict.
        pre_indent (bool, optional): Whether to indent the first line of a list or dict.
        colors (dict[str, str], optional): Colors to use for syntax highlighting.
            Uses `DEFAULT_SYNTAX_HIGHLIGHT_COLORS` if None.

    Returns:
       str: Dictionary as a string with syntax highlighting.
    """
    if colors is None:
        colors = DEFAULT_SYNTAX_HIGHLIGHT_COLORS

    lcub = style('{', fg=colors['dict'])
    rcub = style('}', fg=colors['dict'])

    pre_identation = " " * curr_indent if pre_indent else ''
    output_str = f'{pre_identation}{lcub}{NEWLINE}'

    for i, (key, val) in enumerate(dictionary.items()):
        pretty_key = style(repr(key), fg=colors['key'])
        pretty_value = highlight(val,
                                 indent=indent,
                                 curr_indent=indent + curr_indent,
                                 pre_indent=False,
                                 colors=colors)

        comma = ',' if (i < len(dictionary) - 1) else ''
        output_str += f'{" "*(curr_indent + indent)}{pretty_key}: {pretty_value}{comma}{NEWLINE}'

    output_str += f'{" "* curr_indent}{rcub}{ "," + NEWLINE if trailing_comma else ""}'
    return output_str


def pretty_list(lst: list,
                indent: int = 2,
                curr_indent: int = 0,
                *,
                trailing_comma: bool = False,
                pre_indent: bool = True,
                colors: dict[str, str] | None = None):
    """Converts a list to a string with syntax highlighting.

    Args:
        lst (list): List to syntax highlight.
        indent (int, optional): Amount of spaces to indent.
        curr_indent (int, optional): Current indent level.
        trailing_comma (bool, optional): Whether to add a trailing comma to the last item in a list or dict.
        pre_indent (bool, optional): Whether to indent the first line of a list or dict.
        colors (dict[str, str] | None, optional): Colors to use for syntax highlighting.
            Uses `DEFAULT_SYNTAX_HIGHLIGHT_COLORS` if None.

    Returns:
        str: List as a string with syntax highlighting.
    """
    if colors is None:
        colors = DEFAULT_SYNTAX_HIGHLIGHT_COLORS

    lsqb = style('[', fg=colors['arr'])
    rsqb = style(']', fg=colors['arr'])

    pre_identation = " " * curr_indent if pre_indent else ''
    output_str = f'{pre_identation}{lsqb}{NEWLINE}'

    for i, val in enumerate(lst):
        pretty_value = highlight(val,
                                 indent=indent,
                                 curr_indent=indent + curr_indent,
                                 pre_indent=False,
                                 colors=colors)
        comma = ',' if (i < len(lst) - 1) else ''
        output_str += f'{" "*(curr_indent + indent)}{pretty_value}{comma}{NEWLINE}'

    output_str += f'{" "* curr_indent}{rsqb}{"," + NEWLINE if trailing_comma else ""}'
    return output_str
