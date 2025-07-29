from blessed import Terminal
import re

term = Terminal()

# Utility
def cls():
    print(term.home + term.clear_eos, end="")

# Simplified constructors
def option(label, onselect):
    return {"type": "option", "label": label, "onselect": onselect}

def spacer():
    return {"type": "spacer"}

def checkbox(label, checked=False):
    return {"type": "checkbox", "label": label, "checked": checked}

# Main TUI function
def starri(title, content):
    selected = 0
    scroll_offset = 0

    def visible_length(text):
        return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

    title_lines = title.splitlines()
    header_height = len(title_lines) + 2

    prev_size = (term.height, term.width)
    needs_render = True

    def render():
        nonlocal scroll_offset
        print(term.home + term.clear_eos, end="")

        height, width = term.height, term.width

        for i, line in enumerate(title_lines):
            visible_width = visible_length(line)
            x = (width - visible_width) // 2
            y = i
            print(term.move_xy(x, y) + line)

        max_visible_choices = height - header_height

        visible_indices = [i for i, item in enumerate(content) if item.get("type") != "spacer"]
        if not visible_indices:
            return

        current_real_index = visible_indices.index(selected)
        if current_real_index < scroll_offset:
            scroll_offset = current_real_index
        elif current_real_index >= scroll_offset + max_visible_choices:
            scroll_offset = current_real_index - max_visible_choices + 1

        display_index = 0
        for i, item in enumerate(content):
            if item.get("type") == "spacer":
                if scroll_offset <= display_index < scroll_offset + max_visible_choices:
                    y = header_height + (display_index - scroll_offset)
                    print(term.move_xy(0, y) + "")
                continue

            if scroll_offset <= display_index < scroll_offset + max_visible_choices:
                if item["type"] == "checkbox":
                    box = "[X]" if item.get("checked") else "[ ]"
                    line = f"{box} - {item['label']}"
                else:
                    line = f"> {item['label']}" if i == selected else f"  {item['label']}"

                x = (width - visible_length(line)) // 2
                y = header_height + (display_index - scroll_offset)
                print(term.move_xy(x, y) + (term.reverse(line) if i == selected else line))

            display_index += 1

    def move_selection(delta):
        nonlocal selected, needs_render
        while True:
            selected = (selected + delta) % len(content)
            if content[selected].get("type") != "spacer":
                needs_render = True
                break

    print(term.enter_fullscreen(), end="")
    try:
        with term.cbreak(), term.hidden_cursor():
            while True:
                current_size = (term.height, term.width)
                if current_size != prev_size:
                    prev_size = current_size
                    needs_render = True

                if needs_render:
                    render()
                    needs_render = False

                key = term.inkey(timeout=0.1)
                if not key:
                    continue

                if key.name == "KEY_UP":
                    move_selection(-1)
                elif key.name == "KEY_DOWN":
                    move_selection(1)
                elif key == " ":
                    if content[selected].get("type") == "checkbox":
                        content[selected]["checked"] = not content[selected]["checked"]
                        needs_render = True
                elif key.name in ("KEY_ENTER",) or key == "\n":
                    if content[selected].get("type") != "spacer":
                        cls()
                        break
    finally:
        print(term.exit_fullscreen(), end="")

    if content[selected].get("type") != "spacer":
        content[selected].get("onselect", lambda: None)()
