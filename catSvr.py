#!/usr/bin/env python

# Based on https://stackoverflow.com/questions/40460846/using-flask-inside-class

import flask
import datetime
try:
    import gpiozero
except:
   gpiozero = None


class CatSvr():
    def __init__(self, catoCam):
        '''
        Initialise the catocam web server - catoCam should be an instance of the CatoCam class that is
        doing the cat detection
        '''
        self.cc = catoCam
        self.app = flask.Flask("CatoCam")

        self.app.add_url_rule(rule="/status", view_func=self.getStatus)

    def run(self, nameStr):
        print("CatSvr.run(): %s" % nameStr)
        self.app.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)
        print("CatSvr.run() finished.")

    #def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
    #    self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(handler))

    def getStatus(self):
        now = datetime.datetime.now()
        timeString = now.strftime("%Y-%m-%d %H:%M")
        if gpiozero is not None:
            cpuTemp = gpiozero.CPUTemperature()
        else:
            cpuTemp = -1.0
        statusData = {
            'title' : 'HELLO!',
            'time': timeString,
            'cpuT': cpuTemp
        }
        return statusData



'''app = flask.Flask(__name__)
@app.route("/")
def hello():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
      'title' : 'HELLO!',
      'time': timeString
      }
   return flask.render_template('index.html', **templateData)
@app.route("/status")
def getStatus():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    if gpiozero is not None:
        cpuTemp = gpiozero.CPUTemperature()
    else:
        cpuTemp = -1.0
    statusData = {
        'title' : 'HELLO!',
        'time': timeString,
        'cpuT': cpuTemp
    }
    return statusData

'''
if __name__ == "__main__":
   #app.run(host='0.0.0.0', port=8082, debug=True)
   catSvr = CatSvr(None)
   catSvr.run()