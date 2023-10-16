#!/usr/bin/python3

# Greenhouse water controller interface
# Assumes water control valve is actuated by GPIO pin
# cfg['waterControlPin']

import os
import time
import datetime
import threading
import logging
import RPi.GPIO as GPIO
import simple_pid
import dbConn
import monitorDaemon

class _waterCtrlThread(threading.Thread):
    def __init__(self, cfg, debug = False):
        print("_waterCtrlThread.__init__()")
        self.cfg = cfg
        self.logger = logging.getLogger(self.cfg['logName'])
        self.waterControlPin = cfg['waterControlPin']
        threading.Thread.__init__(self)
        self.dbPath = os.path.join(cfg['dataFolder'],cfg['dbFname'])

        # Initialise settings from database, or config file if DB values not set
        self.db = dbConn.DbConn(self.dbPath)
        dbSetpoint, dbKp, dbKi, dbKd, dbCycleSecs, dbControlVal, dbOnSecs, dbOpMode, dbLightThresh = self.db.getWaterControlVals()
        self.db.close()
        if (dbOpMode is None):
            self.opMode = cfg['opMode']
        else:
            self.opMode = dbOpMode
        if (dbOnSecs is None):
            self.onSecs = cfg['waterOnSecs']
        else:
            self.onSecs = dbOnSecs
        if (dbSetpoint is None):
            self.setPoint = cfg['setPoint']
        else:
            self.setPoint = dbSetpoint
        if (dbCycleSecs is None):
            self.cycleSecs = cfg['waterCycleSecs']
        else:
            self.cycleSecs = dbCycleSecs
        if (dbKp is None):
            self.Kp = cfg['Kp']
        else:
            self.Kp = dbKp
        if (dbKi is None):
            self.Ki = cfg['Ki']
        else:
            self.Ki = dbKi
        if (dbKd is None):
            self.Kd = cfg['Kd']
        else:
            self.Kd = dbKd
        if (dbLightThresh is None):
            self.lightThresh = cfg['lightThresh']
        else:
            self.lightThresh = dbLightThresh
        self.timeOnLimit = cfg['timeOnLimit']
            
        self.logger.info("_waterCtrlThread.__init__(): cycleSecs=%f, setpoint=%f" % (self.cycleSecs, self.setPoint))
        self.logger.info("_waterCtrlThread.__init__(): opMode=%s, (Kp,Ki,Kd)=(%f,%f,%f), lightThresh=%f" % (self.opMode, self.Kp, self.Ki, self.Kd, self.lightThresh))

        self.DEBUG = debug
        self.runThread = True
        self.curTime = datetime.datetime.now()
        self.waterStatus = 0
        self.soilCond = -1
        self.soilRes = -1
        self.controlVal = -1

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.waterControlPin], GPIO.OUT)
        
    def run(self):
        """
        The main loop of the thread  repeatedly checks to see if it is time
        to switch the water on or off.
        """
        self.logger.info("waterCtrlThread.run()")
        # re-open db for this thread.
        self.db = dbConn.DbConn(self.dbPath)

        self.pid = simple_pid.PID(self.Kp, self.Ki, self.Kd,
                                  setpoint=self.setPoint,
                                  sample_time=None,
                                  output_limits=(0,self.timeOnLimit))
        
        while self.runThread:
            # Start cycle
            self.cycleStartTime = datetime.datetime.now()
            self.db = dbConn.DbConn(self.dbPath)
            data_date, temp1, temp2, temp3, rh, light, soil, soil1, soil2, soil3 = self.db.getLatestMonitorData()
            self.db.close()
            condVals = [soil, soil1, soil2, soil3]
            coldVals = condVals.sort()
            condMedian = (condVals[1]+condVals[2])/2.0
            self.soilCond = condMedian

            if (light>self.lightThresh):
                self.controlVal = self.pid(self.soilCond)
                self.logger.debug("self.soilCond=%.1f, soilVals=(%.1f,%.1f,%.1f,%.1f)" % (self.soilCond, soil, soil1, soil2, soil3))
                # Set the cycle watering on time based on the operating mode
                if (self.opMode=="moist"):
                    self.onSecs = self.controlVal
                    self.logger.info("Cycle_Start: soilCond=%.1f, setPoint=%.1f, controlVal=%.1f" %
                      (self.soilCond, self.setPoint, self.controlVal))
                elif (self.opMode=="time"):
                    self.logger.info("Cycle_Start: onSecs="+str(self.onSecs))
                elif (self.opMode=="off"):
                    self.onSecs = 0
                else:
                    self.logger.error("Unrecognised operating mode '%s'"
                                      % self.opMode)
                    self.onSecs = 0

                # Apply some water
                if (self.onSecs>0):
                    self.waterForTime(self.onSecs)
                else:
                    self.logger.info("onSecs <= 0 secs - not watering")
                    self.writeWaterData()
            else:
                self.logger.info("Low light level so not applying water")
                self.onSecs = 0
                self.controlVal = 0
                self.writeWaterData()

            # Wait for end of cycle
            dt = datetime.datetime.now()
            while (dt - self.cycleStartTime).total_seconds() < self.cycleSecs:
                time.sleep(0.1)
                dt = datetime.datetime.now()
            self.logger.info("end of Cycle")
            if (self.DEBUG): print("_waterCtrlThread.run(): end of Cycle")
        self.logger.info("waterCtrlThread.run() - Exiting")
        self.waterOff()

    def stop(self):
        """ Stop the background thread"""
        self.logger.info("Stopping thread")
        self.runThread = False

    def writeWaterData(self):
        self.db = dbConn.DbConn(self.dbPath)
        dt = datetime.datetime.now()
        self.db.writeWaterData(dt, self.waterStatus,
                               self.onSecs,
                               self.cycleSecs,
                               self.controlVal,
                               self.setPoint,
                               self.Kp,
                               self.Ki,
                               self.Kd,
                               self.opMode,
                               self.lightThresh);
        self.db.close()

    def waterForTime(self, onSecs):
        self.writeWaterData()
        self.waterOn()
        self.waterOnTime = datetime.datetime.now()
        self.writeWaterData()
        self.logger.info("waterOn")
        # Wait for time to switch water off.
        dt = datetime.datetime.now()
        while (dt - self.waterOnTime).total_seconds() < onSecs:
            time.sleep(0.1)
            dt = datetime.datetime.now()
        self.writeWaterData()
        self.waterOff()
        self.writeWaterData()
        self.logger.info("waterOff")

        
    def waterOn(self):
        self.logger.info("waterOn()")
        if (self.DEBUG): print("_waterCtrlThread.waterOn()")
        GPIO.output(self.waterControlPin, GPIO.HIGH)
        self.waterStatus=1

    def waterOff(self):
        self.logger.info("waterOff()")
        if (self.DEBUG): print("_waterCtrlThread.waterOff()")
        GPIO.output(self.waterControlPin, GPIO.LOW)
        self.waterStatus=0


