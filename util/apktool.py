import json
import os
from bs4 import BeautifulSoup
import cloudscraper
import shutil
import logging
import zipfile

import UnityPy

APKPURE_LINK = "https://apkpure.com/%EA%B0%80%EB%94%94%EC%96%B8-" \
               "%ED%85%8C%EC%9D%BC%EC%A6%88/com.kakaogames.gdtskr/download"

logging.root.setLevel(logging.INFO)

logging.info("Finding APK")
scraper = cloudscraper.create_scraper(interpreter='nodejs')
res = scraper.get(APKPURE_LINK).text
soup = BeautifulSoup(res, "html.parser").find('a', {'id': 'download_link'})
if not soup['href']:
    exit()

logging.info("Downloading APK")
with scraper.get(soup['href'], stream=True) as r:
    with open('gdts.xapk', 'wb') as f:
        shutil.copyfileobj(r.raw, f)

logging.info("Loading APK")

with zipfile.ZipFile("gdts.xapk") as z:
    apk_name = z.extract("com.kakaogames.gdtskr.apk")
env = UnityPy.load(apk_name)

# grab the 2 relevant portrait files
coord_raw = env.container['assets/spritesheets/story-portraits/portraits.json']
image_raw = env.container['assets/spritesheets/story-portraits/portraits.png']

# read these files for dict & image
coords = json.loads(coord_raw.read().m_Script.tobytes().decode('ascii'))
image = image_raw.read().image
image.show()

# make a new directory if needed
if not os.path.exists("portraits"):
    os.mkdir("portraits")

# iterate through each hero
for hero, value in coords['frames'].items():
    x, y, dx, dy = value['frame'].values()

    # we ignore some "dummy" sprites
    if dx > 20 and dy > 20:
        box = (x, y, x + dx, y + dy)
        portrait = image.crop(box)

        path = os.path.join("portraits", f"gtp_{hero}.png")
        portrait.save(path, "PNG")
