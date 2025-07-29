import re
from blessed import Terminal
import signal

def starri(title, choices):
    selected = 0
    scroll_offset = 0

    def visible_length(text):
        return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

    term = Terminal()

    # Number of lines taken by title + spacing before choices
    title_lines = title.splitlines()
    header_height = len(title_lines) + 2

    # Tracks if terminal resized
    resized = [False]

    def on_resize(signum, frame):
        resized[0] = True

    # Set signal handler for window resize
    signal.signal(signal.SIGWINCH, on_resize)

    def render():
        nonlocal scroll_offset
        print(term.clear)
        height, width = term.height, term.width

        # Render title centered
        for i, line in enumerate(title_lines):
            visible_width = visible_length(line)
            x = (width - visible_width) // 2
            y = i
            print(term.move_xy(x, y) + line)

        # Determine how many choice lines fit on screen
        max_visible_choices = height - header_height
        # Count how many non-spacer choices exist
        choice_lines = [c for c in choices if c.get("type") != "spacer"]

        # Adjust scroll_offset to keep selected choice visible
        if selected < scroll_offset:
            scroll_offset = selected
        elif selected >= scroll_offset + max_visible_choices:
            scroll_offset = selected - max_visible_choices + 1

        visible_index = 0
        real_index = 0  # index through non-spacer choices
        for i, choice in enumerate(choices):
            if choice.get("type") == "spacer":
                y = header_height + visible_index
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
        nonlocal selected
        while True:
            selected = (selected + delta) % len(choices)
            if choices[selected].get("type") != "spacer":
                break

    with term.cbreak(), term.hidden_cursor():
        while True:
            render()
            key = term.inkey(timeout=0.1)
            if resized[0]:
                resized[0] = False
                # Just redraw on resize; continue loop to render
                continue

            if not key:
                continue
            if key.name == "KEY_UP":
                move_selection(-1)
            elif key.name == "KEY_DOWN":
                move_selection(1)
            elif key.name == "KEY_ENTER" or key == "\n":
                if choices[selected].get("type") != "spacer":
                    print(term.clear)
                    choices[selected]["onselect"]()
                    break
