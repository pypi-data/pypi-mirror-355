from blessed import Terminal
import sys
import termios
import tty

term = Terminal()

def starri(title, content):
    if isinstance(content, dict):
        content = list(content.values())
    if isinstance(content, set):
        content = list(content)

    selected_index = 0
    checkbox_states = {}
    input_buffer = ""
    sidebyside_index = 0
    selected_sub = 0  # For checkbox sub-selection

    def get_selectables():
        return [i for i, item in enumerate(content) if item["type"] in ("option", "sidebyside", "checkbox", "textinput")]

    selectables = get_selectables()

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
                print(term.reverse(line) if selected else line)
            elif item["type"] == "sidebyside":
                labels = [o["label"] for o in item["options"]]
                rendered = []
                for i, label in enumerate(labels):
                    if selected and i == sidebyside_index:
                        rendered.append(term.reverse(f"[{label}]"))
                    else:
                        rendered.append(f" {label} ")
                print("   ".join(rendered))
            elif item["type"] == "checkbox":
                for i, box in enumerate(item["items"]):
                    state = checkbox_states.get(i, box["checked"])
                    prefix = "[x]" if state else "[ ]"
                    line = f"{prefix} {box['label']}"
                    print(term.reverse(line) if selected and selected_sub == i else line)
                submit_line = "[ Submit ]"
                print()
                print("   " + (term.reverse(submit_line) if selected and selected_sub == len(item["items"]) else submit_line))
            elif item["type"] == "textinput":
                line = f"{item['prompt']} {input_buffer}" if selected else item["prompt"]
                print(term.reverse(line) if selected else line)

        print("\nUse arrow keys to navigate, Enter to select, q to quit.")

    while True:
        render()
        key = term.inkey()

        if key.name == "KEY_UP":
            # Move selection up
            selected_index = (selected_index - 1) % len(selectables)
            selected_sub = 0
            sidebyside_index = 0
        elif key.name == "KEY_DOWN":
            # Move selection down
            selected_index = (selected_index + 1) % len(selectables)
            selected_sub = 0
            sidebyside_index = 0
        else:
            current = content[selectables[selected_index]]
            if current["type"] == "sidebyside":
                if key.name == "KEY_LEFT":
                    sidebyside_index = (sidebyside_index - 1) % len(current["options"])
                elif key.name == "KEY_RIGHT":
                    sidebyside_index = (sidebyside_index + 1) % len(current["options"])
            elif current["type"] == "checkbox":
                if key.name == "KEY_UP":
                    selected_sub = (selected_sub - 1) % (len(current["items"]) + 1)
                elif key.name == "KEY_DOWN":
                    selected_sub = (selected_sub + 1) % (len(current["items"]) + 1)
                elif key == "\n":
                    if selected_sub < len(current["items"]):
                        # Toggle checkbox
                        checkbox_states[selected_sub] = not checkbox_states.get(selected_sub, current["items"][selected_sub]["checked"])
                    else:
                        # Submit
                        if callable(current["submit"]):
                            selected_values = [checkbox_states.get(i, box["checked"]) for i, box in enumerate(current["items"])]
                            return current["submit"](*selected_values)
            elif current["type"] == "textinput":
                if key == "\n":
                    return current["callback"](input_buffer)
                elif key.name == "KEY_BACKSPACE":
                    input_buffer = input_buffer[:-1]
                elif key.is_printable:
                    input_buffer += key
            elif key == "\n":
                if current["type"] == "option":
                    action = current["action"]
                    if callable(action):
                        return action()
                elif current["type"] == "sidebyside":
                    action = current["options"][sidebyside_index]["action"]
                    if callable(action):
                        return action()
            elif key.lower() == "q":
                break

# Example usage of starri could go here
