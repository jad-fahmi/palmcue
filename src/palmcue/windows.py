"""Small Win32 adapter. No input is sent until explicitly called by a session."""

import ctypes
import os
import sys
from ctypes import wintypes as w

from palmcue.actions import OutputBlocked, Target

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", w.LONG),
        ("dy", w.LONG),
        ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", w.WORD),
        ("wScan", w.WORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", w.DWORD), ("u", INPUTUNION)]


class WindowsBackend:
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Presentation control is currently available on Windows 10 and 11.")
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.api.GetForegroundWindow.restype = w.HWND
        self.api.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
        self.api.GetWindowTextLengthW.argtypes = [w.HWND]
        self.api.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
        self.api.IsWindowVisible.argtypes = [w.HWND]
        self.api.GetClientRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
        self.api.ClientToScreen.argtypes = [w.HWND, ctypes.POINTER(w.POINT)]
        self.api.WindowFromPoint.argtypes = [w.POINT]
        self.api.WindowFromPoint.restype = w.HWND
        self.api.GetAncestor.argtypes = [w.HWND, w.UINT]
        self.api.GetAncestor.restype = w.HWND
        self.api.SendInput.argtypes = [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.api.SendInput.restype = w.UINT
        self.api.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.api.GetAsyncKeyState.restype = w.SHORT

    def foreground(self) -> int:
        return self.api.GetForegroundWindow() or 0

    def process(self, handle: int) -> int:
        pid = w.DWORD()
        self.api.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        return pid.value

    def windows(self) -> list[Target]:
        targets = []
        callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

        @callback_type
        def visit(handle, _):
            size = self.api.GetWindowTextLengthW(handle)
            if size and self.api.IsWindowVisible(handle) and self.process(handle) != os.getpid():
                title = ctypes.create_unicode_buffer(size + 1)
                self.api.GetWindowTextW(handle, title, size + 1)
                targets.append(Target(handle, self.process(handle), title.value))
            return True

        self.api.EnumWindows.argtypes = [callback_type, w.LPARAM]
        self.api.EnumWindows(visit, 0)
        return sorted(targets, key=lambda t: t.title.casefold())

    def modifiers_down(self) -> bool:
        return any(
            self.api.GetAsyncKeyState(key) & 0x8000 for key in (0x10, 0x11, 0x12, 0x5B, 0x5C)
        )

    def _send(self, entries: list[INPUT]) -> None:
        array = (INPUT * len(entries))(*entries)
        if self.api.SendInput(len(entries), array, ctypes.sizeof(INPUT)) != len(entries):
            raise OutputBlocked(
                "Windows blocked the controls. Run your presentation normally, "
                "without 'Run as administrator'."
            )

    def key(self, code: int, control: bool = False) -> None:
        def entry(key, up=False):
            return INPUT(type=1, ki=KEYBDINPUT(wVk=key, dwFlags=2 if up else 0))

        entries = [entry(code), entry(code, True)]
        if control:
            entries = [entry(0x11), *entries, entry(0x11, True)]
        try:
            self._send(entries)
        except OutputBlocked:
            # Best effort release after a partially accepted SendInput batch.
            self._send([entry(code, True), entry(0x11, True)] if control else [entry(code, True)])
            raise

    def move(self, handle: int, x: float, y: float) -> None:
        rect, origin = w.RECT(), w.POINT()
        if not self.api.GetClientRect(handle, ctypes.byref(rect)):
            raise OutputBlocked("The presentation window is no longer available.")
        if not self.api.ClientToScreen(handle, ctypes.byref(origin)):
            raise OutputBlocked("The presentation window is no longer available.")
        px = origin.x + round(min(1, max(0, x)) * max(0, rect.right - 1))
        py = origin.y + round(min(1, max(0, y)) * max(0, rect.bottom - 1))
        vx, vy = self.api.GetSystemMetrics(76), self.api.GetSystemMetrics(77)
        vw, vh = self.api.GetSystemMetrics(78), self.api.GetSystemMetrics(79)
        self._send(
            [
                INPUT(
                    type=0,
                    mi=MOUSEINPUT(
                        dx=round((px - vx) * 65535 / max(1, vw - 1)),
                        dy=round((py - vy) * 65535 / max(1, vh - 1)),
                        dwFlags=0xC001,
                    ),
                )
            ]
        )

    def click(self, handle: int) -> None:
        point = w.POINT()
        self.api.GetCursorPos(ctypes.byref(point))
        under = self.api.WindowFromPoint(point)
        if self.api.GetAncestor(under, 2) != handle:
            raise OutputBlocked("The pointer left the presentation. Start presenting again.")
        try:
            self._send(
                [INPUT(type=0, mi=MOUSEINPUT(dwFlags=2)), INPUT(type=0, mi=MOUSEINPUT(dwFlags=4))]
            )
        except OutputBlocked:
            self._send([INPUT(type=0, mi=MOUSEINPUT(dwFlags=4))])
            raise
