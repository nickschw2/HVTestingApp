import numpy
import pyvisa as visa
import numpy as np
from config import *
from messages import *

# At  some point, make the change that we dont need to pass the brand name, and get it from IDN

class Oscilloscope():
    def __init__(self, nPoints=100000):
        self.nPoints = nPoints
        self.data = {}

        self.rm = visa.ResourceManager()
        self.connectInstrument()

        # Set LAN to static
        self.inst.write(':LAN:MAN ON')
        self.inst.write(':LAN:AUT OFF')
        self.inst.write(':LAN:DHCP OFF')
        self.inst.write(':LAN:APPL')

        self.reset()

        # Get the time scales and offsets
        self.timeScale = float(self.inst.query(':TIM:SCAL?'))
        self.timeOffset = float(self.inst.query(':TIM:OFFS?'))

        print('Oscilloscope has been initialized successfully.')

    def connectInstrument(self):
        instrumentName = self.findIPAddress()
        self.inst = self.rm.open_resource(instrumentName, timeout=5000, chunk_size=1024000, encoding='latin-1') # bigger timeout for long mem

    def findIPAddress(self):
        resources = self.rm.list_resources()
        return resources[0]

    def setScale(self, chargeVoltage, capacitance):
        RCTime = waterResistor * capacitance
        timeScale = RCTime *2
        voltageScale = chargeVoltage / 5
        currentScale = 20e3 / 500 * 0.01 / 2
        interferometerScale = 0.02 # Volts
        diamagneticScale = 1 # Volts

        # Initialize the scope view
        self.inst.write(f':TIM:SCAL {timeScale}')
        self.inst.write(f':TIM:OFFS {4 * timeScale}')

        self.inst.write(':CHAN1:DISP 1')
        self.inst.write(':CHAN2:DISP 1')
        self.inst.write(':CHAN3:DISP 1')
        self.inst.write(':CHAN4:DISP 1')

        self.inst.write(f':CHAN1:SCAL {voltageScale}')
        self.inst.write(f':CHAN1:OFFS {-1 * voltageScale}')
        self.inst.write(f':TRIG:EDGE:LEV {2 * voltageScale}')
        self.inst.write(f':CHAN2:SCAL {currentScale}')
        self.inst.write(f':CHAN2:OFFS {-0 * currentScale}')
        self.inst.write(f':CHAN3:SCAL {interferometerScale}')
        self.inst.write(f':CHAN3:OFFS {0}')
        self.inst.write(f':CHAN4:SCAL {diamagneticScale}')
        self.inst.write(f':CHAN3:OFFS {0}')

        # Get the time scales and offsets
        self.timeScale = float(self.inst.query(':TIM:SCAL?'))
        self.timeOffset = float(self.inst.query(':TIM:OFFS?'))

    # stop reading data
    def reset(self):
        # Reset the internal memory depth
        self.inst.write(':RUN')
        # self.inst.write(f'ACQ:MDEP {self.memoryDepth}')
        self.inst.write(f'ACQ:MDEP AUTO')

        self.inst.write(':CLE') # clear all waveforms from screen
        self.inst.write(':STOP') # stop running scope
        self.inst.write(':SING') # setup for single trigger event

    # pull waveform from screen
    def get_data(self, channel):
        try:
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
            print('Loading data from oscilloscope')
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
            yinc = float(wav_pre_list[7])
            yorigin = int(wav_pre_list[8])
            yref = int(wav_pre_list[9])
            dataarray = ((values - float(yref) - float(yorigin)) * float(yinc))

            # Determine how often to subsample so that the saved file is a reasonable size
            nSkip = int(np.round(stop / self.nPoints))

            self.data[channel] = dataarray[::nSkip]

        except Exception as e:
            print(e)
            self.data[channel] = np.zeros(0) # return empty array

        self.data_size = len(self.data[channel])
        return self.data[channel]

    def get_time(self):
        # Now, generate a time axis.
        timeBlocks = 5 # number of blocks on screen on time axis
        self.time = np.linspace(self.timeOffset - timeBlocks * self.timeScale, self.timeOffset + timeBlocks * self.timeScale, num=self.data_size)

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
