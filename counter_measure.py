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
        # Set Up of SparkFun Ardunio Uno borard
        self.uno = pyfirmata.Arduino('COM4')
        self.iter8 = pyfirmata.util.Iterator(self.uno)
        self.iter8.start()
        # Set Up of Outputs to Turret
        self.ppin = self.uno.get_pin('d:9:s')
        self.ypin = self.uno.get_pin('d:10:s')
        self.fpin = self.uno.get_pin('d:13:o')
        self.mpin = self.uno.get_pin('d:12:o')
        # Initalizing of servos and Outputs
        self.pdelay = False
        self.ydelay = False        
        #self.ppin.write(45)
        #self.ypin.write(40)
        #self.uno.digital[8].write(1)
        self.shut_down_complete = False
        

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

    def retrain_pause(self):
        self.uno.digital[7].write(0)
        self.uno.digital[8].write(0)

    def shut_down(self):
        self.ppin.write(45)
        self.ypin.write(40)
        self.uno.digital[7].write(0)
        self.uno.digital[8].write(0)
        self.shut_down_complete = True
        sleep(3)
        self.uno.exit()
        return self.shut_down_complete

    def start_up(self):
        self.ppin.write(45)
        self.ypin.write(40)
        self.uno.digital[8].write(1)

    def cmmpitch(self, values):       
        if values is not None:          
            y = int(values/4.138)
            if y >= 0 and y <= 73:    
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

           

        
            
        


    