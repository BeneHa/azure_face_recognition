from PIL import Image
from typing import List
import os

def resize_image(source_path, target_path, resolution: tuple) -> None:
    """Resize an image and save it to the target path. This only works for iPhone images at the moment as these save the rotation in exif key 274
    TODO: also turn non-iPhone images

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
        try:
            orientation = exif[274]
            if orientation == 3:   image = image.transpose(Image.ROTATE_180)
            elif orientation == 6: image = image.transpose(Image.ROTATE_270)
            elif orientation == 8: image = image.transpose(Image.ROTATE_90)
        except KeyError:
            print(f"No exif key 274 found in image {os.path.basename(source_path)}")

    image.thumbnail((resolution))
    image.save(target_path)


def cleanup_images(path_list: List[str]) -> List[str]:
    """Take a list of paths. Delete all files that are movies, remove folders or other things from the list

    Args:
        path_list (List[str]): Full list of paths including movies

    Returns:
        List[str]: List of paths that are left over
    """
    movies = [f for f in path_list if any(e in f for e in [".mp4", ".MP4", ".mov", ".MOV"])]
    folders = [f for f in path_list if os.path.isdir(f)]
    for file in movies:
        os.remove(file)

    paths_to_remove_from_orig_list = movies + folders
    return [f for f in path_list if f not in paths_to_remove_from_orig_list]