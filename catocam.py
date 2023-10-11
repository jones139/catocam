#!/usr/bin/env python
import importlib
import time
import cv2

import argparse
#import catFinder
import json


class CatoCam():
    def __init__(self, configObj, debug=None):
        self.debug = False
        if debug is not None:
            self.debug = debug
        else:
            if "debug" in configObj:
                self.debug = configObj['debug']
        print("CatoCam.__init__() - debug=%s" % self.debug)

        self.mModels = []
        self.configObj = configObj
        self.loadModels()

    def loadModels(self):
        if not "models" in self.configObj:
            print("CatoCam.loadModels() - ERROR - configObj does not contain a 'models' element.")
            raise
        for modelCfg in self.configObj['models']:
            moduleId = modelCfg['class'].split('.')[0]
            classId = modelCfg['class'].split('.')[1]
            print("Importing Module %s" % moduleId)
            module = importlib.import_module(moduleId)
            self.mModels.append((
                modelCfg['name'],
                eval("module.%s(modelCfg['settings'], self.debug)" % (classId))))
        
        for m in self.mModels:
            print("Model %s" % m[0])


    def analyseImage(self, img):
        for modelName, modelClass in self.mModels:
            foundCat, retObj = modelClass.findCat(img)
            print(modelName, foundCat, retObj)
            if foundCat:
                modelClass.getAnnotatedImage(img)

    def testFile(self, testFname, fps = 1):
        print("CatoCam.testFile() - testFname=%s" % testFname)
        cap = cv2.VideoCapture(testFname)
        fileFps = cap.get(cv2.CAP_PROP_FPS)
        frameSkip = fileFps / fps
        success = True
        nFrame = 0
        while success:
            success, img = cap.read()
            nFrame += 1
            if nFrame >=frameSkip:
                self.analyseImage(img)
                nFrame = 0

    def getFrames(self, testFname=None):
        if testFname is not None:
            self.testFile(testFname)

        camArr = []
        for cam in credObj["cameras"]:
            # Tp-Link Tapo camera RTSP stream - stream1 is high quality, stream2 low quality.
            camArr.append(cv2.VideoCapture(cam["serverUrl"]))

        FRAME_RATE_REQ = 1 # fps
        FRAME_BATCH_SIZE = 10
        nFrames = 0
        batchStartTime = time.time()
        iterDurationReq = 1.0/FRAME_RATE_REQ
        #cf = catFinder.CatFinder()
        while(cap.isOpened()):
            iterStartTime = time.time()
            ret, frame = cap.read()
            #cv2.imshow('frame', frame)
            #cf.findCat(frame)
            nFrames += 1
            if (nFrames >= FRAME_BATCH_SIZE):
                tdiff = time.time() - batchStartTime
                fps = nFrames / tdiff
                print("%d frames in %.1f sec - %.1f fps" % (nFrames, tdiff, fps))
                batchStartTime = time.time()
                nFrames = 0
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            # Reduce frame rate to desired  rate.
            tnow = time.time()
            iterDuration = iterStartTime - tnow
            if (iterDuration < iterDurationReq):
                time.sleep(iterDurationReq - iterDuration)

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    print("catocam.main()")
    parser = argparse.ArgumentParser(description='Detect Cats in Video Streams')
    parser.add_argument('--config', default="config.json",
                        help='name of json configuration file')
    parser.add_argument('--test', default="testFile.mp4",
                        help='run the system on a test video file rather than live data')
    #parser.add_argument('--index', action="store_true",
    #                    help='Re-build index, not all summaries')
    parser.add_argument('--debug', action="store_true",
                        help='Write debugging information to screen')
    
    argsNamespace = parser.parse_args()
    args = vars(argsNamespace)
    print(args)

    infile = open(args['config'])
    configObj = json.load(infile)
    print(configObj)

    cc = CatoCam(configObj, debug=args['debug'])
    if args['test'] is not None:
        testFname = args['test']
        print("Testing using file %s" % testFname)
        cc.getFrames(testFname=testFname)
    else:
        print("Monitoring Live Camera Streams")
