"""
Arabic text fixer module.
Fixes Arabic text for proper display in tkinter on Linux/Windows.
Requires: pip install arabic-reshaper python-bidi --break-system-packages
"""

# Cache reshaper instance for performance
_reshaper = None

def ar(text):
    """
    Fix Arabic text for tkinter.
    Reshapes Arabic characters and applies bidirectional text algorithm.
    Safe to call with None or non-string values.
    """
    global _reshaper

    if not text or not isinstance(text, str):
        return text

    # Quick check if the text contains any Arabic characters to avoid unnecessary processing
    # Arabic Unicode range: 0600-06FF
    has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
    if not has_arabic:
        return text

    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        if _reshaper is None:
            configuration = {
                'delete_harakat': False,
                'support_default_index': True,
                # isolated forms work better for standard Tkinter fonts
                'use_unshaped_instead_of_isolated': False
            }
            _reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)

        reshaped = _reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        # Fallback to original text if libraries are missing
        return text
