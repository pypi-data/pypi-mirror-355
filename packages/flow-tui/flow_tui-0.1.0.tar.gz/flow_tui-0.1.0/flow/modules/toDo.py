from rich.panel import Panel
from rich.text import Text
from rich.style import Style
import json
from pathlib import Path
from pathlib import Path

DATA_DIR = Path.home() / ".flow_data"
DATA_DIR.mkdir(exist_ok=True)

TASKS_FILE = DATA_DIR / "task.json"

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def load_tasks():
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]")
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)



def render_todo_panel(tasks, cursor_index, input_mode, input_text, focused):
    lines = []
    if input_mode:
        lines.append(Text(f"> {input_text}_"))
    else:
        if not tasks:
            lines.append(Text("(No tasks. Press '+' to add)"))
        else:
            for i, (task, checked) in enumerate(tasks):
                checkbox = "｢x｣" if checked else "｢ ｣"
                base_text = f"{checkbox} {task}"
                if i != cursor_index and focused == "todo":
                    task_text = Text(base_text, style=Style(dim=True, color="white"))
                else:
                    task_text = Text(base_text)
                lines.append(task_text)

    title = "[bold red]T[/bold red]odo"
    border_style = "green" if focused == "todo" else "white"
    subtitle = "↑↓/Navigation, + -/Add,Remove" if focused == "todo" else ""

    return Panel(
        Text("\n").join(lines),
        title=title,
        title_align="left",
        subtitle=subtitle,
        subtitle_align="right",
        padding=(1, 2),
        border_style=border_style
    )
