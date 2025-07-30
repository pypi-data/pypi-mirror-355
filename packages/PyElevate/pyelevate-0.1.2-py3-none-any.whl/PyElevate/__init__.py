import sys

def elevate(show_console=True, graphical=True):
    """
    Re-launch the current process with root/admin privileges

    When run as root, this function does nothing.

    When not run as root, this function replaces the current process (Linux,
    macOS) or creates a child process, waits, and exits (Windows).

    :param show_console: (Windows only) if True, show a new console for the
        child process. Ignored on Linux / macOS.
    :param graphical: (Linux / macOS only) if True, attempt to use graphical
        programs (gksudo, etc). Ignored on Windows.
    """
    if sys.platform.startswith("win"):
        from PyElevate.windows import elevate
    else:
        from PyElevate.posix import elevate
    elevate(show_console, graphical)

def elevated():
    """
    Checks if the process is elevated

    If the process is elevated returns True
    """
    if sys.platform.startswith("win"):
        from PyElevate.windows import is_admin
        return is_admin()
    else:
        from PyElevate.posix import is_root
        return is_root()
    