import time
import math
import sys
import glob
import serial
import serial.tools.list_ports
import time
import serial
import io
import os
import pandas as pd
import csv
import numpy as np
import PyTrinamic
from PyTrinamic.connections.ConnectionManager import ConnectionManager
from PyTrinamic.evalboards.TMC5160_eval import TMC5160_eval
connectionManager = ConnectionManager()
myInterface = connectionManager.connect()
PyTrinamic.showInfo()
TMC5160 = TMC5160_eval(myInterface)
TMC5160.showChipInfo()
DEFAULT_MOTOR = 0
print("Preparing parameters")
TMC5160.writeRegister(TMC5160.registers.A1, 5000)
TMC5160.writeRegister(TMC5160.registers.V1, 15000)
TMC5160.writeRegister(TMC5160.registers.D1, 100000)
TMC5160.writeRegister(TMC5160.registers.DMAX, 100000)
TMC5160.writeRegister(TMC5160.registers.VMAX, 100000)
TMC5160.writeRegister(TMC5160.registers.VSTART, 0)
TMC5160.writeRegister(TMC5160.registers.VSTOP, 10)
TMC5160.writeRegister(TMC5160.registers.AMAX, 5000)
TMC5160.writeRegister(TMC5160.registers.IHOLD_IRUN, 0x00070402)
micval = 0


def findDevice(search):
    ports = serial.tools.list_ports.comports()
    for address, desc, hwid in sorted(ports):
        if search in hwid:
            print("Selected Device: " + desc + address)
            return address
        else:
            pass


def requestPos(device):
    t0 = time.time()
    device.write(bytes("?\r", 'ascii'))
    readoutput = device.read_until(b'\r', size=None)
    t1 = time.time()
    tdelta = round(t1 - t0, 6)
    return readoutput, tdelta

def mov(pos):
    while True:
        TMC5160.moveTo(DEFAULT_MOTOR, pos, 1000000)
        if TMC5160.getAxisParameter(TMC5160.APs.ActualPosition, DEFAULT_MOTOR) == pos:
            TMC5160.stop(DEFAULT_MOTOR)
            return



micrometerSerial = serial.Serial(findDevice(
    "AL4H5UG0A"), baudrate=19200, timeout=1, parity=serial.PARITY_EVEN, bytesize=7, stopbits=2)


TMC5160.stop(DEFAULT_MOTOR)
unit = input("Enter unit number: ")

with open(unit + ".csv", "r") as cycles:
    counter = cycles.readline()
    counter = int(counter)
    print(counter)
    cycles.close()


if micrometerSerial.isOpen():

    mov(0)
    debounce = False  
    localdebounce = False
    micrometerSerial.write(bytes("COR OFF\r", 'ascii'))
    micrometerSerial.write(bytes("MCOR 0\r", 'ascii'))
    micrometerSerial.write(bytes("COR ON\r", 'ascii'))

    while micrometerSerial.isOpen():
        micValue = requestPos(micrometerSerial)
        try:
            micFloat = (float(str(micValue[0].strip().decode('utf-8')).strip("+")))
            if(micFloat > 21) and (debounce == True): 
                mov(0)
                debounce = False 

                print(counter)
                counter = counter + 1
                with open(unit +".csv", "w") as cycles:    
                    cycles.writelines(str(counter))
                    cycles.close()
                
            elif(micFloat < 10) and (debounce == False):
                if(micFloat > 0.2):
                    if (localdebounce == False):
                        gap = micFloat
                        print(gap)
                        localdebounce = True
                    TMC5160.rotate(DEFAULT_MOTOR, -250000)
                else:
                    TMC5160.stop(DEFAULT_MOTOR)
                    TMC5160.setAxisParameter(TMC5160.APs.ActualPosition, DEFAULT_MOTOR, 0)
                    time.sleep(1)
                    mov(2500000)
                    debounce = True
                    localdebounce = False
        except:
            continue
