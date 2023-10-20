#!/usr/bin/env python
import cv2
import catFinder
from ultralytics import YOLO
from PIL import Image
import numpy as np

import imgUtils
'''
from ultralytics import YOLO

test_image_path="/home/graham/yolo/datasets/CatoCam.v5/test/images"

model = YOLO("runs/detect/train5/weights/best.pt")

for input_filename in os.listdir(test_image_path):
    if '.jpg' in input_filename:
        test_full_path = os.path.join(test_image_path, input_filename)
        results = model.predict(source=test_full_path)

        for r in results:
            boxes = r.boxes  # Bounding box coordinates
            masks = r.masks  # Segmentation masks
            probs = r.probs  # Class probabilities
            '''

class CatFinderYolo(catFinder.CatFinder):
    def __init__(self, settingsObj, debug):
        ''' Initialise the YoloV8 based cat finding object detector.
        It expects the following elements in settingsObj:
           - weights - filename of yolo weights file (e.g. best.pt)
           - thresholds - the threshold 0 to 1 to be used to determine if one of the model class is detected (e.g. 0.5 = 50% confidence)
        '''
        super().__init__(settingsObj, debug)
        self.weightsFname = settingsObj['weights']
        self.thresholds = settingsObj['thresholds']

        self.model = YOLO(self.weightsFname)



    def getInferenceResults(self, img):
        print("catFinderYolo.getInferenceResults() - img.shape=", img.shape)
        resultsObj = self.model.predict(img, verbose=False)
        #print("resultsObj=",resultsObj)
        retObj = {}
        retObj['predictions'] = []
        for r in resultsObj:
            namesObj = r.names
            #print("getInferenceResults() namesObj=", namesObj)
            detObj = { 'class': None, 'confidence': 0 }
            for b in r.boxes:
                detObj = {}
                classId = b.cls.item()
                #print("getInferenceResults() - classId=",classId)
                detObj['class'] = namesObj[classId]
                detObj['confidence'] = b.conf
                bbox = b.xywh[0]
                #print(bbox)
                detObj['x'] = bbox[0]
                detObj['y'] = bbox[1]
                detObj['w'] = bbox[2]
                detObj['h'] = bbox[3]
            retObj['predictions'].append(detObj)
            
            
        #print("CatFinderYolo.getInferenceResults() - retObj=", retObj)
        return retObj

    def getAnnotatedImage(self, img):
        resultsObj = self.model.predict(img, verbose=False)
        r = resultsObj[0]
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        #im.show()  # show image
        im.save('results.jpg')  # save image
        # Convert to opencv format before returning.
        return(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))
        

# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())

if __name__ == "__main__":
    print("CatFinderYolo.main()");