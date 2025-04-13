r"""
This program creates an icon in the system tray to remind the user to make visual break to try to slow down myopia.

MIT License

Copyright (c) 2025 Fastattack

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE


The program needs the following registry keys to save parameters:
- "HKEY_CURRENT_USER\Software\APY!\AntiMyopia" : "Language" (REG_SZ)
- "HKEY_CURRENT_USER\Software\APY!\AntiMyopia" : "Auto-start" (REG_BINARY)
- "HKEY_CURRENT_USER\Software\APY!\AntiMyopia" : "Reminder-time" (REG_BINARY)

The program accepts the following command line arguments:
- "force-start" : starts the program even if auto_start is deactivated
- "auto-start" : used by the shortcuts to indicate that the program should take into account the auto-start value for this launch
"""


import time
import pystray
from PIL import Image
import sys
import os
import threading
import subprocess
import winreg


language = {
    "en": [
        "minutes left before the next reminder",
        "Reminders are deactivated for now",
        "Visual break!",
        "Time left",
        "Pause the reminders",
        "Settings",
        "Automatic start",
        "Reminders time",
        "10min",
        "20min",
        "30min",
        "45min",
        "1h",
        "2h",
        "Language",
        "English",
        "Français",
        "Stop",
        "AntiMyopia"
    ],
    "fr": [
        "minutes restantes avant le prochain rappel",
        "Les rappels sont désactivés pour le moment",
        "Pause visuelle !",
        "Temps restant",
        "Mettre en pause les rappels",
        "Paramètres",
        "Démarrage automatique",
        "Temps des rappels",
        "10min",
        "20min",
        "30min",
        "45min",
        "1h",
        "2h",
        "Langue",
        "English",
        "Français",
        "Stop",
        "AntiMyopie"
    ]
}

# default values
auto_start = True
selected_language = "en"
loop_running = False
reminder_time = 30
minutes_counter = 0


def create_registry_keys():
    """Creates the registry keys needed for saving information for the program

    :return: 0 if the keys could not be created, 1 if the keys are created or already exist
    """
    try:
        base_read_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_READ)
        base_write_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_WRITE)
    except FileNotFoundError:  # key does not exist
        try:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia")
            base_read_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_READ)
            base_write_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_WRITE)
        except:
            return 0
    try:
        winreg.QueryValueEx(base_read_key, "Language")
    except FileNotFoundError:  # value does not exist
        try:
            winreg.SetValueEx(base_write_key, "Language", 0, winreg.REG_SZ, "en")
        except:
            return 0
    try:
        winreg.QueryValueEx(base_read_key, "Auto-start")
    except FileNotFoundError:  # value does not exist
        try:
            winreg.SetValueEx(base_write_key, "Auto-start", 0, winreg.REG_BINARY, int.to_bytes(1))
        except:
            return 0
    try:
        winreg.QueryValueEx(base_read_key, "Reminder-time")
    except FileNotFoundError:  # value does not exist
        try:
            winreg.SetValueEx(base_write_key, "Reminder-time", 0, winreg.REG_BINARY, int.to_bytes(30))
        except:
            return 0
    return 1


def read_registry_values(create_keys_if_needed=True):
    """Reads the registry values and set the values for selected_language, auto_start and reminder_time

    :param create_keys_if_needed: if set to True and if the Language value in the registry is "UNSET", will create any missing registry keys
    """
    global auto_start, selected_language, reminder_time
    # Language
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia")
        value = winreg.QueryValueEx(key, "Language")[0]
        winreg.CloseKey(key)
    except:
        pass
    else:
        if type(value) is str:
            if value == "UNSET":
                if create_keys_if_needed:
                    create_registry_keys()
                    read_registry_values(False)
            elif value == "en" or value == "fr":
                selected_language = value
    # Auto-start
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia")
        value = winreg.QueryValueEx(key, "Auto-start")[0]
        winreg.CloseKey(key)
    except:
        pass
    else:
        if type(value) is bytes:
            value = int.from_bytes(value)
            if value == 0 or value == 1:
                auto_start = bool(value)
    # Reminder-time
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia")
        value = winreg.QueryValueEx(key, "Reminder-time")[0]
        winreg.CloseKey(key)
    except:
        pass
    else:
        if type(value) is bytes:
            value = int.from_bytes(value)
            reminder_time = value


