import os
import requests
from urllib.parse import urlparse
from PIL import Image


def save_and_copy_image(url, image_path):
    response = requests.get(url)
    image_file = os.path.join(image_path +  os.path.basename(urlparse(url).path))
    with open(image_file, 'wb') as f:
        f.write(response.content)
    show_image(image_file)


def show_image(image):
    img = Image.open(image)
    img.show()