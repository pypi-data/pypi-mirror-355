def main():
    import signal
    import sys
    from time import perf_counter
    from rich.live import Live
    from .layout import make_layout
    from .modules.clock import render_clock
    from .Class.nonblocking_input import NonBlockingInput
    from .Class.stopWatch import Stopwatch
    from .modules.toDo import render_todo_panel ,save_tasks, load_tasks
    from .modules.burnOutGraph import render_bar_graph , load_workload , save_workload
    from .modules.deadline import render_deadline_panel, parse_deadline_input , save_deadlines, load_deadlines
    from datetime import datetime

    # init layout stopwatch and data
    layout = make_layout()
    stopwatch = Stopwatch()
    tasks = load_tasks()
    work_data = load_workload()

    #init for todo list
    todo_cursor_index = 0
    todo_input_mode = False
    todo_input_text = ""

    #init for deadline
    deadline_data = load_deadlines()
    deadline_cursor_index = 0
    deadline_input_mode = False
    deadline_input_text = ""



    # app state
    focused = ""
    dirty = True
    last_update = 0
    last_saved_elapsed = 0
    resize_flag = False

    def on_resize(signum, frame):
        global resize_flag
        resize_flag = True
    signal.signal(signal.SIGWINCH, on_resize)


    with NonBlockingInput() as nbi:
        with Live(layout, refresh_per_second=60, screen=True) as live:
            while True:
                now = perf_counter()
                key = nbi.get_key(timeout=0.1)
                if resize_flag:
                    dirty = True
                    resize_flag = False
                if key is None:
                    pass

                elif todo_input_mode:
                    if key == "\n":
                        if todo_input_text.strip():
                            tasks.append([todo_input_text.strip(), False])
                            todo_cursor_index = len(tasks) - 1
                            save_tasks(tasks)
                        todo_input_text = ""
                        todo_input_mode = False
                    elif key == "\x1b":
                        todo_input_text = ""
                        todo_input_mode = False
                    elif key == "\x7f":
                        todo_input_text = todo_input_text[:-1]
                    elif key.isprintable():
                        todo_input_text += key
                    dirty = True
                
                elif deadline_input_mode:
                    if key == "\n":
                        if deadline_input_text.strip():
                            parsed_deadline_data = parse_deadline_input(deadline_input_text)
                            if(parsed_deadline_data is not None):
                                deadline_data.append(parsed_deadline_data)
                                deadline_cursor_index = len(deadline_data) - 1
                                save_deadlines(deadline_data)
                        deadline_input_text = ""
                        deadline_input_mode = False
                    elif key == "\x1b":
                        deadline_input_text = ""
                        deadline_input_mode = False
                    elif key == "\x7f":
                        deadline_input_text = deadline_input_text[:-1]
                    elif key.isprintable():
                        deadline_input_text += key
                    dirty = True

                else:
                    if key.lower() == "q":
                        break

                    elif key == " ":
                        stopwatch.stop() if stopwatch.running else stopwatch.start()
                        dirty = True
                    elif key.lower() == "r":
                        stopwatch.reset()
                        last_saved_elapsed = 0
                        dirty = True

                    elif key.lower() == "t":
                        if(focused == "todo"):
                            focused = ""
                        else:
                            focused = "todo"
                        dirty = True

                    elif key.lower() == "d":
                        if focused == "deadline":
                            focused = ""
                        else:
                            focused = "deadline"
                        dirty = True

                    elif focused == "todo":
                        if key == "+":
                            todo_input_mode = True
                            todo_input_text = ""

                        elif key == "\x1b":
                            seq = sys.stdin.read(2)
                            if seq == "[A" and tasks:
                                todo_cursor_index = (todo_cursor_index - 1) % len(tasks)
                            elif seq == "[B" and tasks:
                                todo_cursor_index = (todo_cursor_index + 1) % len(tasks)

                        elif key == "\n" and tasks:
                            tasks[todo_cursor_index][1] = not tasks[todo_cursor_index][1]
                            save_tasks(tasks)

                        elif key == "-" and tasks:
                            tasks.pop(todo_cursor_index)
                            todo_cursor_index = max(0, todo_cursor_index - 1)
                            save_tasks(tasks)

                        dirty = True

                    elif focused == "deadline":
                        if key == "+":
                            deadline_input_mode = True
                            deadline_input_text = ""

                        elif key == "\x1b":
                            seq = sys.stdin.read(2)
                            if seq == "[A" and deadline_data:
                                deadline_cursor_index = (deadline_cursor_index - 1) % len(deadline_data)
                            elif seq == "[B" and deadline_data:
                                deadline_cursor_index = (deadline_cursor_index + 1) % len(deadline_data)
                            elif seq == "[C" and deadline_data and deadline_data[deadline_cursor_index]["progress"] < 100:
                                deadline_data[deadline_cursor_index]["progress"] += 1
                                save_deadlines(deadline_data)
                            elif seq == "[D" and deadline_data and deadline_data[deadline_cursor_index]["progress"] >0:
                                deadline_data[deadline_cursor_index]["progress"] -= 1
                                save_deadlines(deadline_data)

                        elif key == "-" and tasks:
                            deadline_data.pop(deadline_cursor_index)
                            deadline_cursor_index = max(0, deadline_cursor_index - 1)
                            save_deadlines(deadline_data)
                            
                        dirty = True
                if stopwatch.running and (now - last_update) > 0.5:
                    dirty = True
                    last_update = now
                
                if stopwatch.running and (stopwatch.get_elapsed() - last_saved_elapsed) >= 60:
                    today = datetime.now().strftime("%d")
                    work_data[today] = work_data.get(today, 0) + 1  # +1 minute
                    save_workload(work_data)
                    last_saved_elapsed += 60  # move forward by 60, not reset fully
                    dirty = True

                if dirty:
                    layout["timer"].update(render_clock(stopwatch))
                    layout["todo"].update(
                        render_todo_panel(tasks, todo_cursor_index, todo_input_mode, todo_input_text, focused)
                    )
                    layout["workload"].update(render_bar_graph(work_data))
                    layout["deadline"].update(render_deadline_panel(deadline_data,deadline_cursor_index,deadline_input_mode,deadline_input_text,focused))
                    live.update(layout)
                    dirty = False
if __name__ == "__main__":
    main()