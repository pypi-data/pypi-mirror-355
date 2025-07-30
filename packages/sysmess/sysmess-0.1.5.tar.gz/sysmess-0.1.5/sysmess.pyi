"""
Fancy terminal message box renderer using Unicode box characters and ANSI styling.
"""

from typing import Optional

__all__ = ["measure_box_width", "fancy_box"]

def measure_box_width(
    message: str,
    title: Optional[str] = None,
) -> int:
    """
    measure_box_width(message, title=None) -> int
    Return the total width of the box including borders.
    """
    ...

def fancy_box(
    message: str,
    title: Optional[str] = None,
    center: bool = False,
    bold: bool = False,
    italic: bool = False,
    style: Optional[str] = None,
    border_color: Optional[str] = None,
    title_color: Optional[str] = None,
    body_color: Optional[str] = None,
    blink_border: bool = False,
    blink_title: bool = False,
    blink_body: bool = False,
    wrap: bool = False,
    max_width: Optional[int] = None,
) -> str:
    """
    fancy_box(message, title=None, center=False, bold=False, italic=False,
              style=None, border_color=None, title_color=None, body_color=None,
              blink_border=False, blink_title=False, blink_body=False,
              wrap=False, max_width=None) -> str
    Return a string with the message enclosed in a fancy box.
    Optionally specify style='round' for rounded corners.
    Set blink_border/title/body to True to blink the border, title, or body text.
    Set wrap=True to word-wrap text to terminal width or use max_width for a fixed width.
    Colors can be specified for the border, title and body using basic color names:
    black, red, green, yellow, blue, magenta, cyan, white, bright_black, bright_red,
    bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white.
    """
    ...