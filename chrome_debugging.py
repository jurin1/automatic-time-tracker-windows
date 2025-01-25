from playwright.sync_api import sync_playwright
import re
import time


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


def get_chrome_tab_info():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:

            tabs = browser.contexts[0].pages
            for tab in tabs:
                tab_title = tab.title()
                tab_url = tab.url

                print(f"Tab Titel: {tab_title}")
                print(f"Tab URL: {tab_url}")
                if is_video_url(tab_url):
                    print(f"Tab spielt Video")

                is_playing = tab.evaluate(
                    """() => {
                    try {
                        return Array.from(document.querySelectorAll('video')).some(v => !v.paused && v.currentTime > 0);
                    } catch(e){
                        return false;
                    }
                }
            """
                )
                print(f"Tab spielt Audio: {is_playing}")
                print("-" * 40)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    while True:
        get_chrome_tab_info()
        time.sleep(1)
