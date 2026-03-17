import os
import subprocess
import time


def launch_chromium(url: str) -> subprocess.Popen[bytes]:
    chromium_paths = [
        "/snap/bin/chromium",                                   # Snap
        "/var/lib/flatpak/exports/bin/org.chromium.Chromium",   # Flatpak (system)
        os.path.expanduser("~/.local/share/flatpak/exports/bin/org.chromium.Chromium"),  # Flatpak (user)
        "/var/lib/flatpak/exports/bin/com.google.Chrome",       # Flatpak Google Chrome (system)
        os.path.expanduser("~/.local/share/flatpak/exports/bin/com.google.Chrome"),  # Flatpak Google Chrome (user)
        "/run/current-system/sw/bin/chromium",                  # NixOS system
        os.path.expanduser("~/.nix-profile/bin/chromium"), # Nix user profile
        "/nix/var/nix/profiles/default/bin/chromium",           # Nix default profile
        "chromium",                                             # PATH fallback
        "chromium-browser",                                     # PATH fallback (Debian/Ubuntu)
        "google-chrome",                                        # Chrome fallback
    ]

    chromium_bin = next(
        (p for p in chromium_paths if os.path.isfile(p) or (not os.path.sep in p)),
        None,
    )

    if chromium_bin is None:
        raise FileNotFoundError("Could not find a Chromium or Chrome executable.")

    # Flatpak needs to be launched differently
    if "flatpak" in chromium_bin:
        if "google" in chromium_bin:
            app_name = "com.google.Chrome"
        else:
            app_name = "org.chromium.Chromium"
        cmd = [
            "flatpak", "run", app_name,
            "--enable-features=WebBluetooth",
            "--user-data-dir=/tmp/chrome-debug",
            url,
        ]
    else:
        cmd = [
            chromium_bin,
            "--enable-features=WebBluetooth",
            "--user-data-dir=/tmp/chrome-debug",
            url,
        ]

    process = subprocess.Popen(cmd)
    time.sleep(2)
    return process


if __name__ == "__main__":
    # For testing
    launch_chromium("www.google.com")
