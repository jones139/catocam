#!/usr/bin/env python
import cv2
import catFinder
from roboflow import Roboflow

class CatFinderRoboflow(catFinder.CatFinder):
    def __init__(self, settingsObj, debug):
        super().__init__(settingsObj, debug)
        rf = Roboflow(api_key=settingsObj['apiKey'])
        project = rf.workspace().project(settingsObj['projectId'])
        self.model = project.version(settingsObj['versionId']).model


    def findCat(self, img):
        # infer on a local image
        retObj = self.model.predict(img, confidence=50, overlap=30).json()
        #print("CatFinderRoboflow.findCat() - retObj=", retObj)
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
            results = self.model.predict(img, confidence=50, overlap=30).json()
            #print(results)
            if len(results['predictions'])>0:
                for pred in results['predictions']:
                    print(pred)
                   
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

                    print("bbox=(%d, %d, %d, %d)" % (x0,y0,x1,y1))
                    
                    cv2.rectangle(img, (x0, y0), (x1, y1), (255,255,0), 10)
                    cv2.putText(img, "Cat", (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

                    h, w, c = img.shape
                    print("initial w,h=%d,%d" % (w,h))
                    wNew = 640
                    scale = w*1.0/640
                    hNew = int(h*640/w)
                    print("new w,h=%d,%d" % (wNew, hNew))
                    
                    imgScaled = cv2.resize(img, (wNew, hNew))

                    # Show image
                    cv2.imshow('Image Frame', imgScaled)
                    cv2.waitKey(1) # waits 1ms
                    #cv2.destroyAllWindows() # destroys the window showing imag

# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())

if __name__ == "__main__":
    print("CatFinderRoboflow.main()");