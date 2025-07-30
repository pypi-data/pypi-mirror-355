from ctypes import windll
from typing import Any
from typing import Literal
from typing import Optional

import numpy as np
import win32con
import win32gui
import win32ui
from numpy import dtype
from numpy import ndarray
from numpy import uint8

from bshot.exceptions import InvalidMethodException


def get_offset(hwnd: int) -> tuple[int, int]:
    x, y = win32gui.ClientToScreen(hwnd, (0, 0))
    x1, y1, _, _ = win32gui.GetWindowRect(hwnd)
    return x - x1, y - y1


def get_image_by_rect(
    hwnd: int,
    x: int,
    y: int,
    method: Literal["srccopy", "windll"] = "srccopy",
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> ndarray[Any, dtype[uint8]]:
    # if width/height is None, then use the size of the client area
    _, _, w, h = win32gui.GetClientRect(hwnd)
    if width is None:
        width = w
    if height is None:
        height = h

    # add offset to x, y to match the client area
    off_x, off_y = get_offset(hwnd)
    x += off_x
    y += off_y

    scaleFactor = windll.shcore.GetScaleFactorForDevice(0) / 100
    width = int(width * scaleFactor)
    height = int(height * scaleFactor)

    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()

    dataBitMap.CreateCompatibleBitmap(dcObj, width, height)  # type: ignore
    cDC.SelectObject(dataBitMap)  # type: ignore

    if method == "windll":
        # windll method
        windll.user32.PrintWindow(hwnd, cDC.GetSafeHdc(), 2)  # type: ignore
    elif method == "srccopy":
        # srccopy method
        cDC.BitBlt((0, 0), (width, height), dcObj, (x, y), win32con.SRCCOPY)  # type: ignore
    else:
        raise InvalidMethodException(f"Method {method} is not valid.")

    buffer = dataBitMap.GetBitmapBits(True)

    image = np.frombuffer(buffer, dtype=np.uint8)
    image = image.reshape(height, width, 4)
    # bitmap has 4 channels like: BGRA. Discard Alpha
    image = image[:, :, :3]

    win32gui.DeleteObject(dataBitMap.GetHandle())
    cDC.DeleteDC()
    dcObj.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)  # type: ignore

    # Now you have the image data in the NumPy array format
    return image


def get_image(
    hwnd: int, method: Literal["srccopy", "windll"] = "srccopy"
) -> ndarray[Any, dtype[uint8]]:
    return get_image_by_rect(hwnd, 0, 0, method)
