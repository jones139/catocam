''' Dummy GPIO class so we can try out Raspberry Pi scripts on a desktop machine.'''

class GPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    def setmode(modeVal):
        print("rpiDummy.GPIO.setMode(%s)" % str(modeVal))

    def setwarnings(modeVal):
        print("rpiDummy.GPIO.setwarnings(%s)" % str(modeVal))

    def setup(pinId, modeVal):
        print("rpiDummy.GPIO.setup(%d, %s)" % (pinId, str(modeVal)))

    def output(pinId, modeVal):
        print("rpiDummy.GPIO.output(%d, %s)" % (pinId, str(modeVal)))
