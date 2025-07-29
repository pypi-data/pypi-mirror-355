from blessed import Terminal
from .elements import spacer, text, option, sidebyside, checkbox, textinput
import sys

term = Terminal()

def wait_for_keypress():
    with term.cbreak():
        val = term.inkey(timeout=None)
        return val

def starri(title="", content=None):
    if content is None:
        content = []

    # Flatten content if it was a set or something else
    if isinstance(content, (set, tuple)):
        content = list(content)

    selected_index = 0

    # Filter selectable items indexes for navigation
    selectable_indexes = []
    for i, item in enumerate(content):
        if item["type"] in ("option", "sidebyside"):
            selectable_indexes.append(i)

    def render(selected_idx):
        print(term.clear())
        print(term.bold_underline(title))
        print()

        for i, item in enumerate(content):
            is_selected = (i == selected_idx)
            if item["type"] == "spacer":
                print()
            elif item["type"] == "text":
                print(item["content"])
            elif item["type"] == "option":
                line = item["label"]
                if is_selected:
                    print(term.reverse(line))
                else:
                    print(line)
            elif item["type"] == "sidebyside":
                left = item["left"]["label"]
                right = item["right"]["label"]
                # We'll highlight left or right option depending on internal sidebyside state
                # Store which side is selected in item dict for persistence
                if "selected_side" not in item:
                    item["selected_side"] = "left"

                left_sel = is_selected and item["selected_side"] == "left"
                right_sel = is_selected and item["selected_side"] == "right"

                left_text = term.reverse(left) if left_sel else left
                right_text = term.reverse(right) if right_sel else right

                # Simple center spacing
                space = " " * (term.width // 4)
                print(space + left_text + space + right_text)
        print()
        print(term.dim("Use arrow keys to navigate, Enter to select."))

    while True:
        # Clamp selected_index to selectable items
        if selectable_indexes:
            selected_index = selectable_indexes[selected_index % len(selectable_indexes)]
        else:
            selected_index = 0

        render(selected_index)
        key = wait_for_keypress()

        if key.name == "KEY_UP":
            # Move selection up
            idx_pos = selectable_indexes.index(selected_index)
            idx_pos = (idx_pos - 1) % len(selectable_indexes)
            selected_index = selectable_indexes[idx_pos]

        elif key.name == "KEY_DOWN":
            # Move selection down
            idx_pos = selectable_indexes.index(selected_index)
            idx_pos = (idx_pos + 1) % len(selectable_indexes)
            selected_index = selectable_indexes[idx_pos]

        elif key.name == "KEY_LEFT":
            # If sidebyside selected, switch left/right
            item = content[selected_index]
            if item["type"] == "sidebyside":
                if item.get("selected_side") == "right":
                    item["selected_side"] = "left"

        elif key.name == "KEY_RIGHT":
            item = content[selected_index]
            if item["type"] == "sidebyside":
                if item.get("selected_side") == "left":
                    item["selected_side"] = "right"

        elif key.name == "KEY_ENTER" or key == "\n":
            item = content[selected_index]
            if item["type"] == "option":
                action = item["action"]
                if callable(action):
                    action()
                else:
                    sys.exit(0)  # if action is exit or something else
                return
            elif item["type"] == "sidebyside":
                side = item.get("selected_side", "left")
                action = item[side]["action"]
                if callable(action):
                    action()
                else:
                    sys.exit(0)
                return

        elif key == "q":
            # Quit on 'q' key
            sys.exit(0)
