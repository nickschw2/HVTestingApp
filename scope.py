import numpy
import matplotlib.pyplot as plot
import sys
import pyvisa as visa
import numpy as np

class ReadWriteScopeChannels():
    def __init__(self, channels):
        self.channels = channels
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
        self.scope = rm.open_resource(usb[0], timeout=10000, chunk_size=1024000) # bigger timeout for long mem

        try:
            # Grab the raw data from channel
            self.scope.write(':STOP')
            # Autoscale view
            self.scope.write(':AUT')

            self.sample_rate = self.scope.query(':ACQ:SRAT?')

            # Get the time scales and offsets
            self.timescale = float(self.scope.query(':TIM:SCAL?'))
            self.timeoffset = float(self.scope.query(':TIM:OFFS?'))
            self.data = {}
            for channel in self.channels:
                self.scope.write(f':WAV:SOUR CHAN{channel}')
                self.scope.write(':WAV:MODE NORM')
                self.scope.write(':WAV:FORM ASCii')
                rawdata = self.scope.query(':WAV:DATA?')

                # Format string
                # begins with either a positive or negative number
                beginIndex = min(rawdata.find('+'), rawdata.find('-'))
                rawdata = rawdata[beginIndex:]
                rawdata = rawdata.strip() # remove endline
                self.data[channel] = np.fromstring(rawdata, dtype=float, sep=',')

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
            self.tUnit = 'us'
        elif (self.time[-1] < 1):
            self.time = self.time * 1e3
            self.tUnit = 'ms'
        else:
            self.tUnit = 's'
