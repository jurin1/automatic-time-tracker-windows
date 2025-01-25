import psutil
import win32gui
import win32process
import re
from datetime import datetime
import time
import ctypes
from ctypes import wintypes
import comtypes
from comtypes import client
from comtypes.GUID import GUID


def get_active_window_info():
    """
    Ruft Informationen über das aktive Fenster ab.
    """
    try:
        if psutil.WINDOWS:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()
                executable_path = process.exe()
                return {'title': title, 'process_name': process_name, 'executable_path': executable_path, 'hwnd': hwnd}
        elif psutil.MACOS:
            import subprocess
            script = 'tell application "System Events" to get the name of the first process whose frontmost is true'
            process_name = subprocess.check_output(
                ['osascript', '-e', script]).decode('utf-8').strip()
            # Get the path of the application on macOS (implementation needed)
            executable_path = None  # Needs implementation for macOS
            return {'title': process_name, 'process_name': process_name, 'executable_path': executable_path}
        else:
            return {'title': "Unsupported OS", 'process_name': "Unsupported OS", 'executable_path': None}
    except Exception as e:
        print(f"Error getting active window info: {e}")
        return None


def get_active_window_name():
    """
    Gibt den Namen des aktiven Fensters basierend auf den verfügbaren Informationen zurück.
    """
    window_info = get_active_window_info()
    if window_info:
        if window_info['title']:
            return window_info['title']
        elif window_info['process_name']:
            return window_info['process_name']
        elif window_info['executable_path']:
            return window_info['executable_path']
        else:
            return "Unbekannte Anwendung"
    else:
        return "Kein aktives Fenster"


def is_video_url(url):
    """
        Prüft, ob eine URL auf eine Video-Seite verweist.
    """
    if url is None:
        return False
    video_patterns = [
        r"youtube\.com/watch",
        r"vimeo\.com/",
        r"netflix\.com/",
        r"twitch\.tv/",
        r"dailymotion\.com/",
        r"wistia\.com/",
        r"youtube\.com/embed/",
        r"player\.vimeo\.com/video/"
    ]
    for pattern in video_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def is_video_process(process_name, hwnd, title):
    """
    Prüft, ob der Prozessname auf eine Videoanwendung hindeutet.
    """
    video_process_patterns = [
        r"vlc",
        r"mpv",
        r"wmplayer",
        r"potplayer"
    ]
    for pattern in video_process_patterns:
        if re.search(pattern, process_name, re.IGNORECASE):
            return True

    # Browser spezifische Erkennung (nicht perfekt)
    browser_process_patterns = [
        r"chrome",
        r"firefox",
        r"edge",
        r"brave"
    ]

    for pattern in browser_process_patterns:
        if re.search(pattern, process_name, re.IGNORECASE) and is_video_url(title):
            return True
    return False


def is_tab_playing_audio(element, automation):
        try:
            # Get the tabs
            tabs = element.FindAll(
                0,
                automation.CreatePropertyCondition(
                    IUIAutomation.UIA_ControlTypePropertyId,
                    IUIAutomation.UIA_TabItemControlTypeId,
                )
            )
            if not tabs:
                return False

            # Loop to find a tab with speaker
            for tab in tabs:
                try:
                    tab_name = tab.GetCurrentPropertyValue(
                        IUIAutomation.UIA_NamePropertyId)
                    if "Lautsprecher" in tab_name:
                        return tab_name
                except Exception as e:
                    print(f"Error getting tab name: {e}")
        except Exception as e:
            print(f"Error checking Tab: {e}")
        return None


def is_chrome_tab_playing_audio(hwnd, process_name):
    """
    Überprüft, ob ein Audio-Symbol in einem Chrome Tab ist.
    """
    try:
        if not "chrome" in process_name.lower():
            return False

         # IAccessible interface from UIAutomation
        IUIAutomation = client.GetModule(
            ("UIAutomationCore",
             GUID("{ff48dba1-60ef-41d7-a0b8-0a7787d22f50}"),
             0, 1, "IUIAutomation")
        )
        automation = client.CreateObject(IUIAutomation.IUIAutomation)

        # Get window object
        element = automation.ElementFromHandle(wintypes.HWND(hwnd))

        if not element:
            print(f"Error: Could not get element from HWND: {hwnd}")
            return False

        # Get the main window, not tab
        browser_window = element.FindAll(
            0,
            automation.CreatePropertyCondition(
                IUIAutomation.UIA_ControlTypePropertyId,
                IUIAutomation.UIA_WindowControlTypeId,
            )
        )

        if not browser_window:
            return False

        for window in browser_window:
            tab_name = is_tab_playing_audio(window, automation)
            if tab_name:
                return tab_name

    except Exception as e:
        print(f"Error checking chrome tabs: {e}")
    return False


def is_video_active_url(title, process_name, hwnd):
    """
    Gibt zurück, ob ein video gerade aktiv ist
    """
    if not title or not process_name or not hwnd:
        return False

    if is_video_process(process_name, hwnd, title):
        return True

    if is_video_url(title):
        return True

    if "chrome" in process_name.lower():
        tab_name = is_chrome_tab_playing_audio(hwnd, process_name)
        if tab_name:
           return tab_name

    return False
