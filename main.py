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

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from python_utils.bind_reader import upload_binds
from python_utils.directinput import CHAR_MAP, press_key, release_key


# Start webserver
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "HTML-JS"))
server = http.server.HTTPServer(
    ("localhost", 8765), http.server.SimpleHTTPRequestHandler
)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


# Launch Chromium
chromium_process = subprocess.Popen([
    "/snap/bin/chromium",
    "--remote-debugging-port=9222",
    "--user-data-dir=/tmp/chrome-debug",
    "--enable-features=WebBluetooth",
    "http://localhost:8765/index.html"
])

time.sleep(2)


options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
driver = webdriver.Chrome(
    options=options, service=Service("/snap/bin/chromium.chromedriver")
)

print(driver.title)
print(driver.current_url)



binds, constants = upload_binds()
move_history = []
last_move_time = time.time()

def execute_combo(keys_list):
    for combo in keys_list:
        # Delay step: e.g. ['1.0s']
        if len(combo) == 1 and combo[0].endswith("s"):
            try:
                time.sleep(float(combo[0][:-1]))
                continue
            except ValueError:
                pass
        # Key combo: press all together, then release
        keys = [CHAR_MAP[k] for k in combo if k in CHAR_MAP]
        for k in keys:
            press_key(k)
        time.sleep(0.05)
        for k in reversed(keys):
            release_key(k)


def find_match(history):
    best, best_len = None, 0

    for formula in binds:
        n = len(formula)
        if n <= len(history) and tuple(history[-n:]) == formula and n > best_len:
            best, best_len = formula, n

    return best


try: 
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
                print(match)
                if match:
                    execute_combo(binds[match])
                    if constants["delete_mode"] == "flush":
                        move_history.clear()
                    elif constants["delete_mode"] == "postfix":
                        del move_history[-len(match) :]
                    # 'keep': leave history unchanged
            except Exception:
                pass

finally:
    driver.quit()
    chromium_process.terminate()