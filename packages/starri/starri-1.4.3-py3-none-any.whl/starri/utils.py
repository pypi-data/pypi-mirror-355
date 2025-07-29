from blessed import Terminal

term = Terminal()

def wait_for_keypress():
    with term.cbreak():
        val = term.inkey(timeout=None)
        return val
