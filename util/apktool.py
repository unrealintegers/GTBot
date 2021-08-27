import os
import json
import sys
import zipfile
import UnityPy

# pass name of zip as command line arg
zip_name = sys.argv[1]
with zipfile.ZipFile(zip_name) as z:
    apk_name = z.extract("com.kakaogames.gdts.apk")

env = UnityPy.load(apk_name)

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
        box = (x, y, x+dx, y+dy)
        portrait = image.crop(box)

        path = os.path.join("portraits", hero + ".png")
        portrait.save(path, "PNG")


# if not env.objects:
#     raise ValueError("Objects Not Found")

# # iterate over internal objects
# for obj in env.objects:
#     # process specific object types
#     if obj.type in ["Texture2D", "Sprite"]:
#         # parse the object data
#         data = obj.read()
#
#         # create destination path
#         dest = os.path.join("output", data.name)
#
#         # make sure that the extension is correct
#         # you probably only want to do so with images/textures
#         dest, ext = os.path.splitext(dest)
#         dest = dest + ".png"
#
#         try:
#             img = data.image
#             img.save(dest)
#         except (AttributeError, SystemError):
#             print(data.name)
