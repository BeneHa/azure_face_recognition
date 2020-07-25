# Azure Face Recognition

This is a small project to use the Azure Cognitive Services, in this case the Face API, for face recognition. I had thousands of pictures of the last 10 years and needed to find all with a specific person on them, so I created this wrapper around the Azure Face API.

## How it works

The Azure Face Recognition service takes some images of a person's face to learn the face characteristics (eye distance, face shape etc.). So you send some pictures of every person to the service and train a person group (an object holding information on multiple persons).

In the second step, the tool takes a new image and compares it to, lets Azure extract all the faces in this image and compares the found faces to a person group trained previously. If a person is recognized, the picture will be put in a output folder with the person's name.

To sum it up, all the calculations and Machine Learning are done in the Azure Cloud, this project is just a wrapper to make the usage more convenient.

## How to use

The project provides a simple command line interface with two options, "train" and "classify" to train a new person group or classify images using an existing person group. The project is provided with demo pictures of two persons so you can try it out, see how it works and switch the persons and pictures for fotos of your friends (or whoever you want to recognize). I do not have anything to do with the persons in the demo pictures, I just read their books recently and googled some pictures of them.

In a folder on your computer:

`git pull https://github.com/BeneHa/azure_face_recognition`

`cd azure_face_recognition`

`python3 -m venv .`

`venv/bin/activate` (depending on your operating system)

`pip install -r requirements.txt`

Edit the config.yaml and enter your subscription URL and API key for the Azure Face Recognition API.

`python face_recognition.py`

Run the script once entering "train" and use e.g. "demo" as name for the person group. Then run it again using "classify" and the same name from before. Look at the output folder to see the structure how the results will be saved.

After that, create folders in the input, fill them with images, and train and use your own person groups.

## FAQ

<b>What should the training images look like?</b>

There should only be one person on a training image, the person's face should be visible from the front and it should be as high resolution as possible. If you have good pictures, you will need fewer (1 or 2 should be fine in that case).

<b>What happens if there are multiple persons on one picture?</b>

The picture will be located in the output multiple times, once for each person that is found. 

<b>Where are my images being saved?</b>

The images are being uploaded to Azure for processing, but according to Microsoft, these images are not being saved. I provide no guarantee for anything Microsoft does with your images.

<b>Why does it take so long to classify images?</b>

I assume you, like me, are using the free version of the API, so you can only send one request every 3 seconds. That is why there are wait statements in the code to ensure the API does not block any requests.

<b>Something is not working?!?</b>

Please let me know, this is just something I put together some evenings after work so errors are to be expected :)

