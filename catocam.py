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
        FRAME_BATCH_SIZE = fileFps / fps
        success = True
        nFrames = 0
        batchStartTime = time.time()
        while success:
            success, img = cap.read()
            nFrames += 1
            if nFrames >=FRAME_BATCH_SIZE:
                self.analyseImage(img)
                tdiff = time.time() - batchStartTime
                fps = nFrames / tdiff
                print("%d frames in %.1f sec - %.1f fps" % (nFrames, tdiff, fps))
                batchStartTime = time.time()
                nFrames = 0


    def getFrames(self, testFname=None):
        if testFname is not None:
            self.testFile(testFname)

        camArr = []
        for cam in self.configObj["cameras"]:
            print("getFrames() adding camera")
            # Tp-Link Tapo camera RTSP stream - stream1 is high quality, stream2 low quality.
            camArr.append(cv2.VideoCapture(cam["serverUrl"]))

        FRAME_RATE_REQ = self.configObj['maxFps']
        FRAME_BATCH_SIZE = int(10 * FRAME_RATE_REQ)
        nFrames = 0
        batchStartTime = time.time()
        iterDurationReq = 1.0/FRAME_RATE_REQ
        #cf = catFinder.CatFinder()
        while(camArr[0].isOpened()):
            iterStartTime = time.time()
            ret, frame = camArr[0].read()
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

        camArr[0].release()
        cv2.destroyAllWindows()
        print("Finished")


if __name__ == "__main__":
    print("catocam.main()")
    parser = argparse.ArgumentParser(description='Detect Cats in Video Streams')
    parser.add_argument('--config', default="config.json",
                        help='name of json configuration file')
    parser.add_argument('--test', default=None,
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
        cc.getFrames(testFname=None)
