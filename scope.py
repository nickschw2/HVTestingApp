import pyvisa as visa
import numpy as np
import time
import sys
import traceback as tb
from config import *
from messages import *

# At  some point, make the change that we dont need to pass the brand name, and get it from IDN

class Oscilloscope():
    def __init__(self, nPoints=None, memoryDepth='1M', auto_reset=True):
        self.nPoints = nPoints
        self.memoryDepth = memoryDepth
        self.data = {}

        self.rm = visa.ResourceManager()
        self.connectInstrument()

        # Set LAN to static
        self.inst.write(':LAN:MAN ON')
        self.inst.write(':LAN:AUT OFF')
        self.inst.write(':LAN:DHCP OFF')
        self.inst.write(':LAN:APPL')

        if auto_reset:
            self.reset()

        print('Oscilloscope has been initialized successfully.')

    def connectInstrument(self):
        instrumentName = self.findIPAddress()
        self.inst = self.rm.open_resource(instrumentName, timeout=1000, chunk_size=1024000, encoding='latin-1') # bigger timeout for long mem

    def findIPAddress(self):
        resources = self.rm.list_resources()
        return resources[0]

    def setScale(self, chargeVoltage):
        timeScale = duration / 10 
        voltageScale = chargeVoltage / 5
        currentScale = chargeVoltage * 1000 / 500 * 0.01 / 20
        interferometerScale = 0.005 # Volts
        diamagneticScale = 1 # Volts

        # Initialize the scope view
        self.inst.write(f':TIM:SCAL {timeScale}')
        self.inst.write(f':TIM:OFFS {5 * timeScale}')

        self.inst.write(':CHAN1:DISP 1')
        self.inst.write(':CHAN2:DISP 1')
        self.inst.write(':CHAN3:DISP 1')
        self.inst.write(':CHAN4:DISP 1')

        self.inst.write(f':CHAN1:SCAL {voltageScale}')
        self.inst.write(f':CHAN1:OFFS {-1 * voltageScale}')
        self.inst.write(f':CHAN2:SCAL {currentScale}')
        self.inst.write(f':CHAN2:OFFS {-4 * currentScale}')
        self.inst.write(f':CHAN3:SCAL {interferometerScale}')
        self.inst.write(f':CHAN3:OFFS {0}')
        self.inst.write(f':CHAN4:SCAL {diamagneticScale}')
        self.inst.write(f':CHAN4:OFFS {0}')

        # Set up triggering
        self.inst.write(':TRIG:MODE:EDGE')
        self.inst.write(':TRIG:EDGE:SOUR CHAN4')
        self.inst.write(':TRIG:EDGE:SLOP POS')
        self.inst.write(f':TRIG:EDGE:LEV {3.5 * diamagneticScale}')

    # stop reading data
    def reset(self):
        # Reset the internal memory depth
        self.inst.write(':RUN')
        # self.inst.write(f'ACQ:MDEP {self.memoryDepth}')
        self.inst.write(f'ACQ:MDEP AUTO')

        self.inst.write(':CLE') # clear all waveforms from screen
        self.inst.write(':STOP') # stop running scope
        self.inst.write(':SING') # setup for single trigger event

        self.readSuccess = False

    # pull waveform from screen
    def get_data(self, channel):
        try:
            # # active = bool(self.inst.query(f':CHAN{channel}:DISP?').strip())
            # # print(active)
            # # # Setup scope to read
            # self.inst.write(f':WAV:SOUR CHAN{channel}')
            # self.inst.write(':WAV:MODE NORM')
            # self.inst.write(':WAV:FORM ACSii')
            # rawdata = self.inst.query(':WAV:DATA?')
            
            # # Format string
            # # begins with either a positive or negative number
            # beginIndex = min(rawdata.find('+'), rawdata.find('-'))
            # rawdata = rawdata[beginIndex:]
            # rawdata = rawdata.strip() # remove endline
            # self.data[channel] = np.fromstring(rawdata, dtype=float, sep=',')

            # Make sure oscilloscope is stopped first, if not stop it
            # OPC command is short for "Operation Complete" and ensures the scope is stopped before proceeding
            # self.inst.write('TFOR;*OPC?')
            # while not bool(self.inst.query('*OPC?').strip()):
            #     print('not complete')
            #     pass
            # print('complete')
            self.inst.write('*WAI')

            # check if channel is on
            active = bool(self.inst.query(f':CHAN{channel}:DISP?').strip())

            # Setup scope to read
            self.inst.write(f':WAV:SOUR CHAN{channel}')
            self.inst.write(':WAV:MODE RAW')
            self.inst.write(':WAV:FORM BYTE')

            ### Read data in packets ###
            start = 1 # starting index
            stop = int(float(self.inst.query(':ACQ:MDEP?').strip())) # stopping index is length of internal memory
            loopcount = 1 # initialize the loopcount
            startNum = start # initialize the start of the packet
            packetLength = 1000000 # number of samples per packet

            # Determine the number of packets to grab
            if stop - start > packetLength:
                stopnum = start + packetLength - 1
                loopcount = int(np.ceil((stop - start + 1) / packetLength))
            else:
                stopnum = stop

            # Initialize the start and stop position for the first read
            self.inst.write(f':WAV:START {startNum}')
            self.inst.write(f':WAV:STOP {stopnum}')

            # Initialize array to hold read data
            values = np.zeros(stop)
            print(f'Loading data from scope channel {channel}')
            if active:
                # loop through all the packets
                for i in range(0, loopcount):
                    values[i * packetLength:(i + 1) * packetLength] = self.inst.query_binary_values(':WAV:DATA?', datatype='B')
                    # set the next loop to jump a packet length
                    if i < loopcount - 2:
                        startnum = stopnum + 1
                        stopnum = stopnum + packetLength
                    # start and stop positions for last loop if packet is not a full size
                    else:
                        startnum = stopnum + 1
                        stopnum = stop
                    self.inst.write(f':WAV:START {startnum}')
                    self.inst.write(f':WAV:STOP {stopnum}')

                    # Progress bar
                    j = (i + 1) / loopcount
                    print('[%-20s] %d%%' % ('='*int(20 * j), 100*j), end='\r')
                print()

            # Convert from binary to actual voltages
            wav_pre_str = self.inst.query(':WAV:PRE?')
            wav_pre_list = wav_pre_str.split(',')
            self.get_parameters(wav_pre_list)

            dataarray = (values - self.yref - self.yorigin) * self.yinc
            self.lenMax = len(dataarray)

            # Determine how often to subsample so that the saved file is a reasonable size
            if self.nPoints is not None:
                self.nSkip = int(np.round(stop / self.nPoints))
                self.data[channel] = dataarray[::self.nSkip]
            else:
                self.data[channel] = dataarray

            self.readSuccess = True

        except Exception as e:
            # tb.print_tb(sys.exc_info()[2])
            print(e)
            self.data[channel] = np.array([]) # return empty array


        self.data_size = len(self.data[channel])
        
        return self.data[channel]

    def get_parameters(self, wav_pre_list):
        self.format = int(wav_pre_list[0])
        if self.format == 0:
            self.format = 'BYTE'
        elif self.format == 1:
            self.format = 'WORD'
        elif self.format == 2:
            self.format = 'ASC'

        self.type = int(wav_pre_list[1])
        if self.type == 0:
            self.type = 'NORM'
        elif self.type == 1:
            self.type = 'MAX'
        elif self.type == 2:
            self.type = 'RAW'

        self.points = int(wav_pre_list[2])
        self.count = int(wav_pre_list[3])
        self.xinc = float(wav_pre_list[4])
        self.xorigin = float(wav_pre_list[5])
        self.xref = float(wav_pre_list[6])
        self.yinc = float(wav_pre_list[7])
        self.yorigin = float(wav_pre_list[8])
        self.yref = float(wav_pre_list[9])

    def get_time(self):
        # Generate time axis based off parameters
        # breakpoint()
        # self.timeOffset = float(self.inst.query('TIM:OFFS?').strip())
        # self.timeScale = float(self.inst.query('TIM:SCAL?').strip())
        if self.readSuccess:
            self.time = np.linspace(self.xorigin, self.xorigin + (self.lenMax - 1) * self.xinc, self.data_size)
        else:
            self.time = np.array([])
        # self.time = self.time[::self.nSkip]
        # Now, generate a time axis.
        # timeBlocks = 5 # number of blocks on screen on time axis
        # self.time = np.linspace(self.timeOffset - timeBlocks * self.timeScale, self.timeOffset + timeBlocks * self.timeScale, num=self.data_size)

        try:
            # See if we should use a different time axis
            if (max(np.abs(self.time)) < 1e-3):
                self.time = self.time * 1e6
                self.tUnit = 'us'
            elif (max(np.abs(self.time)) < 1):
                self.time = self.time * 1e3
                self.tUnit = 'ms'
            else:
                self.tUnit = 's'
        except:
            self.tUnit = 's'

        return (self.time, self.tUnit)
