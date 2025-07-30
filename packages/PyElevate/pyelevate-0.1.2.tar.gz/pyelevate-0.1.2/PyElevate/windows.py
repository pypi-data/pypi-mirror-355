from ctypes import POINTER, c_ulong, c_char_p, c_int, c_void_p, windll, Structure, sizeof, byref, WinError
from ctypes.wintypes import HANDLE, BOOL, DWORD, HWND, HINSTANCE, HKEY
import subprocess
import traceback
import sys

# Constant defintions


SEE_MASK_NOCLOSEPROCESS = 0x00000040
SEE_MASK_NO_CONSOLE = 0x00008000


# Type definitions

PHANDLE = POINTER(HANDLE)
PDWORD = POINTER(DWORD)


class ShellExecuteInfo(Structure):
    _fields_ = [
        ('cbSize',       DWORD),
        ('fMask',        c_ulong),
        ('hwnd',         HWND),
        ('lpVerb',       c_char_p),
        ('lpFile',       c_char_p),
        ('lpParameters', c_char_p),
        ('lpDirectory',  c_char_p),
        ('nShow',        c_int),
        ('hInstApp',     HINSTANCE),
        ('lpIDList',     c_void_p),
        ('lpClass',      c_char_p),
        ('hKeyClass',    HKEY),
        ('dwHotKey',     DWORD),
        ('hIcon',        HANDLE),
        ('hProcess',     HANDLE)]

    def __init__(self, **kw):
        super(ShellExecuteInfo, self).__init__()
        self.cbSize = sizeof(self)
        for field_name, field_value in kw.items():
            setattr(self, field_name, field_value)

PShellExecuteInfo = POINTER(ShellExecuteInfo)


# Function definitions

ShellExecuteEx = windll.shell32.ShellExecuteExA
ShellExecuteEx.argtypes = (PShellExecuteInfo, )
ShellExecuteEx.restype = BOOL

WaitForSingleObject = windll.kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = (HANDLE, DWORD)
WaitForSingleObject.restype = DWORD

CloseHandle = windll.kernel32.CloseHandle
CloseHandle.argtypes = (HANDLE, )
CloseHandle.restype = BOOL


# At last, the actual implementation!

def elevate(show_console=True, graphical=True, allow_cancel=True, log=True):
    try:
        if windll.shell32.IsUserAnAdmin():
            return

        params = ShellExecuteInfo(
            fMask=SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NO_CONSOLE,
            hwnd=None,
            lpVerb=b'runas',
            lpFile=sys.executable.encode('cp1252'),
            lpParameters=subprocess.list2cmdline(sys.argv).encode('cp1252'),
            nShow=int(show_console))

        if not ShellExecuteEx(byref(params)):
            raise WinError()

        handle = params.hProcess
        ret = DWORD()
        WaitForSingleObject(handle, -1)

        if windll.kernel32.GetExitCodeProcess(handle, byref(ret)) == 0:
            raise WinError()

        CloseHandle(handle)
        sys.exit(ret.value)
    except OSError as e:
        if e.winerror == 1223:
            if log: print("Elevation cancelled by user.")
            if allow_cancel:
                return False
            else:
                sys.exit(e.winerror)
        else:
            traceback.print_exc()

def is_admin():
    return bool(windll.shell32.IsUserAnAdmin())