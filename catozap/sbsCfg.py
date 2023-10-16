
import os
import json


def loadConfig(fname = None):
    print("loadConfig - fname=%s" % fname)
    if (fname is None):
        print("Filename is None - using default configuration")
        return 0
    if (not os.path.exists(fname)):
        print("ERROR: Configuration File %s does not exist" % fname)
        exit(-1)

    inFile = open(fname,'r')
    cfgObj = json.load(inFile)
    print("cfgObj",cfgObj)
    inFile.close()
    return cfgObj
