import serial
import time
import main
import struct
import target_tracking
import counter_measure
from pyfirmata import Arduino, util
from pyfirmata import Arduino, SERVO

class CMMControl:
    def __init__(self, _buffer = 64):   
        self.cv = target_tracking.ComputerVision(_buffer=128)
        self.uno = Arduino('COM5')
        self.ppin = 9
        self.ypin = 10
        self.fpin = 13
        #self.uno.digital[ppin].mode = SERVO
        #self.uno.digital[ypin].mode = SERVO
        #self.p = float(self.cv.get_targetData[0])
        #self.y = float(self.cv.get_targetData[1])
        #self.f = float(self.cv.get_targetData[2])

    def cmmpitch(self, values):
        self.uno.digital[self.ppin].mode = SERVO
        #pin9 = self.uno.get_pin('d:9:s')
        #arduino_ser = serial.Serial('COM5', 9600)
        #time.sleep(2)
        #floatbytes = struct.pack('f', values)
        self.uno.digital[self.ppin].write(values)
        #pin9.write(values)
        #arduino_ser.write(bytes(values))
        #arduino_ser.flush()
        #print(arduino_ser.readline())
    def cmmyaw(self, values):
        self.uno.digital[self.ypin].mode = SERVO
        #pin10 = self.uno.get_pin('d:10:s')
        #pin10.write(values)
        self.uno.digital[self.ypin].write(values)
    def cmmfire(self, values):
        pin13 = self.uno.get_pin('d:13:s')
        time.sleep(values/values)
        self.uno.digital[pin13].write(1)

