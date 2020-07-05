import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, ImageDraw, ExifTags
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, SnapshotObjectType, OperationStatusType
import azure.cognitiveservices.vision.face.models as azure_face_models
import shutil

from typing import List, Optional, Tuple
from azure.cognitiveservices.vision.face.models import Person

from lib.image_operations import resize_image


def add_images_to_person_group(input_path: str, resize_path: str, person_group_id: str) -> None:
    """Go through a folder where training images for different persons are located.
    Resize the images and add them to a person group in Azure.

    Structure for input path:
    input_path
    - name person 1
    - name person 2
        - image 1
        - image 2

    Args:
        input_path (str): Path where the input images are located, structure above
        resize_path (str): [description]
        person_group_id (str): [description]
    """
    #Send images of each person to the service
    for person_name in os.listdir(input_path):
        print(f"\nProcessing images for {person_name}\n")
        current_person_group = face_client.person_group_person.create(PERSON_GROUP_ID, person_name)
        current_path = input_path + person_name
        images_current_person = [current_path + "/" + f for f in os.listdir(current_path)]
        time.sleep(3)

        #Create the folder to put the resized images if it does not exist
        resized_path = resize_path + person_name
        if not os.path.exists(resized_path):
            os.mkdir(resized_path)

        #Go through images for a person, resize them and send to API
        for image in images_current_person:
            image_name = os.path.basename(image)
            target_path = resized_path + "/" + image_name
            
            resize_image(image, target_path, (2000,2000))

            with open(target_path, "r+b") as im:
                try:
                    face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, current_person_group.person_id, im)
                except azure_face_models.APIErrorException as e:
                    print("API error for person " + person_name + " for image " + image_name)
                    print(e)
            time.sleep(3)


def train_person_group(person_group_id: str) -> None:
    """When enough pictures are sent to Azure for a person group, this methods triggers the training and prints the status

    Args:
        person_group_id (str): the person group
    """
    face_client.person_group.train(PERSON_GROUP_ID)

    # Print information on status
    while (True):
        training_status = face_client.person_group.get_training_status(PERSON_GROUP_ID)
        print("Training status: {}.".format(training_status.status))
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            sys.exit('Training the person group has failed.')
        time.sleep(2)

#Return a list of face IDs for an image
def extract_faces_from_image(face_client: FaceClient, path: str) -> Tuple:
    """Takes one image and lets Azure find the faces in the image.
    No identification is done here, the face IDs are specific to this one image

    Args:
        face_client (face_client): The client object for the Azure Face API
        path (str): Path of one image

    Returns:
        List[str]: List of face IDs. These can then be matched against e.g. a person group
    """
    image = open(path, "r+b")
    face_ids = []
    faces = face_client.face.detect_with_stream(image)
    for face in faces:
        face_ids.append(face.face_id)
    return face_ids, faces


#Resolve a list of face IDs to the actual persons
def resolve_face_ids(face_client: FaceClient, face_ids: List[str], person_group_id: str) -> Optional[List[Person]]:
    """For a list of face IDs, let Azure check if there are matches in a person group

    Args:
        face_client (FaceClient): The azure face client
        face_ids (List[str]): List of face IDs
        person_group_id (str): name of the person group

    Returns:
        Optional[List[Person]]: If there were matches, return a list of Person objects.
        Will fail if there are no matches or more than 10 faces in the image
    """
    try:
        results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
        return results
    except Exception as e:
        print(f"Error when resolving faces for {image_basename}: {e}")
        time.sleep(3)


def cleanup_images(path_list: List[str]) -> List[str]:
    """Take a list of paths. Delete all files that are movies

    Args:
        path_list (List[str]): Full list of paths including movies

    Returns:
        List[str]: List of paths that are left over
    """
    items_no_valid_ending = [f for f in path_list if any(e in f for e in [".mp4", ".MP4", ".mov", ".MOV"])]
    for file in items_no_valid_ending:
        os.remove(file)
    return [f for f in path_list if f not in items_no_valid_ending]


# 
def getRectangle(faceDictionary: dict) -> Tuple:
    """Convert width height to a point in a rectangle in order to draw a rectangle around a found face

    Args:
        faceDictionary (dict): [description]

    Returns:
        Tuple: [description]
    """
    rect = faceDictionary.face_rectangle
    left = rect.left
    top = rect.top
    right = left + rect.width
    bottom = top + rect.height
    
    return ((left, top), (right, bottom))


#General settings
#TODO read from file
KEY = ""
ENDPOINT = ""

face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))


PERSON_GROUP_ID = "bhaeuse_face_group_4"


# Train the person group
# face_client.person_group.create(person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID)
# add_images_to_person_group(sys.path[0] + "/faces/original/", sys.path[0] + "/faces/input_resized/", PERSON_GROUP_ID)
# train_person_group(PERSON_GROUP_ID)


test_path = sys.path[0] + "/faces/test_images/"
output_path = sys.path[0] + "/faces/output/"



images_to_be_analyzed = [test_path + f for f in os.listdir(test_path)]
cleaned_images = cleanup_images(images_to_be_analyzed)


for test_image in cleaned_images:
    image_basename = os.path.basename(test_image)

    target_path = sys.path[0] + "/faces/test_images_resized/" + os.path.basename(test_image)

    resize_image(test_image, target_path, (2000,2000))
    face_ids, face_dicts = extract_faces_from_image(face_client, target_path)

    if len(face_ids) > 0:
        #At least one face was found in the image
        results = resolve_face_ids(face_client, face_ids, PERSON_GROUP_ID)

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
                recognized_person = face_client.person_group_person.get(PERSON_GROUP_ID, most_likely_candidate.person_id)
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
            img = Image.open(target_path)
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