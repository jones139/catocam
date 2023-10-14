#!/usr/bin/env python
import cv2
import catFinder
from roboflow import Roboflow
from inference_sdk import InferenceHTTPClient

import imgUtils


class CatFinderRoboflow(catFinder.CatFinder):
    def __init__(self, settingsObj, debug):
        ''' Initialise the Roboflow based cat finding object detector.
        It expects the following elements in settingsObj:
           - apiKey - Roboflow API key
           - projectId - Roboflow project ID of model to be used
           - versionId - Version ID of Roboflow model to be used
           - localServer - if true uses a roboflow inference server on localhost:9001, rather than the one hosted by Roboflow.
           - thresholds - the threshold 0 to 1 to be used to determine if one of the model class is detected (e.g. 0.5 = 50% confidence)
        '''
        super().__init__(settingsObj, debug)
        self.apiKey = settingsObj['apiKey']
        self.projectId = settingsObj['projectId']
        self.versionId = settingsObj['versionId']
        self.localServer = settingsObj['localServer']
        self.thresholds = settingsObj['thresholds']

        if not self.localServer:
            try:
                rf = Roboflow(api_key=self.apiKey)
                project = rf.workspace().project(self.projectId)
                self.model = project.version(self.versionId).model
            except Exception as e:
                print("***************************************************************************************")
                print("******                   Error connecting to Roboflow Model                      ******")
                print("****** Have you started the local inference server with 'inference server start'? *****")
                print("***************************************************************************************")
                raise



    def getInferenceResults(self, img):
        if self.localServer:
            try:
                CLIENT = InferenceHTTPClient(
                api_url="http://localhost:9001",
                api_key=self.apiKey
                )
                retObj = CLIENT.infer(img, model_id="%s/%s" % (self.projectId,self.versionId))
            except Exception as e:
                print("***************************************************************************************")
                print("******                   Error connecting to Roboflow Model                      ******")
                print("****** Have you started the local inference server with 'inference server start'? *****")
                print("***************************************************************************************")
                raise

        else:
            # infer using hosted model
            retObj = self.model.predict(img, confidence=50, overlap=30).json()
        #print("CatFinderRoboflow.findCat() - retObj=", retObj)
        return retObj



    def findCat(self, img):
        retObj = self.getInferenceResults(img)
        foundCat = False
        for pred in retObj['predictions']:
            if pred['class']=="Cat" and pred['confidence']>0.5:
                foundCat = True
        return(foundCat, retObj)

    def getAnnotatedImage(self, img):
            '''
            Returns the image annotated with the detected objects, using the retObj 
            returned by findCat()
            '''
            results = results=self.getInferenceResults(img)
            #print(results)
            if len(results['predictions'])>0:
                for pred in results['predictions']:
                    #print(pred)
                    if pred['confidence']>0.5:
                    
                        #bounding_box = results[0][0]
                        #print(bounding_box)

                        #x0, y0, x1, y1 = map(int, bounding_box[:4])
                        x0 = int(pred['x']-0.5*pred['width'])
                        y0 = int(pred['y']-0.5*pred['height'])
                        x1 = int(x0 + pred['width'])
                        y1 = int(y0 + pred['height'])

                        if x0<0:
                            x0 = 0
                        if y0 <0:
                            y0 = 0

                        #print("bbox=(%d, %d, %d, %d)" % (x0,y0,x1,y1))
                        
                        cv2.rectangle(img, (x0, y0), (x1, y1), (255,255,0), 3)
                        cv2.putText(img, pred['class'], (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                    imgScaled = imgUtils.scaleW(img,640)
                    # Show image
                    #cv2.imshow('Image Frame', imgScaled)
                    #cv2.waitKey(1) # waits 1ms
                    #cv2.destroyAllWindows() # destroys the window showing imag
                    return(imgScaled)

# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())

if __name__ == "__main__":
    print("CatFinderRoboflow.main()");