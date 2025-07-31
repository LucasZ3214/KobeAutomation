import time
import pyautogui
import pytesseract
import pygetwindow as gw
from frame import ScreenAutomator


def list_difference_set(list1, list2):
    return list(set(list1) - set(list2))

def is_in_hanger():
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
        automator.hotkey(['ctrl', 'a'])
        automator.press_keys(['backspace'], interval=0.01)
        automator.type_text(text,interval=0.01)
        time.sleep(0.2)
        automator.press_keys(['enter'],presses=2)
        time.sleep(0.5)
        activate_window("War Thunder")
        return None

def get_current_selected():
    activate_window("War Thunder")
    country = []
    mode = []
    tmode = ['air','ground']
    tcountry = ["usa", "rus", "ger", "gbr", "jpn", "chn", "ita", "fra", "swe", "isr"]
    if automator.find_image("usa.png"):
        country.append("usa")
    if automator.find_image("rus.png"):
        country.append("rus")
    if automator.find_image("ger.png"):
        country.append("ger")
    if automator.find_image("gbr.png"):
        country.append("gbr")
    if automator.find_image("jpn.png"):
        country.append("jpn")
    if automator.find_image("chn.png"):
        country.append("chn")
    if automator.find_image("ita.png"):
        country.append("ita")
    if automator.find_image("fra.png"):
        country.append("fra")
    if automator.find_image("swe.png"):
        country.append("swe")
    if automator.find_image("isr.png"):
        country.append("isr")
    if country == []:
        return False
    else:
        country = list_difference_set(tcountry,country)[0]
    if automator.find_image("air.png"):
        mode.append('air')
    if automator.find_image("ground.png",confidence=1):
        mode.append('ground')
    mode = list_difference_set(tmode, mode)[0]
    print(country, mode)
    return country, mode

def country_select_flow():

    if automator.find_image("ready.png"):
        if get_command_qq(user):
            cmd = get_command_qq(user)
            country = cmd[0]
            mode = cmd[1]
            prompt_qq(user,country+','+mode)

            if not get_current_selected():
                print("Already Selected")
                mode = f"{mode}.png"
                automator.click_element(automator.find_image, template_path=mode)
                automator.wait_for_element(automator.find_image, template_path="ready.png")
                automator.click_element(automator.find_image, template_path="ready.png")
                return True

            else:
                activate_window("War Thunder")
                #automator.click_element(automator.find_image, template_path="usa.png")
                country_image = f"{country}.png"
                automator.click_element(automator.find_image, template_path=country_image)
                #automator.click_element(automator.find_image, template_path="air.png")
                #automator.wait_for_element(automator.find_image, template_path="ground.png")
                mode = f"{mode}.png"
                automator.click_element(automator.find_image, template_path=mode)
                automator.wait_for_element(automator.find_image, template_path="ready.png")
                automator.click_element(automator.find_image, template_path="ready.png")
                return True
        else:
            prompt_qq(user, "No Valid Command Found")
            return False

    else:
        print("Ready Not Possible")
        return False

def gametime_idle():
    for i in range(60):
        print(60-i)
        time.sleep(1)
    while True:
        state = is_in_hanger()
        if state:
            return None
        time.sleep(10)

def go_spectator():
    if automator.wait_for_element(automator.find_image, template_path="specmode.png",timeout=30):
        automator.click_element(automator.find_image, template_path="specmode.png")
        return True
    else:
        return False

def return_hanger():
    if automator.click_element(automator.find_image, template_path="tohanger.png"):
        return True
    else:
        return False

user = "LucasZ"
active_window = gw.getActiveWindow()
active_window.minimize()

automator = ScreenAutomator(pause=0.3, fail_safe=True)
automator.set_image_dir("buttons")
activate_window("War Thunder")

while True:
    state = is_in_hanger()
    while state:
        print("Not in Game")
        if return_hanger():
            print("Returning to Hanger")
            break
        if country_select_flow():
            prompt_qq(user,"OK")
            print("Ready")
            break
        else:
            print("Ready Already")
            break
    else:
        print("Not in Hanger")
        if go_spectator():
            print("Spectating")
            prompt_qq(user, "Spectating")
            break
        else:
            print("Failed to enter Spectator Mode")
            prompt_qq(user, "Failed to enter Spectator Mode")
        gametime_idle()