#!/usr/bin/env python
import time
import cv2

#import catFinder
import json

infile = open("config.json")
credObj = json.load(infile)
print(credObj)

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


