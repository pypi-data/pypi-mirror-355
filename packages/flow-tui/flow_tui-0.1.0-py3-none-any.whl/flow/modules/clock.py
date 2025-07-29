from datetime import datetime
from zoneinfo import ZoneInfo
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from ..Class.stopWatch import Stopwatch
import time


TIMEZONE = "Asia/Ho_Chi_Minh"

DIGIT_ART = {
    "0": [
        " █████╗ ",
        "██╔══██╗",
        "██║  ██║",
        "██║  ██║",
        "╚█████╔╝",
        " ╚════╝ ",
    ],
    "1": [
        "  ███╗  ",
        " ████║  ",
        "██╔██║  ",
        "╚═╝██║  ",
        "███████╗",
        "╚══════╝",
    ],
    "2": [
        "██████╗ ",
        "╚════██╗",
        "  ███╔═╝",
        "██╔══╝  ",
        "███████╗",
        "╚══════╝",
    ],
    "3": [
        "██████╗ ",
        "╚════██╗",
        " █████╔╝",
        " ╚═══██╗",
        "██████╔╝",
        "╚═════╝ ",
    ],
    "4": [
        "  ██╗██╗",
        " ██╔╝██║",
        "██╔╝ ██║",
        "███████║",
        "╚════██║",
        "     ╚═╝",
    ],
    "5": [
        "███████╗",
        "██╔════╝",
        "███████╗",
        "╚═══ ██║",
        "███████║",
        "╚══════╝",
    ],
    "6": [
        " █████╗ ",
        "██╔═══╝ ",
        "██████╗ ",
        "██╔══██╗",
        "╚█████╔╝",
        " ╚════╝ ",
    ],
    "7": [
        "███████╗",
        "╚════██║",
        "    ██╔╝",
        "   ██╔╝ ",
        "  ██╔╝  ",
        "  ╚═╝   ",
    ],
    "8": [
        " █████╗ ",
        "██╔══██╗",
        "╚█████╔╝",
        "██╔══██╗",
        "╚█████╔╝",
        " ╚════╝ ",
    ],
    "9": [
        " █████╗ ",
        "██╔══██╗",
        "╚██████║",
        " ╚═══██║",
        " █████╔╝",
        " ╚════╝ ",
    ],
    ":": [
        "██╗",
        "╚═╝",
        "   ",
        "   ",
        "██╗",
        "╚═╝",
    ]
}

def generate_ascii_time(time_string: str) -> str:
    """Generate ASCII art text for a time string."""
    lines = [""] * 6  # Assuming 6 rows for digit art

    for char in time_string:
        digit_art = DIGIT_ART.get(char, [" " * 9] * 6)  # fallback to empty space
        for i in range(6):
            lines[i] += digit_art[i] + " "  # space between characters

    return "\n".join(lines)

def render_clock(stopwatch: Stopwatch):
    elapsed = stopwatch.get_elapsed()
    time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    ascii_art = generate_ascii_time(time_str)
    style  = "#dd8d7c" if stopwatch.running else "dim white"
    aligned = Align.center(Text(ascii_art, style=style), vertical="middle")

    return Panel(
        aligned,
        title="Stopwatch ───────────── [red]q[/red] to Quit",
        title_align="left",
        border_style="cyan",
        padding=(1, 2)
    )

# Example usage:
# from rich.console import Console
# Console().print(render_clock())
