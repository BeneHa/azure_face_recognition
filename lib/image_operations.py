from PIL import Image
import os

def resize_image(source_path, target_path, resolution: tuple):
    """Resize an image and save it to the target path

    Args:
        source_path ([type]): [description]
        target_path ([type]): [description]
        resolution (tuple): [description]
    """
    
    image = Image.open(source_path)
    

    #Turn image if necessary
    e = image._getexif()
    if e is not None:
        exif = dict(e.items())
        #Probably only for iPhone?
        try:
            orientation = exif[274]
            if orientation == 3:   image = image.transpose(Image.ROTATE_180)
            elif orientation == 6: image = image.transpose(Image.ROTATE_270)
            elif orientation == 8: image = image.transpose(Image.ROTATE_90)
        except KeyError:
            print(f"No exif key 274 found in image {os.path.basename(source_path)}")

    image.thumbnail((resolution))
    image.save(target_path)