
<img src="https://github.com/jones139/catocam/blob/main/www/static/catocam_logo.png?raw=true" width=100/>CatoCam
=======
Detect and Deter cats using cctv images.

Purpose
=======
The purpose of catocam is to deter cats from regarding our garden as their territory humanely.   We do not appreciate what they leave behind!

Project Outline
===============
There are two distinct parts to the project - catocam and catozap
Catocam utilises a Tp-Link tapo cctv camera by connecting to its local network rtsp stream to grab frames.   It uses a machine learning object detection model to determine whether the frame contains an image of a cat or not.
If a cat is detected it will send a signal to catozap to unleash a cat deterrent.

Catozap waits for a signal from catocam, then tries to deter the cat from remaining in the garden.   It is likely to do this using a water spray, but I might try an ultrasonic deterrent as done in this [similar project](https://medium.com/@james.milward/deterring-foxes-and-badgers-with-tensorflow-lite-python-raspberry-pi-ring-cameras-ultrasonic-75b3160faa3c).

CatoCam Structure
=================
  - Connect to the camera rtsp stream using opencv
  - Grab a frame
  - Detect cats in the frame using a custom trained [YoloV8](https://yolov8.com) model.
  - Save annotated frames that contain detected cats, birds or humans to disk for future analysis
  - If a cat is detected, send a signla to catozap to unleash the deterrent.

  Catocam is running on a Raspberry Pi 4B, 2GB memory and achieving 0.6 frames per second.  I am hoping to improve this by using a quantized version of the yolov8n model.

  An example output is shown below:
  <img src="https://github.com/jones139/catocam/blob/main/Docs/example_image.png?raw=true" width=640/>




