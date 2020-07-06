# Azure Face Recognition

This is a small project to use the Azure Cognitive Services, in this case the Face API, for face recognition. I had thousands of pictures of the last 10 years and needed to find some from specific persons, so this is how I did it.

If you want to replicate this project, here is my folder structure:


📦faces
 ┣ 📂input_resized
 ┣ 📂original
 ┃ ┣ 📂Person 1
 ┃ ┃ ┣ train_img1.jpg
 ┃ ┃ ┣ train_img2.jpg
 ┃ ┣ 📂Person 2
 ┣ 📂output
 ┣ 📂test_images
 ┃ ┣ 📜IMG1.jpg
 ┃ ┣ 📜IMG2.jpg
 ┗ 📂test_images_resized

 You need to put images in the "original" and "test_images" folder. Original images are the images used for trainig, test images are the ones where you want faces recognized.