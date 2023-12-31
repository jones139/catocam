
#!/usr/bin/env python

# Based on https://stackoverflow.com/questions/40460846/using-flask-inside-class
import os
import flask
import datetime
import time
import cv2
try:
    import gpiozero
except:
   gpiozero = None
   import psutil


class CatSvr():
    def __init__(self, catoCam):
        '''
        Initialise the catocam web server - catoCam should be an instance of the CatoCam class that is
        doing the cat detection
        '''
        self.cc = catoCam
        self.app = flask.Flask("CatoCam", template_folder="/home/graham/catocam/www/templates", 
                               static_folder="/home/graham/catocam/www/static", static_url_path='/')
        self.app.add_url_rule(rule="/index.html", view_func=self.getIndex)
        self.app.add_url_rule(rule="/", view_func=self.getIndex)
        self.app.add_url_rule(rule="/history/<dateStr>", view_func=self.getHistory)
        self.app.add_url_rule(rule="/history/<dateStr>/<idx>", view_func=self.getHistory)
        self.app.add_url_rule(rule="/status", view_func=self.getStatus)
        self.app.add_url_rule(rule="/mjpeg", view_func=self.getMjpeg)
        self.app.add_url_rule(rule="/currimg", view_func=self.getCurImg)
        self.app.add_url_rule(rule="/lastimg", view_func=self.getLastPositiveImg)
        self.app.add_url_rule(rule="/histimg/<dateStr>/<idx>", view_func=self.getHistoryImg)
        #self.app.add_url_rule(rule="/favicon.ico", view_func=self.getFavicon)
        self.lastImgTime = None

    def run(self, nameStr):
        print("CatSvr.run(): %s" % nameStr)
        self.app.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)
        print("CatSvr.run() finished.")

    def getIndex(self):
        outputFolderLst = self.cc.getOutputFoldersLst()
        statusObj = self.getStatus()
        return flask.render_template('index.html', 
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     folders=outputFolderLst,
                                     fps = "%.2f" % statusObj['fps'],
                                     cpuT = "%.1f" % statusObj['cpuT']
                                     )


    def getHistory(self, dateStr, idx=None):
        #print("getHistory() - dateStr=%s, idx=%s" % (dateStr, idx))
        outputFolderLst = self.cc.getOutputFoldersLst()
        imgLst = self.cc.getSavedImgLst(dateStr)
        statusObj = self.getStatus()
        #print("getHistory() - imgLst=", imgLst)
        if idx is not None and idx != "None":
            idx = int(idx)
            if idx>=0 and idx<=len(imgLst):
                imgStr = imgLst[idx]
                if idx>0: 
                    idxPrev = idx-1
                else:
                    idxPrev = None
                if idx<len(imgLst)-1:
                    idxNext = idx+1
                else:
                    idxNext = None
        else:
            imgStr = None
            idxPrev = None
            idxNext = None
        return flask.render_template('history.html', 
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     folders=outputFolderLst, 
                                     dir=dateStr, 
                                     img=imgStr, 
                                     idx=idx,
                                     idxPrev=idxPrev,
                                     idxNext=idxNext,
                                     imgLst=imgLst,
                                     fps = "%.2f" % statusObj['fps'],
                                     cpuT = "%.1f" % statusObj['cpuT']
                                     )


    def getHistoryByFilename(self, dateStr, imgStr=None):
        print("getHistory() - dateStr=%s, imgStr=%s" % (dateStr, imgStr))
        outputFolderLst = self.cc.getOutputFoldersLst()
        imgLst = self.cc.getSavedImgLst(dateStr)
        statusObj = self.getStatus()
        #print("getHistory() - imgLst=", imgLst)
        return flask.render_template('history.html', 
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     folders=outputFolderLst, 
                                     dir=dateStr, 
                                     img=imgStr, 
                                     imgLst=imgLst,
                                     fps = "%.2f" % statusObj['fps'],
                                     cpuT = "%.1f" % statusObj['cpuT']
                                     )

    def getStatus(self):
        now = datetime.datetime.now()
        timeString = now.strftime("%Y-%m-%d %H:%M")
        if gpiozero is not None:
            cpuTemp = gpiozero.CPUTemperature().temperature
        else:
            print(psutil.sensors_temperatures())
            cpuTemp = psutil.sensors_temperatures()['coretemp'][0][1]
        statusData = {
            'title' : 'CatoCam',
            'time': timeString,
            'cpuT': cpuTemp,
            'foundCat': self.cc.foundCat,
            'foundSomething': self.cc.foundSomething,
            'fps': self.cc.fps,
            'imgTime': self.cc.imgTime
        }
        return statusData

    def prepareImgStream(self):
        while True:
            time.sleep(0.2)
            if self.lastImgTime != self.cc.imgTime:
                a , frame = cv2.imencode('.jpg', self.cc.currImg)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

    def getMjpeg(self):
        return flask.Response(self.prepareImgStream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    

    def getCurImg(self):
        if self.cc.currImg is None:
            return "", 204
        # Based on https://stackoverflow.com/questions/42787927/displaying-opencv-image-using-python-flask
        retval, buffer = cv2.imencode('.png', self.cc.currImg)
        response = flask.make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response

    def getLastPositiveImg(self):
        if self.cc.lastPositiveImg is None:
            return "", 204
        # Based on https://stackoverflow.com/questions/42787927/displaying-opencv-image-using-python-flask
        retval, buffer = cv2.imencode('.png', self.cc.lastPositiveImg)
        response = flask.make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response
    
    def getHistoryImg(self, dateStr, idx):
        if idx is None:
            return None
        idx = int(idx)
        print("getHistoryImg() - dateStr=%s, imgStr=%s" % (dateStr, idx))
        img = self.cc.getHistoryImgByIndex(dateStr, idx)
        if img is None:
            return "", 204
        # Based on https://stackoverflow.com/questions/42787927/displaying-opencv-image-using-python-flask
        retval, buffer = cv2.imencode('.png', img)
        response = flask.make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response

    def getHistoryImgByName(self, dateStr, imgStr):
        print("getHistoryImg() - dateStr=%s, imgStr=%s" % (dateStr, imgStr))
        img = self.cc.getHistoryImg(dateStr, imgStr)
        if img is None:
            return "", 204
        # Based on https://stackoverflow.com/questions/42787927/displaying-opencv-image-using-python-flask
        retval, buffer = cv2.imencode('.png', img)
        response = flask.make_response(buffer.tobytes())
        response.headers['Content-Type'] = 'image/png'
        return response

    def getFavicon(self):
        return flask.send_from_directory(os.path.join(self.app.root_path, 'www'),
                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
   #app.run(host='0.0.0.0', port=8082, debug=True)
   catSvr = CatSvr(None)
   catSvr.run()
