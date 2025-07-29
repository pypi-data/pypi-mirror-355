import re
from blessed import Terminal

term = Terminal()  # create term once, globally

def cls():
    # Full clear + move cursor home
    print(term.clear, end="")

def starri(title, choices):
    selected = 0
    scroll_offset = 0

    def visible_length(text):
        return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

    title_lines = title.splitlines()
    header_height = len(title_lines) + 2

    prev_size = (term.height, term.width)
    needs_render = True  # flag to render only when needed

    def render():
        nonlocal scroll_offset
        # Instead of full clear, move cursor to home and clear from there down
        print(term.home + term.clear_eos, end="")

        height, width = term.height, term.width

        # Render title centered
        for i, line in enumerate(title_lines):
            visible_width = visible_length(line)
            x = (width - visible_width) // 2
            y = i
            print(term.move_xy(x, y) + line)

        max_visible_choices = height - header_height

        # Adjust scroll_offset to keep selected choice visible
        if selected < scroll_offset:
            scroll_offset = selected
        elif selected >= scroll_offset + max_visible_choices:
            scroll_offset = selected - max_visible_choices + 1

        visible_index = 0
        real_index = 0
        for i, choice in enumerate(choices):
            if choice.get("type") == "spacer":
                y = header_height + visible_index
                # Only print spacer if visible within scroll window
                if 0 <= visible_index - scroll_offset < max_visible_choices:
                    print(term.move_xy(0, y - scroll_offset))
                visible_index += 1
                continue

            if real_index >= scroll_offset and real_index < scroll_offset + max_visible_choices:
                label = choice["label"]
                label_with_cursor = f"> {label}" if i == selected else f"  {label}"
                x = (width - len(label_with_cursor)) // 2
                y = header_height + (real_index - scroll_offset)
                print(term.move_xy(x, y) + (term.reverse(label_with_cursor) if i == selected else label_with_cursor))
            real_index += 1

    def move_selection(delta):
        nonlocal selected, needs_render
        while True:
            selected = (selected + delta) % len(choices)
            if choices[selected].get("type") != "spacer":
                needs_render = True
                break

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
            elif key.name == "KEY_ENTER" or key == "\n":
                if choices[selected].get("type") != "spacer":
                    cls()
                    choices[selected]["onselect"]()
                    break
