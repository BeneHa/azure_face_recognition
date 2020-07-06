import time



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
        results = face_client.face.identify(face_ids, person_group_id)
        return results
    except Exception as e:
        print(f"Error when resolving faces for {str(face_ids)}: {e}")
        time.sleep(3)