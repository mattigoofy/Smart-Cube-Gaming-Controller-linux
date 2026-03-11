import subprocess
import time


def launch_chromium(url: str) -> subprocess.Popen:
    process = subprocess.Popen(
        [
            "/snap/bin/chromium",
            "--enable-features=WebBluetooth",
            "--user-data-dir=/tmp/chrome-debug",
            url,
        ]
    )
    time.sleep(2)
    return process
