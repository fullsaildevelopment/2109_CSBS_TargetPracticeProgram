import serial
#import Wire.h
import time
from time import sleep
import struct
import target_tracking
import pyfirmata

class AimingCalc:
    def __init__(self):
        self.delay = 0
        self.cv = target_tracking.ComputerVision(_buffer=128)
        self.uno = pyfirmata.Arduino('COM8')
        self.iter8 = pyfirmata.util.Iterator(self.uno)
        self.iter8.start()
        self.ppin = self.uno.get_pin('d:9:s')
        self.ypin = self.uno.get_pin('d:10:s')
        self.fpin = self.uno.get_pin('d:13:o')
        self.mpin = self.uno.get_pin('d:12:o')
       
        self.fpin.write(90)
        self.ypin.write(90)
        #self.x = 0
        #self.y = 0

    def rotateServo(self,pin,angle):
        self.uno.digital[pin].write(angle)
        sleep()

    def __calabrate_delay(self):
        # move in a grid over the screen and collect average length of time in seconds to get to a position and fire
        return 1

    def set_delay(self):
        self.delay = self.__calabrate_delay()

    def get_delay(self):
        return self.delay

    def cmmpitch(self, values):        
        if values is not None:          
           #y = int(values/3.333)
           y = int(values/1.667)
           if y > 0 and y <= 180:                                   
              self.ppin.write(y)
              sleep(0.015)                    
              print("Y Degrees= ", y)
              print("Y Values= ", values)
           else:
              self.ppin.write(90)
              print("X Degrees= ",y)
              print("X Values= ", values)
           
        
    def cmmyaw(self, values):             
        if values is not None:
            #x = int(values/4.444)
            x = int(values/2.222)
            if x > 0 and x <= 180:                                   
               self.ypin.write(x)
               sleep(0.015)                    
               print("X Degrees= ", x)
               print("X Values= ", values)               
            else:
               self.ypin.write(90)
               print("X Degrees= ",x)
               print("X Values= ", values)
            
    def cmmfire(self, values):       
        self.uno.digital[mpin].write(1)
        time.sleep(values/values)
        self.uno.digital[fpin].write(1)
        time.sleep(0.25)
        self.uno.digital[fpin].write(0)
        time.sleep(0.25)
        self.uno.digital[mpin].write(0)
        


    