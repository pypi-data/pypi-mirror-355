# bshot

Python package to take screenshots of windows that are in background

## Installation

You can install the package via pip:

```
pip install bshot
```

## Usage

```python
import cv2
import win32gui

from bshot.screenshot import get_image

hwnd = win32gui.FindWindow(None, "Untitled - Notepad")
img = get_image(hwnd, method="srccopy") # windll and srccopy methods
cv2.namedWindow("bshot", cv2.WINDOW_NORMAL)
cv2.imshow("bshot", img)
cv2.waitKey(0)
```

## Benchmark

The speed of the capture depends on the size of the window that is being captured.
It can caputre 220x160 window with 2400+ fps.

```python
import time

import win32gui

from bshot.screenshot import get_image

hwnd = win32gui.FindWindow(None, "Untitled - Notepad")

start = time.time()
count = 0
while time.time() - start < 1:
    get_image(hwnd, method="srccopy")
    count += 1
print("fps =", count)
```

## Limitations

- The screenshot module uses GetClientRect which can crop some portion of the window contents.

## License

This project is licensed under the terms of the MIT license.
