
from PIL import Image,ImageSequence
import glob as glob
import os

# For saving exported geotiffs as pngs

folder = r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\b1"

# loop through all files and save .tif as .png
for file in glob.glob(os.path.join(folder, "*.tif")):
    # Get the filename without the extension
    filename_ext = os.path.basename(file)
    filename = os.path.splitext(os.path.basename(file))[0]
    print(filename)
    try:
        im = Image.open(file)
        for i, page in enumerate(ImageSequence.Iterator(im)):
            path = r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\b1\\" + filename + ".png"
            if not os.path.isfile(path):
                try:
                    page.resize((600,500))
                    page.save(path,"png",quality=100)
                except:
                    print(filename_ext)
    except:
        print(filename_ext)

# then move all tif files to a different folder or delete them
# mkdir tif
# find . -type f -iname "*.tif" -exec mv {} tif/ \;