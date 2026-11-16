import ctypes
try:
    user32 = ctypes.windll.user32
    h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
    if h_default:
        user32.SetThreadDesktop(h_default)
except Exception:
    pass
