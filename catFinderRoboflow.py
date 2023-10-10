#!/usr/bin/env python
from roboflow import Roboflow
rf = Roboflow(api_key="qpeWz2ekPrHwb4RM4SK0")
project = rf.workspace().project("catocam")
model = project.version(3).model

# infer on a local image
print(model.predict("fastCatTest.mp4", confidence=50, overlap=30).json())

# visualize your prediction
model.predict("catTest.jpg", confidence=40, overlap=30).save("prediction.jpg")

# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())