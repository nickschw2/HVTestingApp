import pyvisa as visa
from config import *

# At  some point, make the change that we dont need to pass the brand name, and get it from IDN

class PulseGenerator():
    def __init__(self):
        self.rm = visa.ResourceManager()
        self.connectInstrument()
        print('Pulse generator has been initialized successfully.')

    def connectInstrument(self):
        instrumentName = f'GPIB0::{pulseGeneratorGPIBAddress}::INSTR'
        self.inst = self.rm.open_resource(instrumentName, timeout=5000, chunk_size=1024000) # bigger timeout for long mem

    def triggerStart(self):
        self.inst.write('SS')
        print('Pulse generator has been triggered!')

    def setDelay(self, chan, delay):
        self.inst.write(f'DT {chan},{pulseGeneratorChans["T0"]},{delay}')
        print(f'Delay on pulse generator channel {chan} has been set to {delay} s.')

    def reset(self):
        return 0
