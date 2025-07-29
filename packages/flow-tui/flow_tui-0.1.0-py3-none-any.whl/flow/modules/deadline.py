from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich.style import Style
from pathlib import Path
import json

DATA_DIR = Path.home() / ".flow_data"
DATA_DIR.mkdir(exist_ok=True)

DEADLINE_FILE = DATA_DIR / "deadline.json"

def save_deadlines(deadlines):
    with open(DEADLINE_FILE, "w", encoding="utf-8") as f:
        json.dump(deadlines, f, ensure_ascii=False, indent=2)


def load_deadlines():
    if not DEADLINE_FILE.exists():
        DEADLINE_FILE.write_text("[]")
    if DEADLINE_FILE.exists():
        with open(DEADLINE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def parse_deadline_input(input_text):
    parts = input_text.split(":")
    if len(parts) != 3:
        return None  # Or raise an exception / return default
    name = parts[0].strip()
    time_left = parts[1].strip()
    urgency = parts[2].strip()
    return {"name": name, "time_left": time_left, "urgency": urgency, "progress": 0}

def render_deadline_panel(deadline_data,deadline_cursor_index,deadline_input_mode,deadline_input_text,focused):
    lines = []

    # Example data
    # deadline_data = [
    #     {"name": "Math HW", "time_left": "2h left", "urgency": "!!!", "progress": 100},
    #     {"name": "Report", "time_left": "5h left", "urgency": "!! ", "progress": 70},
    #     {"name": "Presentation", "time_left": "1h left", "urgency": "!!!", "progress": 30},
    # ]

    if deadline_input_mode:
        placeholder = "Deadline name : dd/mm/yyyy : urgency_level"
        lines.append(Text(f"> {placeholder}_", style="dim"))
        lines.append(Text(f"> Fix the toilet : 20/03/2025 : UNIVERSAL URGEN" , style="dim"))
        lines.append(Text(f"> {deadline_input_text}"))
    else:
        if not deadline_data:
            lines.append(Text("(No deadline. Press '+' to add)"))
        else:
            for i,task in enumerate(deadline_data):
                # First line: Deadline info
                if i != deadline_cursor_index and focused == "deadline":
                    style = Style(dim=True, color="white")
                else:
                    style="default"
                line1 = Text(f"{i+1}# {task['name']:<12} [{task['time_left']}]  [{task['urgency']}]", style=style)
                
                # Second line: Progress bar
                bar_length = 25
                filled = int(task["progress"] / 100 * bar_length)
                bar = "▋" * filled + " " * (bar_length - filled)
                line2 = Text(f"Progress: {bar} | {task['progress']}%", style=style)
                
                lines.append(line1)
                lines.append(line2)
                lines.append(Text(""))  # blank line between deadline_data

    # Combine and center
    body = Text("\n").join(lines)
    title = "[bold red]D[/bold red]eadline"
    border_style = "green" if focused == "deadline" else "white"
    subtitle = "↑↓/Navigation, + -/Add,Remove, ←→/Progress" if focused == "deadline" else ""
    # Return panel
    return Panel(body, title=title,subtitle=subtitle, subtitle_align="left",title_align="left", border_style=border_style)