def write_registry_values():
    """ Sets the values of selected_language, auto_start and reminder_time to the registry """
    # Language
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Language", 0, winreg.REG_SZ, selected_language)
        winreg.CloseKey(key)
    except:
        pass
    # Auto-start
    try:
        value = int.to_bytes(int(auto_start))
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Auto-start", 0, winreg.REG_BINARY, value)
        winreg.CloseKey(key)
    except:
        pass
    # Reminder-time
    try:
        value = int.to_bytes(reminder_time)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\APY!\AntiMyopia", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Reminder-time", 0, winreg.REG_BINARY, value)
        winreg.CloseKey(key)
    except:
        pass


def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev (.py) and for PyInstaller (.exe) """
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def on_clicked_info():
    if loop_running:
        icon.notify(" ", f"{reminder_time - minutes_counter} {language[selected_language][0]}")
        time.sleep(3)
        icon.remove_notification()
    else:
        icon.notify(" ", language[selected_language][1])


def on_clicked_close():
    global loop_running
    icon.stop()
    loop_running = False


def on_clicked_break():
    global loop_running
    if loop_running:
        loop_running = False
    else:
        loop()


def on_clicked_auto_start():
    global auto_start
    auto_start = not auto_start
    write_registry_values()


def on_click_time_definition(new_reminder_time: int):
    global reminder_time
    reminder_time = new_reminder_time
    write_registry_values()
    check_time()


def on_click_language(lang: str):
    global selected_language, loop_running
    if lang in ["en", "fr"]:
        selected_language = lang
        write_registry_values()
        icon.stop()
        loop_running = False
        if getattr(sys, 'frozen', False):  # in .exe form
            subprocess.Popen([sys.executable, "force-start"])
        else:  # in .py form
            subprocess.Popen([sys.executable, os.path.abspath(__file__), "force-start"])


def check_time():
    global minutes_counter
    if minutes_counter >= reminder_time:
        minutes_counter = 0
        icon.notify(language[selected_language][2])


def _loop():
    global minutes_counter, loop_running
    loop_running = True
    seconds_counter = 0
    minutes_counter = 0
    while loop_running:
        time.sleep(1)
        seconds_counter += 1
        if seconds_counter >= 60:
            seconds_counter = 0
            minutes_counter += 1
            check_time()


def loop():
    threading.Thread(target=_loop).start()


# start the program
read_registry_values()

if "auto-start" not in sys.argv or (auto_start and "auto-start" in sys.argv) or "force-start" in sys.argv:
    image = Image.open(get_resource_path("eye-care.png"))
    icon = pystray.Icon(language[selected_language][18], image, title=language[selected_language][18], menu=pystray.Menu(pystray.MenuItem(language[selected_language][3], on_clicked_info),
                                                                                   pystray.MenuItem(language[selected_language][4], on_clicked_break, checked=lambda item: not loop_running),
                                                                                   pystray.MenuItem(language[selected_language][5], pystray.Menu(
                                                                                       pystray.MenuItem(language[selected_language][6], on_clicked_auto_start, checked=lambda item: auto_start),
                                                                                       pystray.MenuItem(language[selected_language][7], pystray.Menu(
                                                                                           pystray.MenuItem(language[selected_language][8], lambda item: on_click_time_definition(10), checked=lambda item: True if reminder_time == 10 else False),
                                                                                           pystray.MenuItem(language[selected_language][9], lambda item: on_click_time_definition(20), checked=lambda item: True if reminder_time == 20 else False),
                                                                                           pystray.MenuItem(language[selected_language][10], lambda item: on_click_time_definition(30), checked=lambda item: True if reminder_time == 30 else False),
                                                                                           pystray.MenuItem(language[selected_language][11], lambda item: on_click_time_definition(45), checked=lambda item: True if reminder_time == 45 else False),
                                                                                           pystray.MenuItem(language[selected_language][12], lambda item: on_click_time_definition(60), checked=lambda item: True if reminder_time == 60 else False),
                                                                                           pystray.MenuItem(language[selected_language][13], lambda item: on_click_time_definition(120), checked=lambda item: True if reminder_time == 120 else False),
                                                                                       )),
                                                                                       pystray.MenuItem(language[selected_language][14], pystray.Menu(
                                                                                           pystray.MenuItem(language[selected_language][15], lambda item: on_click_language("en"), checked=lambda item: True if selected_language == "en" else False),
                                                                                           pystray.MenuItem(language[selected_language][16], lambda item: on_click_language("fr"), checked=lambda item: True if selected_language == "fr" else False),
                                                                                       )),
                                                                                   )),
                                                                                   pystray.MenuItem(language[selected_language][17], on_clicked_close)
                                                                                   ))
    loop()
    icon.run()
