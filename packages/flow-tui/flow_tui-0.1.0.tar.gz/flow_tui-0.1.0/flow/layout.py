from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from time import sleep

def make_layout() -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="timer", ratio=1),
        Layout(name="body", ratio=4),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    layout["left"].split(
        Layout(name="todo",ratio=1),
        Layout(name="deadline",ratio=1),
    )
    layout["right"].split(
        Layout(name="workload"),
    )
    return layout

# def render_placeholder(name: str) -> Panel:
#     return Panel(
#     f"[bold]{name}[/bold]",
#     title=f"{name}",
#     border_style="#5f87ff",
#     highlight=True
#     )



# if __name__ == "__main__":
#     layout = make_layout()

#     with Live(layout, refresh_per_second=4, screen=True):
#         while True:
#             # Update placeholders (eventually you replace these with dynamic content)
#             layout["timer"].update(render_placeholder("timer"))
#             layout["schedule"].update(render_placeholder("schedule"))
#             layout["todo"].update(render_placeholder("todo"))
#             layout["heatmap"].update(render_placeholder("heatmap"))

#             sleep(0.2)
