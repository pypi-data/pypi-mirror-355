from .utils import wait_for_keypress, term
import sys

def spacer():
    return {"type": "spacer"}

def text(content):
    return {"type": "text", "content": content}

def option(label, action):
    return {"type": "option", "label": label, "action": action}

def sidebyside(left_label, left_action, right_label, right_action):
    return {
        "type": "sidebyside",
        "left": {"label": left_label, "action": left_action},
        "right": {"label": right_label, "action": right_action},
        "selected_side": "left"  # default selection
    }

def checkbox(*args):
    """
    Expects pairs of (label, initial_bool) and then optionally a submitbutton dict at the end.
    Usage: checkbox("Box1", False, "Box2", True, submitbutton("Submit", callback))
    """

    items = []
    submit = None

    # Separate checkboxes and submit button
    i = 0
    while i < len(args):
        arg = args[i]
        if isinstance(arg, dict) and arg.get("type") == "submitbutton":
            submit = arg
            i += 1
            continue
        label = arg
        checked = args[i + 1]
        items.append({"label": label, "checked": checked})
        i += 2

    # Internal state for checkbox navigation
    def run_checkbox_ui():
        selected = 0
        while True:
            print(term.clear())
            print(term.bold_underline("Checkboxes"))
            print()
            for idx, item in enumerate(items):
                mark = "[x]" if item["checked"] else "[ ]"
                line = f"{mark} {item['label']}"
                if idx == selected:
                    print(term.reverse(line))
                else:
                    print(line)
            print()
            if submit:
                line = f"   {submit['label']}   "
                print(term.center(line))
            print(term.dim("Use Up/Down to navigate, Space to toggle, Enter to submit, q to quit."))

            key = wait_for_keypress()
            if key.name == "KEY_UP":
                selected = (selected - 1) % len(items)
            elif key.name == "KEY_DOWN":
                selected = (selected + 1) % len(items)
            elif key == " ":
                items[selected]["checked"] = not items[selected]["checked"]
            elif key.name == "KEY_ENTER" or key == "\n":
                if submit and callable(submit["action"]):
                    # Pass checkbox states as dict to submit action
                    states = {item["label"]: item["checked"] for item in items}
                    submit["action"](states)
                return
            elif key == "q":
                sys.exit(0)

    return {"type": "checkbox", "run": run_checkbox_ui}

def submitbutton(label, action):
    return {"type": "submitbutton", "label": label, "action": action}

def textinput(prompt, action):
    """
    Runs a text input field, calls action with entered text on Enter.
    """

    def run_textinput_ui():
        inp = ""
        print(term.clear())
        print(term.bold_underline("Input"))
        print()
        print(prompt)
        print()
        print(term.yellow("> ") + inp, end="", flush=True)

        with term.cbreak():
            while True:
                val = term.inkey()
                if val.name == "KEY_ENTER" or val == "\n":
                    if callable(action):
                        action(inp)
                    return
                elif val.name == "KEY_BACKSPACE":
                    inp = inp[:-1]
                elif val.is_sequence:
                    # ignore other control sequences
                    pass
                else:
                    inp += val

                print(term.clear())
                print(term.bold_underline("Input"))
                print()
                print(prompt)
                print()
                print(term.yellow("> ") + inp, end="", flush=True)

    return {"type": "textinput", "run": run_textinput_ui}
