# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 01:55:49 2020

@author: Mattigoofy
"""

import http.server
import os
import subprocess
import threading
import time

from evdev import ecodes as e
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from python_utils.bind_reader import upload_binds
from python_utils.directinput import CHAR_MAP, execute_combo, press_key, release_key

# Start webserver
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "HTML-JS"))
server = http.server.HTTPServer(
    ("localhost", 8765), http.server.SimpleHTTPRequestHandler
)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


# Launch Chromium
chromium_process = subprocess.Popen(
    [
        "/snap/bin/chromium",
        "--remote-debugging-port=9222",
        "--user-data-dir=/tmp/chrome-debug",
        "--enable-features=WebBluetooth",
        "http://localhost:8765/index.html",
    ]
)

time.sleep(2)


options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
driver = webdriver.Chrome(
    options=options, service=Service("/snap/bin/chromium.chromedriver")
)

print(driver.title)
print(driver.current_url)


OPTION = "BINDS"  # BINDS or CONSOLE


try:
    if OPTION == "BINDS":
        binds, constants = upload_binds()
        move_history = []
        last_move_time = time.time()

        def find_match(history):
            best, best_len = None, 0

            for formula in binds:
                n = len(formula)
                if (
                    n <= len(history)
                    and tuple(history[-n:]) == formula
                    and n > best_len
                ):
                    best, best_len = formula, n

            return best

        while True:
            for entry in driver.get_log("browser"):
                try:
                    entry = str(entry).split('"')[1].split(";")
                    move = entry[0].replace("\\", "")

                    now = time.time()
                    if now - last_move_time > constants["idle_time"]:
                        move_history.clear()
                    last_move_time = now

                    move_history.append(move)

                    match = find_match(move_history)
                    if match:
                        print(match)
                        execute_combo(binds[match])
                        if constants["delete_mode"] == "flush":
                            move_history.clear()
                        elif constants["delete_mode"] == "postfix":
                            del move_history[-len(match) :]
                        # 'keep': leave history unchanged
                except Exception:
                    pass

    elif OPTION == "CONSOLE":
        keyboard = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["a", "z", "e", "r", "t", "y", "u", "i", "o", "p"],
            ["q", "s", "d", "f", "g", "h", "j", "k", "l", "m"],
            ["w", "x", "c", "v", "b", "n", ",", ";", ":", "="],
        ]
        shiftlock = False
        idx = [1, 0]  # row column

        while True:
            for entry in driver.get_log("browser"):
                try:
                    entry = str(entry).split('"')[1].split(";")
                    move = entry[0].replace("\\", "")

                    if "R" in move:  # move up or down
                        idx[0] += -1 if "'" in move else 1  # move left if '
                        idx[0] %= sum(
                            1 for row in keyboard if idx[1] < len(row)
                        )  # catch overflows

                    if "U" in move:  # move left or right
                        idx[1] += -1 if "'" in move else 1  # move left if ''
                        idx[1] %= len(keyboard[idx[0]])  # catch overflows

                    if "L" in move:  # write or delete
                        if "'" in move:
                            key = CHAR_MAP["backspace"]
                            press_key(key)
                            release_key(key)
                        else:
                            if shiftlock:
                                press_key(CHAR_MAP["shift"])
                                press_key(CHAR_MAP[keyboard[idx[0]][idx[1]]])
                                release_key(CHAR_MAP["shift"])
                                release_key(CHAR_MAP[keyboard[idx[0]][idx[1]]])

                            else:
                                key = CHAR_MAP[keyboard[idx[0]][idx[1]]]
                                press_key(key)
                                release_key(key)

                    if "D" in move:  # space or shiftlock
                        if "'" in move:
                            key = CHAR_MAP["space"]
                            press_key(key)
                            release_key(key)
                        else:
                            shiftlock = not shiftlock

                    if "F" in move:  # key left or key right
                        if "'" in move:
                            key = CHAR_MAP["left arrow"]
                            press_key(key)
                            release_key(key)
                        else:
                            key = CHAR_MAP["right arrow"]
                            press_key(key)
                            release_key(key)

                    if "B" in move:  # key up or key down
                        if "'" in move:
                            key = CHAR_MAP["up arrow"]
                            press_key(key)
                            release_key(key)
                        else:
                            key = CHAR_MAP["down arrow"]
                            press_key(key)
                            release_key(key)

                    print("letter:", keyboard[idx[0]][idx[1]])

                except Exception as e:
                    print("ERROR:", e)
                    pass


finally:
    driver.quit()
    chromium_process.terminate()
