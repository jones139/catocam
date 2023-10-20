#!/usr/bin/env python
import importlib
import sys
import os
import time
import datetime
import cv2

import argparse
import json
import framegrab

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

        self.outDir = configObj['outDir']
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)

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


    def recordCat(self, retObj, img):
        todaysDate = datetime.datetime.now()
        outFolder = todaysDate.strftime("%Y-%m-%d")
        outSubDir = os.path.join(self.outDir, outFolder)
        if not os.path.exists(outSubDir):
            os.makedirs(outSubDir, exist_ok=True)
        imgFname = "catocam-%s-%s.png" % (retObj['predictions'][0]['class'], todaysDate.strftime("%H_%M_%s"))
        logFname = "catocam.log"
        cv2.imwrite(os.path.join(outSubDir,imgFname), img)

        fp = open(os.path.join(outSubDir, logFname),"a")
        timeStr = todaysDate.strftime("%Y/%m/%d %H:%M:%S")
        pred =retObj['predictions'][0]
        print("\n%s: class = %s (%.2f%%) " % (timeStr, pred['class'], pred['confidence']))
        if pred['confidence'] > self.mModels[0][1].thresholds[pred['class']]:
            fp.write("\"%s\", %s, %.f%%, %s\n" % (timeStr, pred['class'], pred['confidence']*100., imgFname))
        fp.close()
        

    def analyseImage(self, img):
        for modelName, modelClass in self.mModels:
            foundCat, retObj = modelClass.findCat(img)
            #print(modelName, foundCat, retObj)
            foundSomething = False
            for pred in retObj['predictions']:
                if pred['confidence']>0.5:
                    foundSomething = True

            if foundSomething:
                annotatedImg = modelClass.getAnnotatedImage(img)
                self.recordCat(retObj, annotatedImg)


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
                if (success):
                    self.analyseImage(img)
                tdiff = time.time() - batchStartTime
                fps = nFrames / tdiff
                print("%d frames in %.1f sec - %.1f fps" % (nFrames, tdiff, fps))
                batchStartTime = time.time()
                nFrames = 0


    def getFrames(self, testFname=None):
        if testFname is not None:
            self.testFile(testFname)
            return
        
        camArr = []
        for cam in self.configObj["cameras"]:
            print("getFrames() adding camera")
            # Tp-Link Tapo camera RTSP stream - stream1 is high quality, stream2 low quality.
            print("Adding Camera: ", cam)
            grabber = framegrab.FrameGrabber.create_grabber(cam)
            camArr.append(grabber)

        FRAME_RATE_REQ = self.configObj['maxFps']
        FRAME_BATCH_SIZE = int(FRAME_RATE_REQ)
        FAIL_RESTART_COUNT = 10
        nFrames = 0
        batchStartTime = time.time()
        iterDurationReq = 1.0/FRAME_RATE_REQ

        print("Looking for Cats......")
        failCount = 0
        while(1):
            iterStartTime = time.time()
            img = grabber.grab()
            if (img is not None):
                cv2.imshow("frame", img)
                self.analyseImage(img)
                failCount = 0
            else:
                print("CatoCam.getFrames(): WARNING: Failed to retrieve image from camera")
                failCount += 1
                if (failCount >= FAIL_RESTART_COUNT):
                    print("CatoCam.getFrames(): Restarting frame Grabber")
                    grabber = framegrab.FrameGrabber.create_grabber(cam)
                    failCount = 0


            nFrames += 1
            if (nFrames >= FRAME_BATCH_SIZE):
                tdiff = time.time() - batchStartTime
                fps = nFrames / tdiff
                sys.stdout.write("%d frames in %.1f sec - %.1f fps\r" % (nFrames, tdiff, fps))
                sys.stdout.flush()
                batchStartTime = time.time()
                nFrames = 0
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            # Reduce frame rate to desired  rate.
            tnow = time.time()
            iterDuration = iterStartTime - tnow
            if (iterDuration < iterDurationReq):
                time.sleep(iterDurationReq - iterDuration)
                pass
            else:
                print("Not Sleeping - too slow!")

        for cam in camArr:
            cam.release()
        #camArr[0].release()
        #cv2.destroyAllWindows()
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
