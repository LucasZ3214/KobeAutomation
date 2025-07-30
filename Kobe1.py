import os
import re
import time
import pyautogui
import pytesseract
import pygetwindow as gw
from frame import ScreenAutomator, ScreenRegion, FlowStatus

def is_in_hanger():
    '''
    status = telemetry.get_wt_data("MISSION")
    return status['status']
    '''
    all_windows = gw.getAllWindows()

    try:
        for i, win in enumerate(all_windows):
            if win.title == "War Thunder":
                return True
        return False
    except Exception as e:
        print(f"未找到窗口: {e}")

def ready_status():
    if automator.find_image("ready.png"):
        return True
    else:
        return False

def activate_window(target_title):
    all_windows = gw.getAllWindows()

    for i, win in enumerate(all_windows):
        if target_title in win.title:
            target_window = all_windows[i]

    try:
        if target_window.isMinimized:
            target_window.restore()

        target_window.activate()

        time.sleep(0.5)

        print(f"已激活窗口: {target_window.title}")

        return target_window
    except Exception as e:
        print(f"激活窗口失败: {e}")

def parse_command(text):

    if "ready" in text:
        country_start = text.rfind("ready")+len("ready")
        country_end = country_start + 4
        mode_start = country_start + 4
        mode_end = text.rfind("end")

        country = text[country_start:country_end].strip()
        mode = text[mode_start:mode_end].strip()

        return country,mode
    return False

def get_command_qq(contact_name):

    target_window = activate_window(contact_name)

    left, top, width, height = target_window.left, target_window.top, target_window.width, target_window.height
    chat_area = (left, top, left+width, top+height)  # 调整坐标

    screenshot = pyautogui.screenshot(region=chat_area)
    #screenshot.save("chat.png")
    text = pytesseract.image_to_string(screenshot, lang='eng')
    if parse_command(text):
        return parse_command(text)
    else:
        return False

def prompt_qq(target:str, text: str):
        activate_window(target)
        automator.type_text(text,interval=0.01)
        automator.press_keys(["Enter"])
        time.sleep(0.1)
        activate_window("War Thunder")
        return None

def country_select_flow():

    if automator.find_image("readytemp.png"):
        if get_command_qq(user):
            cmd = get_command_qq(user)
            country = cmd[0]
            mode = cmd[1]

            activate_window("War Thunder")
            automator.click_element(automator.find_image, template_path="usa.png")
            country_image = f"{country}.png"
            automator.click_element(automator.find_image, template_path=country_image)
            automator.click_element(automator.find_image, template_path="air.png")
            automator.wait_for_element(automator.find_image, template_path="ground.png")
            mode = f"{mode}.png"
            automator.click_element(automator.find_image, template_path=mode)
            automator.wait_for_element(automator.find_image, template_path="ready.png")
            automator.click_element(automator.find_image, template_path="ready.png")
            return True
        else:
            prompt_qq(user, "No Valid Command Found")
            return False

    else:
        print("Not in Squad")
        return False

def gametime_idle():
    for i in range(600):
        print(600-i)
        time.sleep(1)
    while True:
        state = is_in_hanger()
        if state:
            return None
        time.sleep(10)

user = "神户"
active_window = gw.getActiveWindow()
active_window.minimize()

automator = ScreenAutomator(pause=0.3, fail_safe=True)
automator.set_image_dir("buttons")
activate_window("War Thunder")

while True:
    state = is_in_hanger()
    while state:
        if country_select_flow():
            prompt_qq(user,"Ready")
            print("Ready")
            time.sleep(20)
            break
        else:
            time.sleep(10)
    else:
        print("Not in Hanger")
        gametime_idle()