class WaterCtrlDaemon():
    '''
    Start a thread that runs in the background
    '''
    DEBUG = False
    waterCtrlThread = None

    def __init__(self,cfgObj, debug=False):
        '''
        Initialise the class using data provided in object cfgObj
        '''
        self.cfg = cfgObj
        self.logger = logging.getLogger(self.cfg['logName'])
        self.logger.info("WaterCtrlDaemon.__init__()")
        self.waterCtrlThread = _waterCtrlThread(cfgObj, debug)
        self.waterCtrlThread.daemon = True


    def start(self):
        ''' Start the background process
        '''
        print("waterCtrlDaemon.start()")
        self.logger.info("WaterCtrlDaemon.start()")
        self.waterCtrlThread.start()

    def stop(self):
        ''' Stop the background process
        '''
        print("waterCtrlDaemon.stop()")
        self.logger.info("WaterCtrlDaemon.stop()")
        self.waterCtrlThread.stop()

    def setOpMode(self,mode):
        self.logger.info("OpMode==%s" % (mode))
        self.waterCtrlThread.opMode = mode
        self.waterCtrlThread.writeWaterData()

    def setOnSecs(self, onSecs):
        print("waterCtrlDaemon.setOnSecs(%f)" % onSecs)
        self.logger.info("WaterCtrlDaemon.setOnSecs(%f)" % onSecs)
        if (self.waterCtrlThread.cycleSecs >= onSecs):
            self.waterCtrlThread.onSecs = onSecs
            self.waterCtrlThread.writeWaterData()
            return("OK")
        else:
            print("waterCtrlDaemon.setOnSecs - ERROR - onSecs must not be more than cycleSecs")
            return("ERROR")

    def setCycleSecs(self,cycleSecs):
        self.logger.info("cycleSecs==%d" % (cycleSecs))
        self.waterCtrlThread.cycleSecs = cycleSecs
        self.waterCtrlThread.writeWaterData()
        
    def setSetpoint(self,setpoint):
        self.logger.info("setpoint=%f" % setpoint)
        self.waterCtrlThread.pid.setpoint = setpoint
        self.waterCtrlThread.setPoint = setpoint
        self.waterCtrlThread.writeWaterData()

    def setGains(self,Kp,Ki,Kd):
        self.logger.info("Kp,Ki,Kd==%f,%f,%f" % (Kp,Ki,Kd))
        self.waterCtrlThread.Kp=Kp
        self.waterCtrlThread.Ki=Ki
        self.waterCtrlThread.Kd=Kd
        self.waterCtrlThread.pid.tunings=(Kp,Ki,Kd)
        self.waterCtrlThread.writeWaterData()
        
    def setKp(self,Kp):
        self.logger.info("Kp==%f" % (Kp))
        self.waterCtrlThread.Kp=Kp
        self.waterCtrlThread.pid.Kp=Kp
        self.waterCtrlThread.writeWaterData()
        
    def setKi(self,Ki):
        self.logger.info("Ki==%f" % (Ki))
        self.waterCtrlThread.Ki=Ki
        self.waterCtrlThread.pid.Ki=Ki
        self.waterCtrlThread.writeWaterData()

    def setKd(self,Kd):
        self.logger.info("Kd==%f" % (Kd))
        self.waterCtrlThread.Kd=Kd
        self.waterCtrlThread.pid.Kd=Kd
        self.waterCtrlThread.writeWaterData()

    def setLightThresh(self,lightThresh):
        self.logger.info("lightThresh==%f" % (lightThresh))
        self.waterCtrlThread.lightThresh = lightThresh
        self.waterCtrlThread.writeWaterData()

        
    def getStatus(self):
        statusObj = {}
        statusObj['opMode'] = self.waterCtrlThread.opMode
        statusObj['onSecs'] = self.waterCtrlThread.onSecs
        statusObj['cycleSecs'] = self.waterCtrlThread.cycleSecs
        statusObj['waterStatus']=self.waterCtrlThread.waterStatus
        statusObj['soilCond']=self.waterCtrlThread.soilCond
        statusObj['soilRes']=self.waterCtrlThread.soilRes
        statusObj['setPoint']=self.waterCtrlThread.pid.setpoint
        statusObj['controlVal']=self.waterCtrlThread.controlVal
        statusObj['Kp']=self.waterCtrlThread.pid.tunings[0]
        statusObj['Ki']=self.waterCtrlThread.pid.tunings[1]
        statusObj['Kd']=self.waterCtrlThread.pid.tunings[2]
        statusObj['Cp']=self.waterCtrlThread.pid.components[0]
        statusObj['Ci']=self.waterCtrlThread.pid.components[1]
        statusObj['Cd']=self.waterCtrlThread.pid.components[2]
        statusObj['lightThresh']=self.waterCtrlThread.lightThresh
        return statusObj
        
if __name__ == '__main__':
    print("waterCtrl.__main__()")

    cfgObj = {
        "logName": "waterCtrl",
        "waterControlPin": 22,
        "waterMonitorPin": 23,
        "waterCycleSecs": 5,
        "waterOnSecs": 2,
        }

    waterCtrl = WaterCtrlDaemon(cfgObj, debug=True)
    waterCtrl.start()
    time.sleep(20)
    waterCtrl.stop()
    time.sleep(10)
    print("exiting")
