from blessed import Terminal
import sys

term = Terminal()

# Cross-platform key reading
if sys.platform == "win32":
    import msvcrt

    def get_key():
        return msvcrt.getwch()
else:
    import tty
    import termios

    def get_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def safe_format(func, *args):
    try:
        return func(*args)
    except Exception:
        return args[0] if args else ""


def spacer():
    return {"type": "spacer"}

def text(content):
    return {"type": "text", "content": content}

def option(label, action):
    return {"type": "option", "label": label, "action": action}

def sidebyside(label1, action1, label2, action2):
    return {
        "type": "sidebyside",
        "options": [
            {"label": label1, "action": action1},
            {"label": label2, "action": action2},
        ]
    }

def checkbox(*args):
    items = []
    for i in range(0, len(args) - 1, 2):
        items.append({"label": args[i], "checked": args[i+1]})
    submit = args[-1] if callable(args[-1]) else None
    return {"type": "checkbox", "items": items, "submit": submit}

def textinput(prompt, callback):
    return {"type": "textinput", "prompt": prompt, "callback": callback}


def starri(title, content):
    if isinstance(content, dict):
        content = list(content.values())
    if isinstance(content, set):
        content = list(content)

    selected_index = 0
    checkbox_states = {}
    input_buffer = ""
    sidebyside_index = 0
    selected_sub = 0

    def get_selectables():
        return [i for i, item in enumerate(content) if item["type"] in ("option", "sidebyside", "checkbox", "textinput")]

    def render():
        print(term.clear + term.move_y(0))
        print(term.bold(title) + "\n")
        for idx, item in enumerate(content):
            selected = idx == selectables[selected_index]
            if item["type"] == "spacer":
                print()
            elif item["type"] == "text":
                print(item["content"])
            elif item["type"] == "option":
                label = item["label"]
                line = ("> " if selected else "  ") + label
                print(safe_format(term.reverse, line) if selected else line)
            elif item["type"] == "sidebyside":
                labels = [o["label"] for o in item["options"]]
                rendered = []
                for i, label in enumerate(labels):
                    if selected and i == sidebyside_index:
                        rendered.append(safe_format(term.reverse, f"[{label}]"))
                    else:
                        rendered.append(f" {label} ")
                print("   ".join(rendered))
            elif item["type"] == "checkbox":
                for i, box in enumerate(item["items"]):
                    state = checkbox_states.get(i, box["checked"])
                    prefix = "[x]" if state else "[ ]"
                    line = f"{prefix} {box['label']}"
                    print(safe_format(term.reverse, line) if selected and selected_sub == i else line)
                print("\n   " + (safe_format(term.reverse, "[ Submit ]") if selected and selected_sub == len(item["items"]) else "[ Submit ]"))
            elif item["type"] == "textinput":
                line = f"{item['prompt']} {input_buffer}" if selected else f"{item['prompt']}"
                print(safe_format(term.reverse, line) if selected else line)
        # print(term.dim("Use arrow keys to navigate, Enter to select, q to quit."))

    selectables = get_selectables()

    while True:
        render()
        key = term.inkey()

        if not key:
            key = get_key()

        current = content[selectables[selected_index]]

        if key.name == "KEY_UP":
            selected_index = (selected_index - 1) % len(selectables)
            sidebyside_index = 0
            selected_sub = 0
        elif key.name == "KEY_DOWN":
            selected_index = (selected_index + 1) % len(selectables)
            sidebyside_index = 0
            selected_sub = 0
        elif key.name == "KEY_LEFT" and current["type"] == "sidebyside":
            sidebyside_index = (sidebyside_index - 1) % 2
        elif key.name == "KEY_RIGHT" and current["type"] == "sidebyside":
            sidebyside_index = (sidebyside_index + 1) % 2
        elif key.name == "KEY_RIGHT" and current["type"] == "checkbox":
            selected_sub = (selected_sub + 1) % (len(current["items"]) + 1)
        elif key.name == "KEY_LEFT" and current["type"] == "checkbox":
            selected_sub = (selected_sub - 1) % (len(current["items"]) + 1)
        elif key == "\n":
            if current["type"] == "option":
                action = current["action"]
                if callable(action):
                    return action()
            elif current["type"] == "sidebyside":
                action = current["options"][sidebyside_index]["action"]
                if callable(action):
                    return action()
            elif current["type"] == "checkbox":
                if selected_sub < len(current["items"]):
                    state = checkbox_states.get(selected_sub, current["items"][selected_sub]["checked"])
                    checkbox_states[selected_sub] = not state
                else:
                    if callable(current["submit"]):
                        selected_values = [checkbox_states.get(i, box["checked"]) for i, box in enumerate(current["items"])]
                        return current["submit"](*selected_values)
            elif current["type"] == "textinput":
                return current["callback"](input_buffer)
        elif key == "q":
            break
        elif current["type"] == "textinput" and key.is_printable:
            input_buffer += key
        elif current["type"] == "textinput" and key.name == "KEY_BACKSPACE":
            input_buffer = input_buffer[:-1]
