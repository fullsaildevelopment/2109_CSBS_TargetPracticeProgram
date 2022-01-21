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
        buffer = 32
        self.fire = False
        self.cv = target_tracking.ComputerVision(_buffer=buffer)
        #self.mForm = Form()
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
        if values is not None:          
            y = int(values/4.615)
            if y >= 0 and y <= 70:    
              self.ppin.write(y)
              sleep(0.015)                 
              self.pdelay = True
           
        
    def cmmyaw(self, values):        
        if values is not None:            
            x = int(values/6.154)            
            x = 65-x            
            if x >= 0 and x <= 65:           
               self.ypin.write(x)
               sleep(0.015)               
               self.ydelay = True
            
            
    def cmmfire(self, values, fire, target_aquired):
        
        if values is not None:
            
            if fire and target_aquired:                
               self.uno.digital[7].write(1)               
               #print("fire ")

            else:
               self.uno.digital[7].write(0)               
               #print("No Fire")

                #self.uno.digital[8].write(0)
            #if self.ydelay==False and self.pdelay==False:
            #    self.uno.digital[8].write(0)
            #    self.uno.digital[7].write(0)
            #time.sleep(0.015)
            #else:
            #    self.uno.digital[8].write(0)
            #    self.uno.digital[7].write(0)               
            #    print("No Fire")
            #    #self.ydelay = False
            #    #self.pdelay = False

        
            
        


    