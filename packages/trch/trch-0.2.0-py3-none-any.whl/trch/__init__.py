from .main import ClipboardHelper

clipboard_helper = ClipboardHelper()


def _register_methods():
    """
    Регистрация методов из ClipboardHelper в глобальном пространстве модуля.
    """
    global clipboard_helper
    for method_name in clipboard_helper.methods_info:
        if hasattr(clipboard_helper, method_name):
            globals()[method_name] = getattr(clipboard_helper, method_name)


_register_methods()

__all__ = list(clipboard_helper.methods_info.keys()) + ["clipboard_helper"]
