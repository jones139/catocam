#!/usr/bin/env python
import cv2
import catFinder
from PIL import Image
import numpy as np
import tensorflow as tf


class CatFinderTfLite(catFinder.CatFinder):
    def __init__(self, settingsObj, debug):
        ''' Initialise the Tensor Flow TfLite based cat finding object detector.
        It expects the following elements in settingsObj:
           - weights - filename of yolo weights file (e.g. best.tflite)
           - thresholds - the threshold 0 to 1 to be used to determine if one of the model class is detected (e.g. 0.5 = 50% confidence)
        '''
        super().__init__(settingsObj, debug)
        self.weightsFname = settingsObj['weights']
        self.thresholds = settingsObj['thresholds']

        self.model = tf.lite.Interpreter(
            model_path=self.weightsFname,
            experimental_delegates=None,
            num_threads=1)
        self.model.allocate_tensors()

        self.input_details = self.model.get_input_details()
        self.output_details = self.model.get_output_details()

        # check the type of the input tensor
        self.floating_model = self.input_details[0]['dtype'] == np.float32

        # NxHxWxC, H:1, W:2
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

        print("CatFinder.TfLite.__init__():  Floating Model=%d, h=%d, w=%d" % (self.floating_model, self.height, self.width))
        print(" input_details= ", self.input_details)
        print(" output_details=", self.output_details)
        #img = Image.open(args.image).resize((width, height))



    def getInferenceResults(self, img):
        # add N dim
        print("catFinderTfLite.getInferenceResults - img.shape=", img.shape)

        #scale image
        imgScaled = img.resize((self.width, self.height))
        input_data = np.expand_dims(imgScaled, axis=0)
        print(" input_data.shape=",input_data.shape)

        if self.floating_model:
            input_data = (np.float32(input_data))   #Normalise data?

        self.model.set_tensor(self.input_details[0]['index'], input_data)

        #start_time = time.time()
        self.model.invoke()
        #stop_time = time.time()

        output_data = self.model.get_tensor(self.output_details[0]['index'])
        print("output_data=",output_data)
        results = np.squeeze(output_data)

        top_k = results.argsort()[-5:][::-1]
        print("top_k=",top_k)

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