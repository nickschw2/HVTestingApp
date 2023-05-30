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

# Channels
''' 
HOW TO ADD NEW CHANNEL
There are a few important bits of information when assigning a new channel:
Variable name: name of the variable in the program
Channel: which analog input channel it's connected to, i.e. ai0
Description: Plan english description of variable, i.e. Discharge Current
Units: Units of variable, i.e. (V) or (A)
1. Each DAQ card port has 8 channels, if a 'default' is filled with 8 channels, add another DAQ card.
2. Add channel to 'diagnosticsN_defaults', where N is the card you're referencing
3. Add channel to a specific line group, i.e. all the diamagnetic signals are grouped together
    diamagneticLines = {'DIA01': Line('DIA01', []),
                    'DIA02': Line('DIA02', []),
                    'DIA03': Line('DIA03', []),
                    'DIA04': Line('DIA04', [])}
    (it's okay to have one channel in a line group).
4. In CMFX_App.py, change the value of 'self.resultsPlotData' to add your line group, if it is not there already.
5. In constants.py, change the value of 'single_columns' to include your channel in the following format:
    'variable_name': {'name': 'description (units)', 'type': 'array'},
'''
charge_ao_defaults = {'Power Supply Output': f'{output_name}/ao0'} # analog outputs
systemStatus_defaults = {'Power Supply Voltage': f'{systemStatus_name}/ai0',
                         'Power Supply Current': f'{systemStatus_name}/ai1',
                         'Capacitor Voltage': f'{systemStatus_name}/ai2'} # analog inputs
do_defaults = {'Load Switch': f'{output_name}/{digitalOutName}/line0',
               'Dump Switch': f'{output_name}/{digitalOutName}/line1',
               'Power Supply Switch': f'{output_name}/{digitalOutName}/line2'}
diagnostics_defaults = {'dischargeCurrent': f'{diagnostics_name}/ai0',
                        'DIA01': f'{diagnostics_name}/ai2',
                        'DIA02': f'{diagnostics_name}/ai3',
                        'DIA03': f'{diagnostics_name}/ai4',
                        'DIA04': f'{diagnostics_name}/ai6',
                        'DIODE02': f'{diagnostics_name}/ai7',
                        'BR01': f'{diagnostics2_name}/ai0',
                        'BR02': f'{diagnostics2_name}/ai1',
                        'BR03': f'{diagnostics2_name}/ai2',
                        'BR04': f'{diagnostics2_name}/ai3',
                        'dumpCurrent': f'{diagnostics2_name}/ai4',
                        'DIODE00': f'{diagnostics2_name}/ai5',
                        'DIODE01': f'{diagnostics2_name}/ai6',
                        'dischargeVoltage': f'{diagnostics2_name}/ai7'}
charge_ao_options = [f'{output_name}/a0{i}' for i in list(range(2))]
systemStatus_options = [f'{systemStatus_name}/ai{i}' for i in list(range(8))]
do_options = [f'{output_name}/{digitalOutName}/line{8}' for i in list(range(16))]
diagnostics_options = [f'{diagnostics_name}/ai{i}' for i in list(range(8))] + \
                      [f'{diagnostics2_name}/ai{i}' for i in list(range(8))]
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
# interferometerLines = {'INT01': Line('INT01', [])}
diamagneticLines = {'DIA01': Line('DIA01', []),
                    'DIA02': Line('DIA02', []),
                    'DIA03': Line('DIA03', []),
                    'DIA04': Line('DIA04', [])}
BRLines = {'BR01': Line('BR01', []),
           'BR02': Line('BR02', []),
           'BR03': Line('BR03', []),
           'BR04': Line('BR04', [])}
DIODELines = {'DIODE00': Line('DIODE00', []),
              'DIODE01': Line('DIODE01', []),
              'DIODE02': Line('DIODE02', [])}

voltageAnalysisLines = {'dischargeVoltageFiltered': Line('Voltage', [])}
currentAnalysisLines = {'dischargeCurrentFiltered': Line('Dis. Current', []),
                        'dumpCurrentFiltered': Line('Dump Current', [])}
diamagneticAnalysisLines = {'DIA01Density': Line('DIA01', []),
                            'DIA02Density': Line('DIA02', []),
                            'DIA03Density': Line('DIA03', []),
                            'DIA04Density': Line('DIA04', [])}

# Diagnostic hardware
voltageDivider = 10000 # voltage ratio in:out
voltageDivider_2 = 1000 # voltage ratio in:out
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
switchWaitTime = 0.1
hardCloseWaitTime = 4
gasPuffWaitTime = switchWaitTime

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
default_dumpDelay = 0.2 # s
ignitronDelay = 0.01 # s
gasPuffTime = 0.03 # s

duration = 0.4 # s
pulse_period = 10.1e-3 # s
pulse_width = 50e-4 # s
spectrometer_delay = 0.0 # s
n_pulses = 1 # pulses sent to the spectrometer

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
                         'gasPuffStop': {'chan': pulseGeneratorChans['B'], 'delay': gasPuffTime},
                         'load_ign': {'chan': pulseGeneratorChans['C'], 'delay': ignitronDelay},
                         'dump_ign': {'chan': pulseGeneratorChans['D'], 'delay': default_dumpDelay + ignitronDelay}}
