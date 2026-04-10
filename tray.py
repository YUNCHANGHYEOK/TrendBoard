import subprocess
import threading
import sys
import os
from PIL import Image, ImageDraw
import pystray

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
process = None


def create_icon(color):
    """색상으로 원형 아이콘 생성 (green=실행중, red=중지)"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=color)
    return img


def is_running():
    return process is not None and process.poll() is None


def start_server(icon, item):
    global process
    if is_running():
        return
    log_path = os.path.join(BASE_DIR, "trendboard.log")
    log_file = open(log_path, "a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "run.py")],
        cwd=BASE_DIR,
        stdout=log_file,
        stderr=log_file,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    icon.icon = create_icon("green")
    icon.title = "TrendBoard — 실행 중"


def stop_server(icon, item):
    global process
    if not is_running():
        return
    process.terminate()
    process.wait()
    process = None
    icon.icon = create_icon("red")
    icon.title = "TrendBoard — 중지됨"


def open_browser(icon, item):
    import webbrowser
    webbrowser.open("https://yunchannel.cloud")


def quit_app(icon, item):
    global process
    if is_running():
        process.terminate()
    icon.stop()


def main():
    global process

    # 시작 시 자동으로 서버 실행
    log_path = os.path.join(BASE_DIR, "trendboard.log")
    log_file = open(log_path, "a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "run.py")],
        cwd=BASE_DIR,
        stdout=log_file,
        stderr=log_file,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    icon_img = create_icon("green")

    menu = pystray.Menu(
        pystray.MenuItem("▶  시작", start_server),
        pystray.MenuItem("■  중지", stop_server),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🌐 사이트 열기", open_browser),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✕  종료", quit_app),
    )

    icon = pystray.Icon(
        name="TrendBoard",
        icon=icon_img,
        title="TrendBoard — 실행 중",
        menu=menu,
    )
    icon.run()


if __name__ == "__main__":
    main()
