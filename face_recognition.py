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

from lib.image_operations import resize_image, cleanup_images
from lib.person_group_operations import train_person_group, add_images_to_person_group
from lib.face_operations import extract_faces_from_image, resolve_face_ids, getRectangle



#General settings
KEY = open(sys.path[0] + "/secret/face_api_key").readline()
ENDPOINT = open(sys.path[0] + "/secret/face_api_endpoint").readline()
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