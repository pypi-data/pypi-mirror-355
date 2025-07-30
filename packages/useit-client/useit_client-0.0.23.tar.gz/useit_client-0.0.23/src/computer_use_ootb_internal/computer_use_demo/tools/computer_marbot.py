import ctypes
import time
from time import sleep
import pyautogui  # 用于获取当前鼠标位置
import uiautomation as auto

# =========================== 结构体定义 ===========================
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUT_UNION)]

# =========================== 常量定义 ===========================
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# 键盘扫描码表（可扩展）
VK_CODE = {
    # 字母
    'a': 0x1E, 'b': 0x30, 'c': 0x2E, 'd': 0x20, 'e': 0x12, 'f': 0x21,
    'g': 0x22, 'h': 0x23, 'i': 0x17, 'j': 0x24, 'k': 0x25, 'l': 0x26,
    'm': 0x32, 'n': 0x31, 'o': 0x18, 'p': 0x19, 'q': 0x10, 'r': 0x13,
    's': 0x1F, 't': 0x14, 'u': 0x16, 'v': 0x2F, 'w': 0x11, 'x': 0x2D,
    'y': 0x15, 'z': 0x2C,

    # 数字（主键盘）
    '0': 0x0B, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05,
    '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A,

    # 功能键
    'f1': 0x3B, 'f2': 0x3C, 'f3': 0x3D, 'f4': 0x3E,
    'f5': 0x3F, 'f6': 0x40, 'f7': 0x41, 'f8': 0x42,
    'f9': 0x43, 'f10': 0x44, 'f11': 0x57, 'f12': 0x58,

    # 控制键
    'esc': 0x01, 'tab': 0x0F, 'capslock': 0x3A,
    'shift': 0x2A, 'ctrl': 0x1D, 'alt': 0x38,
    'space': 0x39, 'enter': 0x1C, 'backspace': 0x0E,

    # 符号键
    '-': 0x0C, '=': 0x0D, '[': 0x1A, ']': 0x1B,
    '\\': 0x2B, ';': 0x27, "'": 0x28, ',': 0x33,
    '.': 0x34, '/': 0x35, '`': 0x29,

    # 导航键
    'insert': 0x52, 'delete': 0x53,
    'home': 0x47, 'end': 0x4F,
    'pageup': 0x49, 'pagedown': 0x51,

    # 箭头
    'up': 0x48, 'down': 0x50,
    'left': 0x4B, 'right': 0x4D,

    # 小键盘（注意需加 NumLock 才能正确使用）
    'num0': 0x52, 'num1': 0x4F, 'num2': 0x50, 'num3': 0x51,
    'num4': 0x4B, 'num5': 0x4C, 'num6': 0x4D,
    'num7': 0x47, 'num8': 0x48, 'num9': 0x49,
    'num.': 0x53, 'num+': 0x4E, 'num-': 0x4A, 'num*': 0x37, 'num/': 0x35
}


# =========================== 类封装接口 ===========================
class MarbotAutoGUI:
    def __init__(self):
        pass
    
    def click(self, x: int = None, y: int = None, wait_time: float = 0.0):
        if x is None or y is None:
            auto.Click(waitTime=wait_time)
        else:
            auto.Click(x, y, waitTime=wait_time)

    def rightClick(self, x: int = None, y: int = None, wait_time: float = 0.0):
        if x is None or y is None:
            auto.RightClick(waitTime=wait_time)
        else:
            auto.RightClick(x, y, waitTime=wait_time)
            
    def middleClick(self, x: int = None, y: int = None, wait_time: float = 0.0):
        if x is None or y is None:
            auto.MiddleClick(waitTime=wait_time)
        else:
            auto.MiddleClick(x, y, waitTime=wait_time)

    def doubleClick(self, x: int = None, y: int = None, wait_time: float = 0.0):
        if x is None or y is None:
            auto.DoubleClick(waitTime=wait_time)
        else:
            auto.DoubleClick(x, y, waitTime=wait_time)

    def moveTo(self, x: int, y: int, duration: float = 0.0, wait_time: float = 0.0):
        auto.MoveTo(x, y, duration, waitTime=wait_time)
        
    def mouseDown(self, x: int = None, y: int = None, button: str = 'left'):
        if x is None or y is None:
            x, y = self.position()
        auto.MouseDown(x, y, auto.MouseButton.Left if button == 'left' else auto.MouseButton.Right)

    def mouseUp(self, x: int = None, y: int = None, button: str = 'left'):
        if x is None or y is None:
            x, y = self.position()
        auto.MouseUp(x, y, auto.MouseButton.Left if button == 'left' else auto.MouseButton.Right)
        
    def position(self):
        return auto.GetCursorPos()
        
    def dragTo(self, x: int, y: int, duration: float = 0.0):
        x1, y1 = self.position()
        auto.DragDrop(x1, y1, x, y, duration=duration)

    def scroll(self, clicks: int, x: int = None, y: int = None):
        if clicks < 0:
            auto.WheelDown(wheelTimes=abs(clicks), waitTime=0)
        else:
            auto.WheelUp(wheelTimes=clicks, waitTime=0)



if __name__ == "__main__":
    # 实例化你的类
    bot = MarbotAutoGUI()

    # 等待你切到目标窗口
    print("⌛ Waiting 10 seconds...")
    sleep(5)

    print("🚀 Start action sequence")

    # 设置目标位置
    target_x = 3061
    target_y = 666

    # 按住 Alt 键
    bot.keyDown('alt')
    sleep(1)

    # 移动到目标并点击（内部自动包含微调）
    bot.click(x=target_x, y=target_y, duration=2.0)

    sleep(1)
    # 松开 Alt 键
    bot.keyUp('alt')

    print("✅ Done")