import ctypes
import subprocess
import time

import win32gui


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


class GameSession:
    """Owns game-process discovery, focus, window bounds, and input-language setup."""

    def __init__(
        self,
        logger=None,
        update_regions=None,
        ui_call=None,
        is_running=None,
        set_overlay_geometry=None,
        process_name="forzahorizon6.exe",
    ):
        self.logger = logger or (lambda message: None)
        self.update_regions = update_regions
        self.ui_call = ui_call
        self.is_running = is_running or (lambda: True)
        self.set_overlay_geometry = set_overlay_geometry
        self.process_name = process_name

    def log(self, message):
        self.logger(message)

    def set_english_input(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return

            hkl = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 1)
            ctypes.windll.user32.PostMessageW(hwnd, 0x0050, 0, hkl)

            wm_ime_control = 0x0283
            imc_set_open_status = 0x0006
            ctypes.windll.user32.SendMessageW(hwnd, wm_ime_control, imc_set_open_status, 0)
            self.log("已自动切换英文键盘/关闭中文输入法状态。")
        except Exception as e:
            self.log(f"自动防中文输入设置失败: {e}")

    def check_and_focus_game(self):
        self.log(f"检查游戏进程 ({self.process_name})...")
        try:
            target_pid = self._find_process_pid()
            if not target_pid:
                return False

            hwnds = self._find_windows_for_pid(target_pid)
            if not hwnds:
                return False

            hwnd = hwnds[0]
            if ctypes.windll.user32.IsIconic(hwnd):
                ctypes.windll.user32.ShowWindow(hwnd, 9)
            else:
                ctypes.windll.user32.ShowWindow(hwnd, 5)

            ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            self.set_english_input()

            if not self._update_game_window(hwnd):
                return False

            time.sleep(1.0)
            return True
        except Exception as e:
            self.log(f"检查进程异常: {e}")
            return False

    def _find_process_pid(self):
        create_no_window = 0x08000000
        cmd = f'tasklist /FI "IMAGENAME eq {self.process_name}" /NH /FO CSV'
        output = subprocess.check_output(cmd, shell=True, text=True, creationflags=create_no_window)

        if self.process_name.lower() not in output.lower():
            self.log(f"未发现 {self.process_name} 进程！(请确保游戏已运行)")
            return None

        for line in output.strip().split("\n"):
            parts = line.split('","')
            if len(parts) >= 2 and self.process_name.lower() in parts[0].lower():
                return int(parts[1].replace('"', ""))

        self.log("找到进程但无法解析PID！")
        return None

    def _find_windows_for_pid(self, target_pid):
        hwnds = []

        def foreach_window(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    window_pid = ctypes.c_ulong()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                    if window_pid.value == target_pid:
                        hwnds.append(hwnd)
            return True

        enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        ctypes.windll.user32.EnumWindows(enum_windows_proc(foreach_window), 0)
        return hwnds

    def _update_game_window(self, hwnd):
        try:
            client_rect = win32gui.GetClientRect(hwnd)
            point = win32gui.ClientToScreen(hwnd, (0, 0))
            gx, gy = point[0], point[1]
            gw, gh = client_rect[2], client_rect[3]

            if gw < 1000 or gh < 600:
                self.log(f"拦截到过小窗口 ({gw}x{gh})，判定为启动闪屏，等待主窗口加载...")
                return False

            if self.update_regions:
                self.update_regions(gx, gy, gw, gh)

            mx, my, mw, mh = self._monitor_bounds(hwnd, gx, gy, gw, gh)
            self._snap_overlay(mx, my, mw, mh)
            return True
        except Exception as e:
            self.log(f"获取窗口坐标失败: {e}")
            return True

    def _monitor_bounds(self, hwnd, gx, gy, gw, gh):
        monitor_default_to_nearest = 2
        hmonitor = ctypes.windll.user32.MonitorFromWindow(hwnd, monitor_default_to_nearest)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)

        if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            mx = info.rcMonitor.left
            my = info.rcMonitor.top
            mw = info.rcMonitor.right - info.rcMonitor.left
            mh = info.rcMonitor.bottom - info.rcMonitor.top
            return mx, my, mw, mh

        return gx, gy, gw, gh

    def _snap_overlay(self, mx, my, mw, mh):
        if not self.set_overlay_geometry:
            return

        def snap():
            if not self.is_running():
                return
            width = max(int(mw * 0.40), 650)
            height = max(int(mh * 0.15), 150)
            x = mx + mw - width - 20
            y = my + 20
            self.set_overlay_geometry(x, y, width, height)

        if self.ui_call:
            self.ui_call(snap)
        else:
            snap()
