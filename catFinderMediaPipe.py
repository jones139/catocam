#!/usr/bin/env python
import cv2
import catFinder
from PIL import Image
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import imgUtils

class CatFinderMediaPipe(catFinder.CatFinder):
    def __init__(self, settingsObj, debug):
        ''' Initialise the MediaPipe tflite based cat finding object detector.
        It expects the following elements in settingsObj:
           - weights - filename of tflite weights file (e.g. model.tflite)
           - thresholds - the threshold 0 to 1 to be used to determine if one of the model class is detected (e.g. 0.5 = 50% confidence)
        '''
        super().__init__(settingsObj, debug)
        self.weightsFname = settingsObj['weights']
        self.thresholds = settingsObj['thresholds']

        BaseOptions = mp.tasks.BaseOptions
        ObjectDetector = mp.tasks.vision.ObjectDetector
        ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = ObjectDetectorOptions(
            base_options=BaseOptions(model_asset_path=self.weightsFname),
            max_results=5,
            running_mode=VisionRunningMode.IMAGE)

        self.model = ObjectDetector.create_from_options(options)




    def getInferenceResults(self, img):
        #print("catFinderMediaPipe.getInferenceResults() - img.shape=", img.shape)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
        resultsObj =  self.model.detect(mp_image)
    
        #print("resultsObj=",resultsObj)
        #print(dir(resultsObj))

        retObj = {}
        retObj['predictions'] = []
        for r in resultsObj.detections:
            #print(r)
            #namesObj = r.names
            #print("getInferenceResults() namesObj=", namesObj)
            detObj = { 'class': None, 'confidence': 0 }
            bbox = r.bounding_box
            classObj = r.categories[0]
            #print(bbox, classObj)
            detObj['class'] = classObj.category_name
            detObj['confidence'] = classObj.score
            detObj['x'] = int(bbox.origin_x+0.5*bbox.width)
            detObj['y'] = int(bbox.origin_y+0.5*bbox.height)
            detObj['width'] = bbox.width
            detObj['height'] = bbox.height
            retObj['predictions'].append(detObj)
            
            
        #print("CatFinderMediaPipe.getInferenceResults() - retObj=", retObj)
        return retObj


if __name__ == "__main__":
    print("CatFinderYolo.main()");