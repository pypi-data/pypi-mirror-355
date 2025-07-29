def spacer():
    return {"type": "spacer"}

def text(label):
    return {"type": "text", "label": label}

def option(label, action):
    return {"type": "option", "label": label, "action": action}

def sidebyside(left_label, left_action, right_label, right_action):
    return {"type": "sidebyside", "left": left_label, "right": right_label, "left_action": left_action, "right_action": right_action}

def checkbox(*args):
    elements = []
    i = 0
    while i < len(args):
        if isinstance(args[i], str) and isinstance(args[i+1], bool):
            elements.append({"type": "checkbox", "label": args[i], "checked": args[i+1]})
            i += 2
        elif isinstance(args[i], dict):
            elements.append(args[i])
            i += 1
        else:
            i += 1
    return elements

def textinput(prompt, action):
    return {"type": "textinput", "label": prompt, "action": action, "value": ""}
