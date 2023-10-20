
from ultralytics import YOLO

test_image_path="/home/graham/yolo/datasets/CatoCam.v5/test/images"

model = YOLO("yoloWeights.pt")

model.export(format="tflite")
