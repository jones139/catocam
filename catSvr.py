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
        self.app = flask.Flask("CatoCam", template_folder="www/templates", 
                               static_folder="www/static", static_url_path='/')
        self.app.add_url_rule(rule="/index.html", view_func=self.getIndex)
        self.app.add_url_rule(rule="/", view_func=self.getIndex)
        self.app.add_url_rule(rule="/history/<dateStr>", view_func=self.getHistory)
        self.app.add_url_rule(rule="/history/<dateStr>/<imgStr>", view_func=self.getHistory)
        self.app.add_url_rule(rule="/status", view_func=self.getStatus)
        self.app.add_url_rule(rule="/mjpeg", view_func=self.getMjpeg)
        self.app.add_url_rule(rule="/currimg", view_func=self.getCurImg)
        self.app.add_url_rule(rule="/lastimg", view_func=self.getLastPositiveImg)
        self.app.add_url_rule(rule="/histimg/<dateStr>/<imgStr>", view_func=self.getHistoryImg)
        #self.app.add_url_rule(rule="/favicon.ico", view_func=self.getFavicon)
        self.lastImgTime = None

    def run(self, nameStr):
        print("CatSvr.run(): %s" % nameStr)
        self.app.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)
        print("CatSvr.run() finished.")

    def getIndex(self):
        outputFolderLst = self.cc.getOutputFoldersLst()
        return flask.render_template('index.html', 
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     folders=outputFolderLst)

    def getHistory(self, dateStr, imgStr=None):
        print("getHistory() - dateStr=%s, imgStr=%s" % (dateStr, imgStr))
        outputFolderLst = self.cc.getOutputFoldersLst()
        imgLst = self.cc.getSavedImgLst(dateStr)
        print("getHistory() - imgLst=", imgLst)
        return flask.render_template('history.html', 
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                     folders=outputFolderLst, 
                                     dir=dateStr, 
                                     img=imgStr, 
                                     imgLst=imgLst)

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
    
    def getHistoryImg(self, dateStr, imgStr):
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