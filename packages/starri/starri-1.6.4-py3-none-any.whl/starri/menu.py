import re
from blessed import Terminal

term = Terminal()

def cls():
    print(term.home + term.clear_eos, end="")

def starri(title, choices):
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

        visible_choices = [i for i, ch in enumerate(choices) if ch.get("type") != "spacer"]
        if not visible_choices:
            return

        current_real_index = visible_choices.index(selected)
        if current_real_index < scroll_offset:
            scroll_offset = current_real_index
        elif current_real_index >= scroll_offset + max_visible_choices:
            scroll_offset = current_real_index - max_visible_choices + 1

        real_index = 0
        display_index = 0
        for i, choice in enumerate(choices):
            if choice.get("type") == "spacer":
                if scroll_offset <= real_index < scroll_offset + max_visible_choices:
                    y = header_height + (real_index - scroll_offset)
                    print(term.move_xy(0, y) + "")
                continue

            if scroll_offset <= display_index < scroll_offset + max_visible_choices:
                label = choice["label"]
                prefix = "> " if i == selected else "  "
                label_with_cursor = prefix + label
                x = (width - len(label_with_cursor)) // 2
                y = header_height + (display_index - scroll_offset)
                print(term.move_xy(x, y) + (term.reverse(label_with_cursor) if i == selected else label_with_cursor))
            display_index += 1
            if i == selected:
                real_index = display_index - 1

    def move_selection(delta):
        nonlocal selected, needs_render
        while True:
            selected = (selected + delta) % len(choices)
            if choices[selected].get("type") != "spacer":
                needs_render = True
                break

    print(term.enter_fullscreen(), end="")  # ⬅️ Start fullscreen
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
                elif key.name in ("KEY_ENTER",) or key == "\n":
                    if choices[selected].get("type") != "spacer":
                        cls()
                        break
    finally:
        print(term.exit_fullscreen(), end="")  # ⬅️ Exit fullscreen no matter what

    # After fullscreen exit, run the selected action
    if choices[selected].get("type") != "spacer":
        choices[selected]["onselect"]()
