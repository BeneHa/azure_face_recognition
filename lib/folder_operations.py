import os
import sys
import yaml

from typing import Optional, Dict


def extract_infos_from_yaml(yaml_path: str, yaml_part: str) -> Optional[Dict]:
    """Reads a yaml at the specified path and returns the part of the file that is specified as a dict

    Args:
        yaml_path (str): location of the file
        yaml_part (str): Part of the yaml (at the highest level) that should be returned

    Returns:
        Dict: [description]
    """
    yaml_lines = open(yaml_path).readlines()
    yaml_string = "".join(yaml_lines)
    yaml_dict = yaml.safe_load(yaml_string)
    try:
        return yaml_dict[yaml_part]
    except KeyError:
        print(f"The specified part {yaml_part} could not be found in file {yaml_path}.")


def create_necessary_folders() -> None:
    """Creates the folder structure needed for the project
    """
    current_path = sys.path[0]
    faces_path = current_path + "/faces/"
    needed_folders = [faces_path + f for f in ["input", "output", "unclassified", "unclassified_resized",
                                    "input_resized", "output/no face found", "output/api_error", "output/some faces not recognized"]] + [faces_path]
    for f in needed_folders:
        if not os.path.exists(f):
            os.mkdir(f)

def ensure_training_structure() -> None:
    training_path = sys.path[0] + "/faces/input/"

    #Make sure all files in the training path are folders
    all_files_in_training_path = [training_path + f + "/" for f in os.listdir(training_path)]
    for f in all_files_in_training_path:
        if not os.path.isdir(f):
            print(f"In the training path, there should only be folders. {f} is not a folder.")
            return False

    #Make sure there is at least one folder
    if len(all_files_in_training_path) == 0:
        print("There are no files in the training path. Please create at least one folder with at least one image in it.")
        return False

    #Make sure there is at least one valid image in every folder
    for folder in all_files_in_training_path:
        training_images_this_folder = [folder + f for f in os.listdir(folder)]
        for im in training_images_this_folder:
            if os.path.isdir(im):
                print(f"In a training folder, there should only be images of that person. {im} is a folder.")
                return False
        if len(training_images_this_folder) == 0:
            print(f"Folder {folder} does not contain an image. Each folder of a person needs at least one image.")
            return False