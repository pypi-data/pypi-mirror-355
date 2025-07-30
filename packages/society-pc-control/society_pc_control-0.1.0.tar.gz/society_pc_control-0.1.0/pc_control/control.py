import pyautogui
import tempfile
import cv2
import numpy as np
from PIL import ImageDraw, Image

def draw_mouse_pointer(image):
    draw = ImageDraw.Draw(image)
    x, y = pyautogui.position()
    radius = 8
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill='red', outline='white', width=2)
    return image

def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot = draw_mouse_pointer(screenshot)
    img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    tmp_file = tempfile.mktemp(suffix=".jpg")
    cv2.imwrite(tmp_file, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    return tmp_file

def type_text_smart(text):
    pyautogui.write(text, interval=0.03)

def press_hotkey(*args):
    pyautogui.hotkey(*args)

def move_mouse(dx, dy, accelerated=False):
    step = 150 if accelerated else 50
    pyautogui.moveRel(dx * step, dy * step, duration=0.1)

def click_mouse(button='left'):
    pyautogui.click(button=button)

def scroll_mouse(amount):
    pyautogui.scroll(amount)
