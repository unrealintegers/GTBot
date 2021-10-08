import json
import os

import UnityPy

files = [f for f in os.listdir() if f.endswith('.apk')]

env = UnityPy.load(files[0])

# grab the 2 relevant portrait files
coord_raw = env.container['assets/spritesheets/story-portraits/portraits.json']
image_raw = env.container['assets/spritesheets/story-portraits/portraits.png']

# read these files for dict & image
coords = json.loads(coord_raw.read().m_Script.tobytes().decode('ascii'))
image = image_raw.read().image

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
