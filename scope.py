import numpy
import pyvisa as visa
import numpy as np
from config import *
from messages import *

# At  some point, make the change that we dont need to pass the brand name, and get it from IDN

class Oscilloscope():
    def __init__(self, brand='Rigol'):
        self.brand = brand
        self.data = {}

        self.rm = visa.ResourceManager()
        self.connectInstrument()

        # Set LAN to static
        self.inst.write(':LAN:MAN ON')
        self.inst.write(':LAN:AUT OFF')
        self.inst.write(':LAN:DHCP OFF')
        self.inst.write(':LAN:APPL')

        self.reset()

        # We have a LeCroy 9305 and a Rigol MSO5000 Series scope, commands differe between the two
        if self.brand == 'Rigol':
            # Get the time scales and offsets
            self.timeScale = float(self.inst.query(':TIM:SCAL?'))
            self.timeOffset = float(self.inst.query(':TIM:OFFS?'))

        else:
            raise Exception('Please provide a valid brand name of the oscilloscope')

        print('Oscilloscope has been initialized successfully.')

    def connectInstrument(self):
        instrumentName = self.findIPAddress()
        self.inst = self.rm.open_resource(instrumentName, timeout=5000, chunk_size=1024000, encoding='latin-1') # bigger timeout for long mem

    def findIPAddress(self):
        resources = self.rm.list_resources()
        return resources[0]

    def setScale(self, chargeVoltage, capacitance):
        RCTime = waterResistor * capacitance
        timeScale = RCTime / 2 * 0.01
        voltageScale = chargeVoltage / 5
        currentScale = 20e3 / 500 * 0.01 / 2
        interferometerScale = 0.4 #Volts

        # Initialize the scope view
        self.inst.write(f':TIM:SCAL {timeScale}')
        self.inst.write(f':TIM:OFFS {4 * timeScale}')

        self.inst.write(':CHAN1:DISP 1')
        self.inst.write(':CHAN2:DISP 1')
        self.inst.write(':CHAN3:DISP 1')

        self.inst.write(f':CHAN1:SCAL {voltageScale}')
        self.inst.write(f':CHAN1:OFFS {-1 * voltageScale}')
        self.inst.write(f':TRIG:EDGE:LEV {2 * voltageScale}')
        self.inst.write(f':CHAN2:SCAL {currentScale}')
        self.inst.write(f':CHAN2:OFFS {-0 * currentScale}')
        self.inst.write(f':CHAN3:SCAL {interferometerScale}')
        self.inst.write(f':CHAN3:OFFS {-0.3 * interferometerScale}')

        # Get the time scales and offsets
        self.timeScale = float(self.inst.query(':TIM:SCAL?'))
        self.timeOffset = float(self.inst.query(':TIM:OFFS?'))

    # stop reading data
    def reset(self):
        if self.brand == 'Rigol':
            self.inst.write(':CLE') # clear all waveforms from screen
            self.inst.write(':STOP') # stop running scope
            self.inst.write(':SING') # setup for single trigger event

    # pull waveform from screen
    def get_data(self, channel):
        if self.brand == 'Rigol':
            self.inst.write(f':WAV:SOUR CHAN{channel}')
            self.inst.write(':WAV:MODE NORM')
            self.inst.write(':WAV:FORM ASCii')
            rawdata = self.inst.query(':WAV:DATA?')

            # Format string
            # begins with either a positive or negative number
            beginIndex = min(rawdata.find('+'), rawdata.find('-'))
            rawdata = rawdata[beginIndex:]
            rawdata = rawdata.strip() # remove endline
            self.data[channel] = np.fromstring(rawdata, dtype=float, sep=',')

        self.data_size = len(self.data[channel])
        return self.data[channel]

    def get_time(self):
        # If there is no data on the scope, return empty array
        # if isinstance(self.data_size, int):
        #     return (np.array([]), 's')

        # Now, generate a time axis.
        timeBlocks = 5 # number of blocks on screen on time axis
        self.time = numpy.linspace(self.timeOffset - timeBlocks * self.timeScale, self.timeOffset + timeBlocks * self.timeScale, num=self.data_size)

        # See if we should use a different time axis
        if (self.time[-1] < 1e-3):
            self.time = self.time * 1e6
            self.tUnit = 'us'
        elif (self.time[-1] < 1):
            self.time = self.time * 1e3
            self.tUnit = 'ms'
        else:
            self.tUnit = 's'

        return (self.time, self.tUnit)
