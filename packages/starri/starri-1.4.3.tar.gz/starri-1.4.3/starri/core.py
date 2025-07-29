from .elements import spacer, text, option, sidebyside, checkbox, textinput
from .utils import wait_for_keypress, term
import sys

def starri(title="", content=None):
    if content is None:
        content = []

    # Flatten content if needed
    if isinstance(content, (set, tuple)):
        content = list(content)

    # Allow dict with "run" key to handle their own interaction (checkbox, textinput)
    for item in content:
        if "type" in item and item["type"] in ("checkbox", "textinput"):
            # Run their UI and then return
            item["run"]()
            return

    # Gather selectable indexes
    selectable_indexes = [i for i, item in enumerate(content) if item["type"] in ("option", "sidebyside")]
    if not selectable_indexes:
        # No selectable items, just print content
        print(term.clear())
        print(term.bold_underline(title))
        print()
        for item in content:
            if item["type"] == "spacer":
                print()
            elif item["type"] == "text":
                print(item["content"])
        input("Press Enter to exit...")
        return

    selected_index_pos = 0  # index in selectable_indexes list

    def render():
        print(term.clear())
        print(term.bold_underline(title))
        print()

        for i, item in enumerate(content):
            is_selected = (selectable_indexes[selected_index_pos] == i)
            if item["type"] == "spacer":
                print()
            elif item["type"] == "text":
                print(item["content"])
            elif item["type"] == "option":
                line = item["label"]
                print(term.reverse(line) if is_selected else line)
            elif item["type"] == "sidebyside":
                left = item["left"]["label"]
                right = item["right"]["label"]

                if "selected_side" not in item:
                    item["selected_side"] = "left"

                left_sel = is_selected and item["selected_side"] == "left"
                right_sel = is_selected and item["selected_side"] == "right"

                left_text = term.reverse(left) if left_sel else left
                right_text = term.reverse(right) if right_sel else right

                space = " " * (term.width // 4)
                print(space + left_text + space + right_text)
        print()
        print(term.dim("Use arrow keys to navigate, Enter to select, q to quit."))

    while True:
        render()
        key = wait_for_keypress()

        if key.name == "KEY_UP":
            selected_index_pos = (selected_index_pos - 1) % len(selectable_indexes)
        elif key.name == "KEY_DOWN":
            selected_index_pos = (selected_index_pos + 1) % len(selectable_indexes)
        elif key.name == "KEY_LEFT":
            current_item = content[selectable_indexes[selected_index_pos]]
            if current_item["type"] == "sidebyside":
                if current_item["selected_side"] == "right":
                    current_item["selected_side"] = "left"
        elif key.name == "KEY_RIGHT":
            current_item = content[selectable_indexes[selected_index_pos]]
            if current_item["type"] == "sidebyside":
                if current_item["selected_side"] == "left":
                    current_item["selected_side"] = "right"
        elif key.name == "KEY_ENTER" or key == "\n":
            current_item = content[selectable_indexes[selected_index_pos]]
            if current_item["type"] == "option":
                action = current_item["action"]
                if callable(action):
                    action()
                else:
                    sys.exit(0)
                return
            elif current_item["type"] == "sidebyside":
                side = current_item.get("selected_side", "left")
                action = current_item[side]["action"]
                if callable(action):
                    action()
                else:
                    sys.exit(0)
                return
        elif key == "q":
            sys.exit(0)
