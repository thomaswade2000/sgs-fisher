import cv2
import numpy as np
import ctypes
from ctypes import wintypes
import pygetwindow as gw
import pydirectinput
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Windows API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

BI_RGB = 0
DIB_RGB_COLORS = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


WINDOW_TITLE = "雷电模拟器"
_threshold = 0.8
_current_window = None


def _get_window():
    global _current_window
    windows = gw.getWindowsWithTitle(WINDOW_TITLE)
    if windows:
        _current_window = windows[0]
    return _current_window


def imread_chinese(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)


def capture_screen():
    win = _get_window()
    if win is None:
        logger.error(f"未找到窗口: {WINDOW_TITLE}")
        return None
    
    hwnd = win._hWnd
    
    hwndDC = user32.GetDC(hwnd)
    mfcDC = gdi32.CreateCompatibleDC(hwndDC)
    saveDC = gdi32.CreateCompatibleDC(mfcDC)
    
    saveBitMap = gdi32.CreateCompatibleBitmap(hwndDC, win.width, win.height)
    gdi32.SelectObject(mfcDC, saveBitMap)
    
    user32.PrintWindow(hwnd, mfcDC, 0)
    
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = win.width
    bmi.bmiHeader.biHeight = -win.height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    
    buffer = ctypes.create_string_buffer(win.width * win.height * 4)
    
    gdi32.GetDIBits(
        mfcDC, saveBitMap, 0, win.height,
        buffer, ctypes.byref(bmi), DIB_RGB_COLORS
    )
    
    img_data = np.frombuffer(buffer, dtype=np.uint8)
    img_data = img_data.reshape((win.height, win.width, 4))
    img_bgr = cv2.cvtColor(img_data, cv2.COLOR_BGRA2BGR)
    
    gdi32.DeleteObject(saveBitMap)
    gdi32.DeleteDC(mfcDC)
    gdi32.DeleteDC(saveDC)
    user32.ReleaseDC(hwnd, hwndDC)
    
    return img_bgr


def find_template(template_path, threshold=None):
    if threshold is None:
        threshold = _threshold
    
    screen = capture_screen()
    if screen is None:
        return None
    
    template = imread_chinese(template_path)
    if template is None:
        logger.error(f"找不到模板: {template_path}")
        return None
    
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    
    matches = []
    h, w = template.shape[:2]
    for pt in zip(*locations[::-1]):
        matches.append((pt[0], pt[1], w, h))
    
    if not matches:
        return None
    
    return matches


def find_and_click(template_path, threshold=None, match_index=0):
    matches = find_template(template_path, threshold)
    if matches is None:
        return False
    
    if match_index >= len(matches):
        logger.warning(f"索引 {match_index} 超出范围，共{len(matches)}个匹配")
        return False
    
    win = _get_window()
    if win is None:
        return False
    
    x, y, w, h = matches[match_index]
    center_x = win.left + x + w // 2
    center_y = win.top + y + h // 2
    
    pydirectinput.click(center_x, center_y)
    logger.info(f"点击: ({center_x}, {center_y})")
    return True


def set_threshold(threshold):
    global _threshold
    _threshold = threshold


def get_window():
    return _get_window()
