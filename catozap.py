#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
from threading import Thread

class CatoZap:
    def __init__(self, pinLst):
        self.pinLst = pinLst
        self.startFiring = False
        self.shutdown = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pinNo in self.pinLst:
            GPIO.setup(pinNo, GPIO.OUT)
            GPIO.output(pinNo, GPIO.LOW)
            
        
    def _fire(self):
        print("CatoZap._fire()")
        try:
            GPIO.output(self.pinLst[0], GPIO.HIGH)
            for pinNo in self.pinLst[1:]:
                GPIO.output(pinNo, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(pinNo, GPIO.LOW)
            time.sleep(0.2)
            GPIO.output(self.pinLst[0], GPIO.LOW)
            print("CatoZap._fire() - water off")
        except:
            print("CatoZap._fire() - exception - calling stopFiring()")
            self.stopFiring()
            raise

    def stopFiring(self):
        ''' Shut down the water - should be called if an exception is raised
        such as a keyboard interrupt so that we exit with the water off.
        '''
        print("Catozap.stopFiring()")
        for pinNo in self.pinLst:
            GPIO.output(pinNo, GPIO.LOW)
        

    def zapLoop(self):
        print("CatoZap.zapLoop()")
        while(1):
            if self.startFiring:
                self.startFiring = False
                self._fire()
            if self.shutdown:
                break
        print("CatoZap.zapLoop exiting")
        
    def start(self):
        ''' Run the zapLoop() function in a background thread - it waits
        for the fire() function to be called to initiate the firing
        sequence.
        '''
        print("CatoZap.start()")
        self.thread = Thread(target=self.zapLoop)
        self.thread.start()

    def stop(self):
        print("CatoZap.stop()")
        self.shutdown = True
        print("CatoZap.stop() - waiting for zapLoop to exit...")
        self.thread.join()
        
    def fire(self):
       self.startFiring = True       
        
    

if __name__ == "__main__":
    print("catozap main()")
    cz = CatoZap([17, 27, 22])

    cz.start()

    cz.fire()

    print("sleeping")
    time.sleep(3)
    print("shutting down cz")
    cz.stop()
    print("finished..")
