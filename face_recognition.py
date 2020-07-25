import asyncio
import glob
import io
import os
import shutil
import sys
import time
import uuid
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import azure.cognitiveservices.vision.face.models as azure_face_models
import click
import requests
import yaml
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import (OperationStatusType,
                                                        Person,
                                                        SnapshotObjectType,
                                                        TrainingStatusType)
from azure.cognitiveservices.vision.face.models._models_py3 import \
    APIErrorException
from msrest.authentication import CognitiveServicesCredentials
from msrest.exceptions import ValidationError
from PIL import ExifTags, Image, ImageDraw

from lib.face_operations import (extract_faces_from_image, getRectangle,
                                 resolve_face_ids)
from lib.folder_operations import (create_necessary_folders,
                                   ensure_training_structure,
                                   extract_infos_from_yaml)
from lib.image_operations import cleanup_images, resize_image
from lib.person_group_operations import (add_images_to_person_group,
                                         train_person_group)


def classify_pictures(image_paths: List[str], face_client: FaceClient, person_group_id: str, output_path: str) -> None:
    for test_image in image_paths:
        image_basename = os.path.basename(test_image)
        target_path = sys.path[0] + "/faces/unclassified_resized/" + os.path.basename(test_image)

        resize_image(test_image, target_path, (2000,2000))
        face_ids, face_dicts = extract_faces_from_image(face_client, target_path)
        os.remove(target_path)

        if len(face_ids) > 0:
            #At least one face was found in the image
            results = resolve_face_ids(face_client, face_ids, person_group_id)

            #If the list of face ids could not be resolved, move the picture to error folder
            if not results:
                shutil.copyfile(test_image, f"{sys.path[0]}/faces/output/api_error/{image_basename}")
                os.remove(test_image)
                continue

            for person in results:
                #for everybody found, copy the file in a folder with his/her name
                if len(person.candidates) > 0:
                    most_likely_candidate = person.candidates[0]
                    
                    confidence = most_likely_candidate.confidence
                    recognized_person = face_client.person_group_person.get(person_group_id, most_likely_candidate.person_id)
                    recognized_name = recognized_person.name
                    print(f"Recognized {recognized_name} in image {image_basename}")

                    #Write to the output folder of this person
                    output_path_this_person = output_path + "/" + recognized_name
                    if not os.path.exists(output_path_this_person):
                        os.mkdir(output_path_this_person)
                    shutil.copyfile(test_image, output_path_this_person + "/" + image_basename)

            #Get information on faces that could not be recognized 
            faces_no_candidates = [p.face_id for p in results if len(p.candidates) == 0]
            face_dicts_no_candidates = [d for d in face_dicts if d.face_id in faces_no_candidates]
            
            #Save images with at least one person not recognized with a red rectangle around the face
            if len(face_dicts_no_candidates) > 0:
                img = Image.open(test_image)
                draw = ImageDraw.Draw(img)
                for face in face_dicts_no_candidates:
                    draw.rectangle(getRectangle(face), outline="red")
                img.save(sys.path[0] + "/faces/output/some faces not recognized/" + image_basename)
                print(f"{len(face_dicts_no_candidates)} faces not recognized in image {image_basename}")
            
            time.sleep(3)

        else:
            print(f"No face found in image {image_basename}")
            shutil.copyfile(test_image, sys.path[0] + "/faces/output/no face found/" + image_basename)
        
        #Remove the image so it will not be classified again in the next run
        os.remove(test_image)
        time.sleep(3)
    

def prepare_environment() -> FaceClient:
    yaml_path = sys.path[0] + "/config.yaml"
    secrets_dict = extract_infos_from_yaml(yaml_path, "secrets")
    KEY = secrets_dict["face_api_key"]
    ENDPOINT = secrets_dict["face_api_endpoint"]
    try:
        return FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
    except ValueError:
        click.echo("You need to provide an endpoint and API key in the config.yaml.")
        sys.exit()
    

def run_if_valid_credentials(func, *args):
    try:
        func(*args)

    except APIErrorException:
        click.echo("""API error. Either this person group already exists, or your credentials are invalid. Please try another name. If this error appears again,
                         please check your Microsoft Azure Face API endpoint and key in the config.yaml""")
        sys.exit()

    except ValidationError:
        click.echo("The person group name is invalid, please only use letters (no special characters like 'ä'), numbers and underscores")
        sys.exit()


@click.command()
@click.option("--task", prompt="Do you want to 'train' or 'classify'")
@click.option("--person_group_name", prompt="Name of the person group")
def main_script(task, person_group_name):
    """The main script which either takes the input images and trains a person group or uses a trained person group to classify images and sort the to the output folder.

    Args:
        task ([type]): [description]
        person_group_name ([type]): [description]
    """
    face_client = prepare_environment()
    create_necessary_folders()
    if task == "train":
        # Train the person group
        training_structure_result = ensure_training_structure()
        if training_structure_result is False:
            sys.exit()

        #Create the person group if the credentials are valid and the naming is allowed
        run_if_valid_credentials(face_client.person_group.create, person_group_name, person_group_name)
        
        add_images_to_person_group(face_client = face_client, person_group_id = person_group_name,
            input_path = sys.path[0] + "/faces/input/", resize_path = sys.path[0] + "/faces/input_resized/")
        train_person_group(face_client = face_client, person_group_id = person_group_name)
        click.echo(f"Training completed for person group {person_group_name}")

    elif task == "classify":
        # Classify images using an existing person group
        unclassified_path = sys.path[0] + "/faces/unclassified/"
        output_path = sys.path[0] + "/faces/output/"

        images_to_be_analyzed = glob.glob(unclassified_path + "**/*", recursive = True)
        cleaned_images = cleanup_images(images_to_be_analyzed)
        run_if_valid_credentials(classify_pictures, cleaned_images, face_client, person_group_name, output_path)
        click.echo("Classifying images completed.")
        
    else:
        click.echo("Please call the script with --task 'train' or 'classify' to tell me what to do.")

if __name__ == '__main__':
    main_script()
