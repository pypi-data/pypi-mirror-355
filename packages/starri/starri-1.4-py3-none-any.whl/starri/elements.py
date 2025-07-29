from blessed import Terminal
term = Terminal()

class Element:
    def render(self, selected=False): raise NotImplementedError
    def is_selectable(self): return False
    def on_select(self): pass

class Spacer(Element):
    def render(self, selected=False): return "", False

class Text(Element):
    def __init__(self, txt): self.txt = txt
    def render(self, selected=False): return self.txt, False

class Option(Element):
    def __init__(self, txt, action): self.txt, self.action = txt, action
    def render(self, selected=False):
        prefix = term.bold_red("> ") if selected else "  "
        return prefix + self.txt, True
    def is_selectable(self): return True
    def on_select(self): return self.action()

class SideBySide(Element):
    def __init__(self, left_text, left_action, right_text, right_action):
        self.left_text, self.left_action = left_text, left_action
        self.right_text, self.right_action = right_text, right_action
        self.selected_side = 0

    def render(self, selected=False):
        lsel = term.reverse if selected and self.selected_side == 0 else ""
        rsel = term.reverse if selected and self.selected_side == 1 else ""
        out = f"{lsel} {self.left_text} {term.normal}    {rsel} {self.right_text} {term.normal}"
        return term.center(out), True

    def is_selectable(self): return True

    def on_key(self, key):
        if key.code == term.KEY_LEFT:
            self.selected_side = 0
        elif key.code == term.KEY_RIGHT:
            self.selected_side = 1

    def on_select(self):
        return self.left_action() if self.selected_side == 0 else self.right_action()

class Checkboxes(Element):
    def __init__(self, *args):
        self.boxes = []
        self.submit = None
        i = 0
        while i < len(args):
            if isinstance(args[i], str):
                self.boxes.append([args[i], args[i+1]])
                i += 2
            elif isinstance(args[i], SubmitButton):
                self.submit = args[i]
                i += 1

        self.selected_index = 0

    def render(self, selected=False):
        output = []
        for i, (label, checked) in enumerate(self.boxes):
            sel = term.reverse if selected and i == self.selected_index else ""
            state = "[X]" if checked else "[ ]"
            output.append(f"{sel} {state} {label} {term.normal}")
        if self.submit:
            sub = self.submit.render(selected=(selected and self.selected_index == len(self.boxes)))[0]
            output.append(sub)
        return "\n".join(output), True

    def is_selectable(self): return True

    def on_key(self, key):
        max_idx = len(self.boxes) + (1 if self.submit else 0)
        if key.code == term.KEY_DOWN:
            self.selected_index = (self.selected_index + 1) % max_idx
        elif key.code == term.KEY_UP:
            self.selected_index = (self.selected_index - 1) % max_idx
        elif key == " " and self.selected_index < len(self.boxes):
            self.boxes[self.selected_index][1] = not self.boxes[self.selected_index][1]

    def on_select(self):
        if self.submit and self.selected_index == len(self.boxes):
            return self.submit.on_select(self.boxes)

class SubmitButton:
    def __init__(self, text, action): self.text, self.action = text, action
    def render(self, selected=False):
        prefix = term.bold_green("> ") if selected else "  "
        return f"{prefix}{self.text}", True
    def on_select(self, boxes):
        box_dict = {name: state for name, state in boxes}
        return self.action(box_dict)

class TextInput(Element):
    def __init__(self, prompt, action):
        self.prompt = prompt
        self.buffer = ""
        self.action = action

    def render(self, selected=False):
        cursor = "_" if selected else ""
        return f"{self.prompt} {self.buffer}{cursor}", True

    def is_selectable(self): return True

    def on_key(self, key):
        if key.code == term.KEY_BACKSPACE:
            self.buffer = self.buffer[:-1]
        elif key.is_sequence: pass
        elif key:
            self.buffer += key

    def on_select(self):
        return self.action(self.buffer)

# Factories
def spacer(): return Spacer()
def text(txt): return Text(txt)
def option(txt, action): return Option(txt, action)
def sidebyside(l, la, r, ra): return SideBySide(l, la, r, ra)
def checkbox(*args): return Checkboxes(*args)
def submitbutton(txt, act): return SubmitButton(txt, act)
def textinput(prompt, action): return TextInput(prompt, action)