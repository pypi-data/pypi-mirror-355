from .core import term

def safe_format(attr, text):
    cap = getattr(term, attr, None)
    if callable(cap):
        try:
            return cap(text)
        except Exception:
            return text
    return text
