import serial
#import Wire.h
import time
from time import sleep
import struct
import target_tracking
import pyfirmata
import math

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
       
        self.ppin.write(90)
        self.ypin.write(90)
        

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
        #y = int(values/1.667)      
        y = int(values/3.333)
        if values is not None: 
            #if y >= 0 and y <= 180:
            if y >= 0 and y <= 90:                                   
              self.ppin.write(y)
              sleep(0.015)                    
              print("Y Degrees= ", y)
              print("Y Values= ", values)
            
           
        
    def cmmyaw(self, values):        
        x = int(values/2.222)
        print("x value",x)        
        
        if values is not None:            
            if x > 90 or x < 90:
              x = 180-x
              print("x value",x)            
            else:
              x = x
            
            if x >= 0 and x <= 180:                                   
               self.ypin.write(x)
               sleep(0.015)                    
               print("X Degrees= ", x)
               print("X Values= ", values)
            
            
    def cmmfire(self, values):
        
        if values is not None:
            
            for i in range(5): 
                #self.uno.digital[self.mpin].write(1)
                #self.mpin.write(1)
                self.uno.digital[7].write(1)
                #sleep(.05)
                #sleep(values/values)
                #self.uno.digital[self.fpin].write(1)
                #self.fpin.wirte(1)
                self.uno.digital[8].write(1)
                sleep(.05)
                print("fire values ", values)
            
            sleep(0.0015)
            self.uno.digital[7].write(0)
            self.uno.digital[8].write(0)       

        
            
        


    