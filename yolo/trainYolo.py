from ultralytics import YOLO

# Load a model
#model = YOLO('yolov8n.pt')  # load a pretrained model (recommended for training)
model = YOLO('catFinderV13_yoloWeights.pt')

# Train the model
results = model.train(data='/home/graham/yolo/datasets/catocam_v14/data.yaml', epochs=100, imgsz=640)
