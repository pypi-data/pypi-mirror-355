from blessed import Terminal
term = Terminal()

def starri(title="", content=[]):
    selected_idx = 0

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            print(term.home + term.clear)
            print(term.center(term.bold(title)) + "\n")

            lines = []
            for idx, item in enumerate(content):
                rendered, _ = item.render(selected=(idx == selected_idx))
                lines.append(rendered)
            print("\n".join(lines))

            key = term.inkey()

            current = content[selected_idx]
            if hasattr(current, "on_key"):
                current.on_key(key)

            if key.code == term.KEY_DOWN:
                selected_idx = (selected_idx + 1) % len(content)
                while not content[selected_idx].is_selectable():
                    selected_idx = (selected_idx + 1) % len(content)
            elif key.code == term.KEY_UP:
                selected_idx = (selected_idx - 1) % len(content)
                while not content[selected_idx].is_selectable():
                    selected_idx = (selected_idx - 1) % len(content)
            elif key.code in [term.KEY_ENTER] or key == "\n":
                result = content[selected_idx].on_select()
                if result is not None:
                    return result