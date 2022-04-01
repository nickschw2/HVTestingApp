import numpy
import matplotlib.pyplot as plot
import sys
import pyvisa as visa
import numpy as np

# At  some point, make the change that we dont need to pass the brand name, and get it from IDN

class ReadWriteScope():
    def __init__(self, brand='Rigol'):
        self.brand = brand
        self.data = {}
        # turn self.channels into list so it doesnt throw error in trying to loop through
        if not isinstance(self.channels, list):
            self.channels = [self.channels]

        self.rm = visa.ResourceManager()
        # Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
        self.instruments = self.rm.list_resources()
        usb = list(filter(lambda x: 'USB' in x, instruments))
        if len(usb) != 1:
            print('Bad instrument list', self.instruments)
            sys.exit(-1)
        self.inst = rm.open_resource(usb[0], timeout=10000, chunk_size=1024000) # bigger timeout for long mem

        # We have a LeCroy 9305 and a Rigol MSO5000 Series scope, commands differe between the two
        if self.brand = 'Rigol':
            # Auto scale everything
            self.inst.write(':AUT')

            self.sample_rate = float(self.inst.query(':ACQ:SRAT?'))

            # Get the time scales and offsets
            self.timescale = float(self.inst.query(':TIM:SCAL?'))
            self.timeoffset = float(self.inst.query(':TIM:OFFS?'))

        elif self.brand = 'LeCroy':
            # Autoscale everything
            self.inst.write('ASET')

            self.sample_rate = float(self.inst.query('SCLK?').split(' ')[1])

            # Get the time scales and offsets
            self.timescale = float(self.inst.query('TDIV?').split(' ')[1])
            self.timeoffset = float(self.inst.query('OFST?').split(' ')[1])

        else:
            raise Exception('Please provide a valid brand name of the oscilloscope')

        # Now, generate a time axis.
        timeBlocks = 5 # number of blocks on screen on time axis
        self.time = numpy.linspace(self.timeoffset - timeBlocks * self.timescale, self.timeoffset + timeBlocks * self.timescale, num=data_size)

        # See if we should use a different time axis
        if (self.time[-1] < 1e-3):
            self.time = self.time * 1e6
            self.tUnit = 'us'
        elif (self.time[-1] < 1):
            self.time = self.time * 1e3
            self.tUnit = 'ms'
        else:
            self.tUnit = 's'

    # stop reading data and scale
    def stop(self):
        # Grab the raw data from channel
        self.inst.write(':STOP')

    # pull waveform from screen
    def get_data(self, channel):
        if self.brand = 'Rigol':
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

        elif self.brand = 'LeCroy':
            offset = 2e-39
            multiplier = 1.25e-41
            self.data[channel] = (numpy.array(self.inst.query_binary_values("C2:WAVEFORM? DAT1")) - offset)/1.25e-41
