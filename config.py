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
scopeChannelDefaults = {'Discharge Voltage': '1', 'Trigger': '3'}
scopeChannelOptions = ['1', '2', '3', '4']

# Pulse Generator parameters
pulseGeneratorGPIBAddress = 15

# NI DAQ parameters
output_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
systemStatus_name = 'PXI1Slot2' # The name of the DAQ device as shown in MAX
diagnostics_name = 'PXI1Slot4' # The name of the DAQ device as shown in MAX
diagnostics2_name = 'PXI1Slot5' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
charge_ao_defaults = {'Power Supply Output': 'ao0'} # analog outputs
systemStatus_defaults = {'Power Supply Voltage': 'ai0',
                         'Power Supply Current': 'ai1',
                         'Capacitor Voltage': 'ai2'} # analog inputs
do_defaults = {'Load Switch': 'line0',
               'Dump Switch': 'line1',
               'Power Supply Switch': 'line2'}
diagnostics_defaults = {'dischargeCurrent': 'ai0',
                        'dumpCurrent': 'ai1',
                        'DIA01': 'ai2',
                        'DIA02': 'ai3',
                        'DIA03': 'ai4',
                        'dischargeVoltage': 'ai5',
                        'DIA04': 'ai6',
                        'trigger': 'ai7'}
diagnostics2_defaults = {'BR01': 'ai0',
                         'BR02': 'ai1',
                         'BR03': 'ai2',
                         'BR04': 'ai3'}
# diagnostics2_defaults = {}
charge_ao_options = ['ao0', 'ao1']
systemStatus_options = ['ai0', 'ai1', 'ai2', 'ai3']
do_options = ['line0', 'line1', 'line2', 'line3']
diagnostics_options = ['ai0', 'ai1', 'ai2', 'ai3', 'ai4', 'ai5', 'ai6', 'ai7']
samp_freq = 1000000 # Frequency for acquiring data [Hz]
switch_samp_freq = 1000 # Frequency for triggering switches [Hz]

# Results plot
# Create a small class to store line label and data so that the data is mutable (unlike namedtuple, for example)
class Line:
    def __init__(self, label, data):
        self.label = label
        self.data = data

# Structure for storing data to plot lines:
# {variable_name: Line(legend_entry, [])}
voltageLines = {'dischargeVoltage': Line('Voltage', [])}
currentLines = {'dischargeCurrent': Line('Dis. Current', []),
                'dumpCurrent': Line('Dump Current', [])}
interferometerLines = {'INT01': Line('INT01', []),
                       'INT02': Line('INT02', [])}
diamagneticLines = {'DIA01': Line('DIA01', []),
                    'DIA02': Line('DIA02', []),
                    'DIA03': Line('DIA03', []),
                    'DIA04': Line('DIA04', [])}
BRLines = {'BR01': Line('BR01', []),
           'BR02': Line('BR02', []),
           'BR03': Line('BR03', []),
           'BR04': Line('BR04', [])}
triggerLines = {'trigger': Line('Trigger', [])}

voltageAnalysisLines = {'dischargeVoltageFiltered': Line('Voltage', [])}
currentAnalysisLines = {'dischargeCurrentFiltered': Line('Dis. Current', []),
                        'dumpCurrentFiltered': Line('Dump Current', [])}
diamagneticAnalysisLines = {'DIA01Density': Line('DIA01', []),
                            'DIA02Density': Line('DIA02', []),
                            'DIA03Density': Line('DIA03', []),
                            'DIA04Density': Line('DIA04', [])}

# Diagnostic hardware
voltageDivider = 10000 # voltage ratio in:out
pearsonCoilDischarge = 0.01 # V/A
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
gasPuffWaitTime = 0.2

# Is the ignitron used for switching?
# If so, it will stop conducting when the current becomes too low, meaning that there is a steep drop to zero voltage when the switch reopens
ignitronInstalled = True

# Circuit constants
maxVoltage = {'LBL': 5, 'BLU': 50, 'GRA': 10, '': 'N/A'}
capacitance = 144 # uF
ballastResistance = 500 # Ohms
dumpResistance = 0.29 / 7 # Ohms

# User input validation
maxValidVoltage = min([maxVoltagePowerSupply / 1000, maxVoltage['BLU']]) # kV
maxValidGasPuff = 500 # ms
maxValidDumpDelay = maxValidGasPuff + 1000 # ms

# Discharge timing
duration = 0.4 # s
pulse_period = 10.1e-3 # s
pulse_width = 50e-6 # s
spectrometer_delay = 0 # s
n_pulses = 1 # pulses sent to the spectrometer

default_dump_time = 0.2 # s

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
pulseGeneratorOutputs = {'gasPuff': {'chan': pulseGeneratorChans['A'], 'delay': 0},
                         'daq': {'chan': pulseGeneratorChans['B'], 'delay': 0.05},
                         'trigger': {'chan': pulseGeneratorChans['C'], 'delay': 0},
                         'ignitron': {'chan': pulseGeneratorChans['D'], 'delay': default_dump_time}}
