import serial
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
        self.uno = pyfirmata.Arduino('COM4')
        self.iter8 = pyfirmata.util.Iterator(self.uno)
        self.iter8.start()
        self.ppin = self.uno.get_pin('d:9:s')
        self.ypin = self.uno.get_pin('d:10:s')
        self.fpin = self.uno.get_pin('d:13:o')
        self.mpin = self.uno.get_pin('d:12:o')
        self.pdelay = False
        self.ydelay = False        
        self.ppin.write(45)
        self.ypin.write(40)
        self.uno.digital[8].write(1)
        

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
        #y = int(values/3.333)
        self.pdelay = False

        if values is not None:             
            y = int(values/4.286)
            
            if y >= 0 and y <= 70:    
              self.ppin.write(y)
              sleep(0.015)                    
              #print("Y Degrees= ", y)
              #print("Y Values= ", values)
              self.pdelay = True
           
        
    def cmmyaw(self, values):        
        #x = int(values/2.222)
        #print("x value",x)        
        self.ydelay = False

        if values is not None:            
            x = int(values/6.154)            
            x = 65-x            
            if x >= 0 and x <= 65:           
               self.ypin.write(x)
               sleep(0.015)                    
               #print("X Degrees= ", x)
               #print("X Values= ", values)
               self.ydelay = True
            
            
    def cmmfire(self, values):
        
        if values is not None:
            #self.uno.digital[7].write(1)
            if self.ydelay==True and self.pdelay==True: 
                #for i in range(2):                    
                    self.uno.digital[7].write(1)
                    sleep(.015)
                    print("fire ")
                    #self.uno.digital[8].write(0)
            if self.ydelay==False and self.pdelay==False:
                self.uno.digital[8].write(0)
                self.uno.digital[7].write(0)
        #time.sleep(0.015)
        #self.uno.digital[8].write(0)
        #self.uno.digital[7].write(0)
        print("No Fire")
        #self.ydelay = False
        #self.pdelay = False

        
            
        


    