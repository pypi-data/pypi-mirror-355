import re
from blessed import Terminal

term = Terminal()

def cls():
    print(term.clear, end="")

def starri(title, choices):
    selected = 0
    scroll_offset = 0

    def visible_length(text):
        return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

    title_lines = title.splitlines()
    header_height = len(title_lines) + 2

    prev_size = (term.height, term.width)
    needs_render = True  # full redraw flag

    # Store previously selected index to optimize redraw
    prev_selected = None

    def render_full():
        nonlocal scroll_offset
        # Clear screen once at start or on resize
        cls()
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
                visible_index += 1
                continue

            if real_index >= scroll_offset and real_index < scroll_offset + max_visible_choices:
                label = choice["label"]
                label_with_cursor = f"> {label}" if i == selected else f"  {label}"
                x = (width - len(label_with_cursor)) // 2
                y = header_height + (real_index - scroll_offset)
                print(term.move_xy(x, y) + (term.reverse(label_with_cursor) if i == selected else label_with_cursor))
            real_index += 1

    def update_selection(old, new):
        height, width = term.height, term.width
        max_visible_choices = height - header_height

        # Compute scroll offset update for new selected
        nonlocal scroll_offset
        if new < scroll_offset:
            scroll_offset = new
        elif new >= scroll_offset + max_visible_choices:
            scroll_offset = new - max_visible_choices + 1

        # Redraw old selected line if visible
        if old is not None:
            # Find old selected's position in visible window
            real_index_old = sum(1 for i,c in enumerate(choices[:old]) if c.get("type") != "spacer")
            if scroll_offset <= real_index_old < scroll_offset + max_visible_choices:
                choice = choices[old]
                label = choice["label"]
                label_with_cursor = f"  {label}"
                x = (width - len(label_with_cursor)) // 2
                y = header_height + (real_index_old - scroll_offset)
                print(term.move_xy(x, y) + label_with_cursor)

        # Redraw new selected line if visible
        real_index_new = sum(1 for i,c in enumerate(choices[:new]) if c.get("type") != "spacer")
        if scroll_offset <= real_index_new < scroll_offset + max_visible_choices:
            choice = choices[new]
            label = choice["label"]
            label_with_cursor = f"> {label}"
            x = (width - len(label_with_cursor)) // 2
            y = header_height + (real_index_new - scroll_offset)
            print(term.move_xy(x, y) + term.reverse(label_with_cursor))

        # If scroll offset changed so that visible lines changed, fallback to full redraw
        # (Optional: you can track previous scroll_offset and compare)

    def move_selection(delta):
        nonlocal selected, needs_render, prev_selected
        old = selected
        while True:
            selected = (selected + delta) % len(choices)
            if choices[selected].get("type") != "spacer":
                break

        # If scroll offset or selected changed, update only those lines
        if old != selected:
            prev_selected = old
            needs_render = False
            update_selection(old, selected)

    with term.cbreak(), term.hidden_cursor():
        cls()
        render_full()
        while True:
            current_size = (term.height, term.width)
            if current_size != prev_size:
                prev_size = current_size
                needs_render = True
                cls()
                render_full()

            if needs_render:
                render_full()
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
