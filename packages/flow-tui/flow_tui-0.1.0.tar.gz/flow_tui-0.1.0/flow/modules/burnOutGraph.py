from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import json
from pathlib import Path
from datetime import datetime

console = Console()

DATA_DIR = DATA_DIR = Path.home() / ".flow_data"
DATA_DIR.mkdir(exist_ok=True)

def get_workload_file():
    now = datetime.now()
    filename = f"workload_{now.year}_{now.month:02}.json"
    return DATA_DIR / filename

def load_workload():
    workload_file = get_workload_file()
    if not workload_file.exists():
        workload_file.write_text("{}", encoding="utf-8")
    with open(workload_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_workload(work_data):
    workload_file = get_workload_file()
    with open(workload_file, "w", encoding="utf-8") as f:
        json.dump(work_data, f, ensure_ascii=False, indent=2)

def render_bar_graph(work_data):
    max_minutes = max([10] + list(work_data.values()))
    terminal_width = console.size.width
    max_bar_length = max((terminal_width // 2) - 15, 10)

    lines = []
    for day in range(1, 32):
        day_str = f"{day:02}"
        minutes = work_data.get(day_str, 0)
        bar_length = max(1, round((minutes / max_minutes) * max_bar_length))
        bar = "─" * (bar_length - 1) + "◉" if bar_length > 1 else "◉"
        lines.append(f"{day_str} | {bar} {minutes}")

    lines.reverse()
    graph = Text()
    for line in lines:
        graph.append(line + "\n")

    centered_graph = Align.left(graph, vertical="middle")
    return Panel(centered_graph, title="Workload Bar Graph", border_style="cyan")
