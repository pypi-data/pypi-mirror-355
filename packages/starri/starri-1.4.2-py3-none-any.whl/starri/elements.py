from blessed import Terminal
from .core import wait_for_keypress

term = Terminal()

def spacer():
    """A blank line that cannot be selected."""
    return {"type": "spacer"}

def text(content):
    """Text line that cannot be selected."""
    return {"type": "text", "content": content}

def option(label, action):
    """Selectable option with label and action (callable)."""
    return {"type": "option", "label": label, "action": action}

def sidebyside(label1, action1, label2, action2):
    """
    Two selectable options side by side.
    Navigation between them with left/right arrows.
    """
    return {
        "type": "sidebyside",
        "left": {"label": label1, "action": action1},
        "right": {"label": label2, "action": action2}
    }

def checkbox(*args, onsubmit=None):
    """
    Checkbox list.

    args: tuples ("Label", initial_bool)
    onsubmit: callback receiving list of bool states when submitted
    """

    labels = [arg[0] for arg in args]
    states = [arg[1] for arg in args]

    selected_index = 0
    submitted = False

    while not submitted:
        print(term.clear())
        print(term.bold_underline("Use ↑↓ to navigate, Space to toggle, Enter to submit\n"))

        for i, label in enumerate(labels):
            prefix = "[x]" if states[i] else "[ ]"
            if i == selected_index:
                print(term.reverse(f"{prefix} {label}"))
            else:
                print(f"{prefix} {label}")

        val = wait_for_keypress()
        if val.name == "KEY_UP":
            selected_index = (selected_index - 1) % len(labels)
        elif val.name == "KEY_DOWN":
            selected_index = (selected_index + 1) % len(labels)
        elif val == " ":
            states[selected_index] = not states[selected_index]
        elif val.name == "KEY_ENTER" or val == "\n":
            submitted = True

    if onsubmit:
        onsubmit(states)

def submitbutton(label, action):
    """
    Submit button to be used inside checkbox or other compound elements.
    Just a wrapper around option for now.
    """
    return option(label, action)

def textinput(prompt, onsubmit=None):
    """
    Text input field.

    prompt: string prompt
    onsubmit: callback receiving entered string on submit
    """
    input_str = ""
    print(term.clear())
    print(term.bold(prompt))

    while True:
        print(term.move_down + term.clear_eol + input_str, end="", flush=True)
        val = wait_for_keypress()

        if val.name == "KEY_ENTER" or val == "\n":
            break
        elif val.name == "KEY_BACKSPACE" or val == "\x7f":
            input_str = input_str[:-1]
        elif isinstance(val, str) and len(val) == 1 and val.isprintable():
            input_str += val

    if onsubmit:
        onsubmit(input_str)

# end