from blessed import Terminal
import sys
from .utils import safe_format

term = Terminal()
selected_index = 0

current_elements = []

def wait_for_keypress():
    with term.cbreak():
        return term.inkey()

def render():
    print(term.home + term.clear)
    print(term.bold(current_title))
    print()
    for i, element in enumerate(current_elements):
        if element['type'] == 'option':
            text = element['label']
            if i == selected_index:
                print(term.reverse(text))
            else:
                print(text)
        elif element['type'] == 'text':
            print(element['label'])
        elif element['type'] == 'spacer':
            print()
        elif element['type'] == 'sidebyside':
            left = element['left']
            right = element['right']
            print(f"{left:^20}    {right:^20}")
        elif element['type'] == 'checkbox':
            status = '[x]' if element['checked'] else '[ ]'
            text = f"{status} {element['label']}"
            if i == selected_index:
                print(term.reverse(text))
            else:
                print(text)
        elif element['type'] == 'textinput':
            if i == selected_index:
                print(term.reverse(f"{element['label']} {element.get('value', '')}"))
            else:
                print(f"{element['label']} {element.get('value', '')}")
    print()
    print(safe_format("dim", "Use arrow keys to navigate, Enter to select, q to quit."))

def starri(title, content):
    global selected_index, current_elements, current_title
    current_elements = content
    current_title = title
    selected_index = 0
    while True:
        render()
        key = wait_for_keypress()
        if key.code == term.KEY_UP:
            selected_index = (selected_index - 1) % len(current_elements)
        elif key.code == term.KEY_DOWN:
            selected_index = (selected_index + 1) % len(current_elements)
        elif key.code == term.KEY_ENTER or key == '\n':
            action = current_elements[selected_index].get('action')
            if action:
                return action()
        elif key.lower() == 'q':
            sys.exit(0)