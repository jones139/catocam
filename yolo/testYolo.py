import os
from ultralytics import YOLO

test_image_path="/home/graham/yolo/datasets/CatoCamV6/test/images"

model = YOLO("runs/detect/train8/weights/best.pt")

for input_filename in os.listdir(test_image_path):
    if '.jpg' in input_filename:
        test_full_path = os.path.join(test_image_path, input_filename)
        results = model.predict(source=test_full_path, save=True)
        print("Image=%s, len(results)=%d" % (input_filename, len(results)))
        for r in results:
            print(r.names)
            for b in r.boxes:
                print(b.xywh, b.cls, b.conf)
        #r.render()
