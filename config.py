# Test mode for when we're not connected to the National Instruments hardware
DEBUG_MODE = False
ADMIN_MODE = True
SHOT_MODE = True

# Power supply constants
maxVoltagePowerSupply = 20e3 # V
maxCurrentPowerSupply = 15e-3 # A
maxVoltageInput = 10 # V
systemStatus_sample_rate = 100 # Hz, rate at which the NI hardware updates the voltage

# Oscilloscope parameters
scopeChannelDefaults = {'Discharge Voltage': '1', 'Discharge Current': '4', 'Trigger': '3', 'Interferometer': '2'}
scopeChannelOptions = ['1', '2', '3', '4']

# Pulse Generator parameters
pulseGeneratorGPIBAddress = 2

# NI DAQ parameters
output_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
systemStatus_name = 'PXI1Slot2' # The name of the DAQ device as shown in MAX
discharge_name = 'PXI1Slot4' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
charge_ao_defaults = {'Power Supply Output': 'ao0'} # analog outputs
systemStatus_defaults = {'Power Supply Voltage': 'ai0',
    'Power Supply Current': 'ai1',
    'Capacitor Voltage': 'ai2'} # analog inputs
do_defaults = {'Load Switch': 'line0',
    'Power Supply Switch': 'line1',
    'Dump Switch': 'line2'}
diagnostics_defaults = {'Current': 'ai0',
    'Interferometer': 'ai1'}
charge_ao_options = ['ao0', 'ao1']
systemStatus_options = ['ai0', 'ai1', 'ai2', 'ai3']
do_options = ['line0', 'line1', 'line2', 'line3']
diagnostics_options = ['ai0', 'ai1', 'ai2', 'ai3']
maxDischargeFreq = int(250000 / len(diagnostics_defaults)) # Hz

# Results plot
# Create a small class to store line label and data so that the data is mutable (unlike namedtuple, for example)
class Line:
    def __init__(self, label, data):
        self.label = label
        self.data = data

dischargeLines = {'dischargeVoltage': Line('Voltage', []), 'dischargeCurrent': Line('Current', [])}
interferometerLines = {'interferometer': Line('Central', [])}
diamagneticLines = {'diamagneticAxial': Line('Axial', []),'diamagneticRadial': Line('Radial', [])}

# Diagnostic hardware
voltageDivider = 1000 # voltage ratio in:out
attenuator = 19.3 # attenuate voltage on end of capacitor input, this was calibrated for specific voltage divider
pearsonCoil = 0.01 # V/A
# Changing waterResistor temporarily to match plasma
waterResistor = 500 # Ohms
measureInterval = 5 # time between capacitor voltage measurements in seconds

# Testing constants
RCTime = 0.2 # seconds

# Charging constants
chargeTimeLimit = 10 # seconds
epsilonDesiredChargeVoltage = 0.05 # Unitless, fraction of desired charge that will trigger a discharge if the capacitor is not charging
chargeVoltageLimit = 0.95 # fraction above which the capacitor will be considered charged to the desired charge

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 100.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.2
hardCloseWaitTime = 4
gasPuffWaitTime = 0.4

# Is the ignitron used for switching?
# If so, it will stop conducting when the current becomes too low, meaning that there is a steep drop to zero voltage when the switch reopens
ignitronInstalled = True

# Circuit constants
maxVoltage = {'LBL': 5, 'BLU': 50, 'GRA': 10, '': 'N/A'}
capacitance = 72 # uF
ballastResistance = 500 # Ohms
dumpResistance = 0.29 / 7 # Ohms

# User input validation
maxValidVoltage = min([maxVoltagePowerSupply / 1000, maxVoltage['BLU']]) # kV
maxValidGasPuff = 500 # ms
maxValidDumpDelay = maxValidGasPuff + 1000 # ms

# Discharge timing
duration = 0.7 # s
pulse_period = 10.1e-3 # s
pulse_width = 50e-6 # s
spectrometer_delay = 0 # s

# Pulse generator channels SRS DG535
# Channel layout found on page ix of https://www.thinksrs.com/downloads/pdfs/manuals/DG535m.pdf
pulseGeneratorChans = {'Trigger Input': 0,
                          'T0': 1,
                          'A': 2,
                          'B': 3,
                          'AB': 4,
                          'C': 5,
                          'D': 6,
                          'CD': 7}

# Gas puff is on T0
pulseGeneratorOutputs = {'daq': {'chan': pulseGeneratorChans['A'], 'delay': 0},
                         'loadIgnitron': {'chan': pulseGeneratorChans['B'], 'delay': 495e-3},
                         'scopeTrigger': {'chan': pulseGeneratorChans['C'], 'delay': 0},
                         'dumpIgnitron': {'chan': pulseGeneratorChans['D'], 'delay': 300e-3}}
