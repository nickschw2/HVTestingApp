import numpy
import matplotlib.pyplot as plot
import sys
import pyvisa as visa
import numpy as np

class ReadWriteScopeChannel():
    def __init__(self channel):
        self.channel = channel
        self.rm = visa.ResourceManager()
        # Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
        self.instruments = self.rm.list_resources()
        usb = list(filter(lambda x: 'USB' in x, instruments))
        if len(usb) != 1:
            print('Bad instrument list', self.instruments)
            sys.exit(-1)
        self.scope = rm.open_resource(usb[0], timeout=10000, chunk_size=1024000) # bigger timeout for long mem

        try:
            # Grab the raw data from channel 1
            self.scope.write(':STOP')

            # Get the time and voltage scales and offsets
            self.timescale = float(self.scope.query(':TIM:SCAL?'))
            self.timeoffset = float(self.scope.query(':TIM:OFFS?'))
            self.voltscale = float(self.scope.query(f':CHAN{self.channel}:SCAL?'))
            self.voltoffset = float(self.scope.query(f':CHAN{self.channel}:OFFS?'))

            self.scope.write(f':WAV:SOUR CHAN{self.channel}')
            self.scope.write(':WAV:MODE NORM')
            self.scope.write(':WAV:FORM ASCii')
            rawdata = self.scope.query(':WAV:DATA?')

            # Format string
            # begins with either a positive or negative number
            beginIndex = min(rawdata.find('+'), rawdata.find('-'))
            rawdata = rawdata[beginIndex:]
            rawdata = rawdata.strip() # remove endline
            self.data = np.fromstring(rawdata, dtype=float, sep=',')

            data_size = len(data)
            sample_rate = self.scope.query(':ACQ:SRAT?')
            print(f'Data size: {data_size} points, Sample rate: {sample_rate/1e6} MHz')

            self.scope.close()

        except visa.errors.VisaIOError as e:
            self.scope.close()
            print(e)

        # Now, generate a time axis.
        timeBlocks = 5 # number of blocks on screen on time axis
        self.time = numpy.linspace(self.timeoffset - timeBlocks * self.timescale, self.timeoffset + timeBlocks * self.timescale, num=data_size)

        # See if we should use a different time axis
        if (self.time[-1] < 1e-3):
            self.time = self.time * 1e6
            self.tUnit = 'uS'
        elif (self.time[-1] < 1):
            self.time = self.time * 1e3
            self.tUnit = 'mS'
        else:
            self.tUnit = 'S'
