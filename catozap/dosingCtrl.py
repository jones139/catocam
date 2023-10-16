#!/usr/bin/python3

# Greenhouse water controller interface
# Assumes dosing pump motor is actuated by GPIO pin
# cfg['dosingControlPin']

import os
import time
import datetime
import threading
import logging
import RPi.GPIO as GPIO
import simple_pid
import dbConn
import monitorDaemon

class _dosingCtrlThread(threading.Thread):
    def __init__(self, cfg, debug = False):
        print("_dosingCtrlThread.__init__()")
        self.DEBUG = debug
        self.cycleStartTime = None
        self.dosingStartTime = None
        self.waterStatus=0

        self.cfg = cfg
        self.logger = logging.getLogger(self.cfg['logName'])
        self.dosingControlPin = cfg['dosingControlPin']
        threading.Thread.__init__(self)

        self.runThread = True
        self.curTime = datetime.datetime.now()

        self.onSecs = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.dosingControlPin], GPIO.OUT)
        
    def run(self):
        """
        The main loop of the thread  repeatedly checks to see if it is time
        to switch the water on or off.
        """
        self.logger.info("dosingCtrlThread.run()")

        while self.runThread:
            # Start cycle
            self.cycleStartTime = datetime.datetime.now()

            # Apply some water
            if (self.onSecs>0):
                self.waterForTime(self.onSecs)
                self.onSecs = 0
            else:
                self.logger.info("onSecs <= 0 secs - not watering")

            time.sleep(1.0)
        self.logger.info("dosingCtrlThread.run() - Exiting")
        self.waterOff()

    def stop(self):
        """ Stop the background thread"""
        self.waterOff()
        self.logger.info("Stopping thread")
        self.runThread = False


    def waterForTime(self, onSecs):
        self.waterOn()
        self.waterOnTime = datetime.datetime.now()
        self.logger.info("dosingOn")
        # Wait for time to switch water off.
        dt = datetime.datetime.now()
        while (dt - self.waterOnTime).total_seconds() < onSecs:
            time.sleep(0.1)
            dt = datetime.datetime.now()
        self.waterOff()
        self.logger.info("dosingOff")

        
    def waterOn(self):
        self.logger.info("dosingOn()")
        if (self.DEBUG): print("_dosingCtrlThread.dosingOn()")
        GPIO.output(self.dosingControlPin, GPIO.HIGH)
        self.waterStatus=1

    def waterOff(self):
        self.logger.info("dosingOff()")
        if (self.DEBUG): print("_dosingCtrlThread.dosingOff()")
        GPIO.output(self.dosingControlPin, GPIO.LOW)
        self.waterStatus=0


class DosingCtrlDaemon():
    '''
    Start a thread that runs in the background
    '''

    def __init__(self,cfgObj, debug=False):
        '''
        Initialise the class using data provided in object cfgObj
        '''
        self.DEBUG = debug
        self.cfg = cfgObj
        self.logger = logging.getLogger(self.cfg['logName'])
        self.logger.info("DosingCtrlDaemon.__init__()")
        self.dosingCtrlThread = _dosingCtrlThread(cfgObj, debug)
        self.dosingCtrlThread.daemon = True


    def start(self):
        ''' Start the background process and make sure that dosing is off.
        '''
        print("DosingCtrlDaemon.start()")
        self.logger.info("DosingCtrlDaemon.start()")
        self.dosingCtrlThread.start()
        self.dosingCtrlThread.waterOff()
        self.dosingCtrlThread.onSecs = 0.0

    def stop(self):
        ''' Stop the background process
        '''
        print("DosingCtrlDaemon.stop()")
        self.logger.info("DosingCtrlDaemon.stop()")
        self.dosingCtrlThread.stop()

    def setOnSecs(self, onSecs):
        print("dosingCtrlDaemon.setOnSecs(%f)" % onSecs)
        self.logger.info("DosingCtrlDaemon.setOnSecs(%f)" % onSecs)
        self.dosingCtrlThread.onSecs = onSecs
        return("OK")


    def getStatus(self):
        statusObj = {}
        statusObj['onSecs'] = self.dosingCtrlThread.onSecs
        statusObj['dosingStatus']=self.dosingCtrlThread.waterStatus
        return statusObj
        
if __name__ == '__main__':
    print("dosingCtrl.__main__()")

    cfgObj = {
        "logName": "dosingCtrl",
        "dosingControlPin": 24,
        "waterOnSecs": 2,
        }

    dosingCtrl = DosingCtrlDaemon(cfgObj, debug=True)
    dosingCtrl.start()
    #print("waiting 1 secs..")
    #time.sleep(1)
    print("dosing for 100 secs")
    dosingCtrl.setOnSecs(100)
    print("waiting 110 secs..")
    time.sleep(110)
    #dosingCtrl.setOnSecs(2)
    #print("waiting 3 secs..")
    #time.sleep(3)
    dosingCtrl.stop()
    #print("waiting 2 secs..")
    #time.sleep(2)
    print("exiting")
