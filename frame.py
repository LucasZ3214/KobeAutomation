import os
import time
import cv2
import numpy as np
import pytesseract
import pyautogui
import ctypes
from typing import Optional, Tuple, List, Callable, Dict
from dataclasses import dataclass
import logging
from enum import Enum, auto

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'


@dataclass
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int


class FlowStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()
    USER_INTERVENTION_NEEDED = auto()
    RETRY = auto()


class ScreenAutomator:
    def __init__(self, pause: float = 0.2, fail_safe: bool = True):
        pyautogui.PAUSE = pause
        pyautogui.FAILSAFE = fail_safe
        self.user_choices: Dict[str, str] = {}
        self.image_dir = "images"

        pyautogui.MINIMUM_DURATION = 0.2


    def set_image_dir(self, directory: str):
        self.image_dir = directory
        if not os.path.exists(directory):
            logger.info(f"未找到目录")

    def capture_screen(self, region: Optional[ScreenRegion] = None) -> np.ndarray:
        if region:
            screenshot = pyautogui.screenshot(region=(region.x, region.y, region.width, region.height))
        else:
            screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_image(self, template_path: str, region: Optional[ScreenRegion] = None,
                   confidence: float = 0.9) -> Optional[Tuple[int, int]]:
        try:
            full_path = os.path.join(self.image_dir, template_path) if self.image_dir else template_path
            screen_img = self.capture_screen(region)
            template = cv2.imread(full_path, cv2.IMREAD_COLOR)

            if template is None:
                raise FileNotFoundError(f"无法加载模板图像: {full_path}")

            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                center_x = max_loc[0] + template.shape[1] // 2
                center_y = max_loc[1] + template.shape[0] // 2
                if region:
                    center_x += region.x
                    center_y += region.y
                return (center_x, center_y)
            return None

        except Exception as e:
            logger.error(f"图像识别失败: {str(e)}")
            return None

    def find_text(self, text: str, region: Optional[ScreenRegion] = None,
                  lang: str = 'eng') -> Optional[Tuple[int, int]]:
        screen_img = self.capture_screen(region)
        gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)

        data = pytesseract.image_to_data(gray, lang=lang, output_type=pytesseract.Output.DICT)

        for i, word in enumerate(data['text']):
            if text.lower() in word.lower():
                x = data['left'][i]
                y = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]

                center_x = x + width // 2
                center_y = y + height // 2

                if region:
                    center_x += region.x
                    center_y += region.y

                return (center_x, center_y)
        return None

    def wait_for_element(self, find_func: Callable, timeout: float = 10,
                         interval: float = 0.5, **kwargs) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = find_func(**kwargs)
            if result:
                return True
            time.sleep(interval)
        return False

    def click_element(self, find_func: Callable, **kwargs) -> bool:
        position = find_func(**kwargs)
        if position:
            pyautogui.moveTo(position[0], position[1], duration=0.1)
            time.sleep(0.2)
            MouseClick("left")
            time.sleep(0.5)
            return True
        return False

    def press_keys(self, keys: [str, List[str]], presses: int = 1, interval: float = 0.1, **kwargs):
        """
        模拟键盘按键操作
        :param keys: 单个键名(str)或组合键列表(List[str])
        :param presses: 按键次数
        :param interval: 按键间隔(秒)
        :param kwargs: 其他pyautogui.keyDown/keyUp参数
        """
        try:
            if isinstance(keys, str):
                keys = [keys]

            logger.info(f"准备按下按键: {keys} {presses}次")

            for _ in range(presses):
                for key in keys:
                    pyautogui.keyDown(key, **kwargs)
                    time.sleep(0.1)

                if presses > 1:
                    time.sleep(interval)

            return True
        except Exception as e:
            logger.error(f"按键操作失败: {str(e)}")
            return False

    def hotkey(self, *args, **kwargs):
        try:
            logger.info(f"准备按下组合键: {args}")
            pyautogui.hotkey(*args, **kwargs)
            return True
        except Exception as e:
            logger.error(f"组合键操作失败: {str(e)}")
            return False

    def type_text(self, text: str, interval: float = 0.1, with_enter: bool = False):
        try:
            logger.info(f"准备输入文本: {text}")
            pyautogui.write(text, interval=interval)
            if with_enter:
                pyautogui.press('enter')
            return True
        except Exception as e:
            logger.error(f"文本输入失败: {str(e)}")
            return False

SendInput = ctypes.windll.user32.SendInput

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

MOUSE_LEFT_DOWN = 0x0002
MOUSE_LEFT_UP = 0x0004
MOUSE_RIGHT_DOWN = 0x0008
MOUSE_RIGHT_UP = 0x0010
MOUSE_MIDDLE_DOWN = 0x0020
MOUSE_MIDDLE_UP = 0x0040

def PressKey(hexKeyCode: int):
    """按下键盘按键"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode: int):
    """释放键盘按键"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def MouseClick(button: str = "left", x: Optional[int] = None, y: Optional[int] = None):

    if x is not None and y is not None:
        MoveMouse(x, y)

    if button.lower() == "left":
        MouseEvent(MOUSE_LEFT_DOWN)
        MouseEvent(MOUSE_LEFT_UP)
    elif button.lower() == "right":
        MouseEvent(MOUSE_RIGHT_DOWN)
        MouseEvent(MOUSE_RIGHT_UP)
    elif button.lower() == "middle":
        MouseEvent(MOUSE_MIDDLE_DOWN)
        MouseEvent(MOUSE_MIDDLE_UP)
    else:
        raise ValueError(f"不支持的鼠标按键: {button}")

def MouseDown(button: str = "left"):

    if button.lower() == "left":
        MouseEvent(MOUSE_LEFT_DOWN)
    elif button.lower() == "right":
        MouseEvent(MOUSE_RIGHT_DOWN)
    elif button.lower() == "middle":
        MouseEvent(MOUSE_MIDDLE_DOWN)
    else:
        raise ValueError(f"不支持的鼠标按键: {button}")

def MouseUp(button: str = "left"):
    """释放鼠标按键"""
    if button.lower() == "left":
        MouseEvent(MOUSE_LEFT_UP)
    elif button.lower() == "right":
        MouseEvent(MOUSE_RIGHT_UP)
    elif button.lower() == "middle":
        MouseEvent(MOUSE_MIDDLE_UP)
    else:
        raise ValueError(f"不支持的鼠标按键: {button}")

def MouseEvent(dwFlags: int, dx: int = 0, dy: int = 0, dwData: int = 0):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(dx, dy, dwData, dwFlags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)  # 0表示鼠标输入
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def MoveMouse(x: int, y: int, relative: bool = False):
    """
    移动鼠标到指定位置
    :param x: X坐标
    :param y: Y坐标
    :param relative: 是否为相对移动
    """
    if relative:
        MouseEvent(0x0001, x, y)  # MOUSEEVENTF_MOVE
    else:
        # 转换为绝对坐标 (0-65535)
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        abs_x = int((x / screen_width) * 65535)
        abs_y = int((y / screen_height) * 65535)
        MouseEvent(0x8000 | 0x0001, abs_x, abs_y)  # MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE

def MouseScroll(direction: str = "up", clicks: int = 1):
    """
    模拟鼠标滚轮滚动
    :param direction: 滚动方向 (up/down)
    :param clicks: 滚动次数
    """
    if direction.lower() == "up":
        dwData = 120 * clicks
    elif direction.lower() == "down":
        dwData = -120 * clicks
    else:
        raise ValueError("方向必须是 'up' 或 'down'")

    MouseEvent(0x0800, dwData=dwData)  # MOUSEEVENTF_WHEEL