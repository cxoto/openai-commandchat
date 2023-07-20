import os
import requests
from urllib.parse import urlparse
from PIL import Image

import time
import sys
import threading


class WaitingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            for i in range(4):
                sys.stdout.write('\r' + ' ' * 60 + '\r')  # 清空当前行
                sys.stdout.write('Waiting' + '.' * i + ' ' * (3 - i))
                sys.stdout.flush()
                time.sleep(0.5)

    def stop(self):
        self._stop_event.set()


def save_and_copy_image(url, image_path):
    response = requests.get(url)
    image_file = os.path.join(image_path, os.path.basename(urlparse(url).path))
    with open(image_file, 'wb') as f:
        f.write(response.content)
    print("image download path: " + image_file)
    show_image(image_file)


def show_image(image):
    img = Image.open(image)
    img.show()


waiting_thread = WaitingThread()


def waiting_start():
    waiting_thread.start()


def waiting_stop():
    waiting_thread.stop()
    waiting_thread.join()
    sys.stdout.write('\r' + ' ' * 60 + '\r')
    sys.stdout.flush()
