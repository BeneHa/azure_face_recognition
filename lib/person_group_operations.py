import sys
import os
import time

from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, SnapshotObjectType, OperationStatusType
import azure.cognitiveservices.vision.face.models as azure_face_models

from lib.image_operations import resize_image

def add_images_to_person_group(face_client: FaceClient, person_group_id: str, input_path: str, resize_path: str) -> None:
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
        current_person_group = face_client.person_group_person.create(person_group_id, person_name)
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
                    face_client.person_group_person.add_face_from_stream(person_group_id, current_person_group.person_id, im)
                except azure_face_models.APIErrorException as e:
                    print("API error for person " + person_name + " for image " + image_name)
                    print(e)
            time.sleep(3)


def train_person_group(face_client: FaceClient, person_group_id: str) -> None:
    """When enough pictures are sent to Azure for a person group, this methods triggers the training and prints the status

    Args:
        person_group_id (str): the person group
    """
    face_client.person_group.train(person_group_id)

    # Print information on status
    while (True):
        training_status = face_client.person_group.get_training_status(person_group_id)
        print("Training status: {}.".format(training_status.status))
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            sys.exit('Training the person group has failed.')
        time.sleep(2)