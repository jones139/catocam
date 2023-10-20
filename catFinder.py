# Abstract cat finder class - different algorithms will inherit from this class 
# to provide a consistent interface

class CatFinder:
    ''' 
    CatFinder is an abstract class to provide a standard interface to a cat finding model.
    '''
    def __init__(self, settingsObj, debug):
        '''
        Initialise the model
        '''
        print("CatFinder.__init__")
        self.settingsObj = settingsObj
        self.debug = debug

    def findCat(self, img):
        retObj = self.getInferenceResults(img)
        foundCat = False
        for pred in retObj['predictions']:
            if pred['class']=="Cat" and pred['confidence']>self.thresholds['Cat']:
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
                    if pred['confidence']>self.thresholds[pred['class']]:
                        print("found %s" % pred['class'])
                    
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


