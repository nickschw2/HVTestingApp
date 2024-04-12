from constants import *

# Test mode for when we're not connected to the National Instruments hardware
DEBUG_MODE = False
ADMIN_MODE = True
SHOT_MODE = True
# Is the ignitron used for switching?
# If so, it will stop conducting when the current becomes too low, meaning that there is a steep drop to zero voltage when the switch reopens
IGNITRON_MODE = True
USING_SCOPE = False
POWER_SUPPLY = 'PLEIADES' # Options are ['PLEIADES', 'EB100', '20KV', 'TDK']
if POWER_SUPPLY == 'PLEIADES' or POWER_SUPPLY == 'EB-100':
    POLARITY = 'Negative'
elif POWER_SUPPLY == 'TDK':
    POLARITY = 'Positive'
else:
    print('Wrong name of Power Supply')
    POLARITY = None

# Power supply indicators
powerSupplyIndicatorLabels = {'PLEIADES': ['HV On', 'CONST HV Mode', 'CONST mA Mode', 'Interlock Closed', 'Spark', 'Over Temp Fault', 'AC Fault'],
                              'EB-100': ['HV On', 'CONST HV Mode', 'CONST mA Mode', 'Interlock Closed', 'Oil Over Temp', 'Inverter Over Temp', 'Emergency Stop', 'Short Circuit', 'Inverter Over Current', 'IGBT Fault', 'VBus Low', 'HV Switch', 'HV Fault'],
                              'TDK': ['HV On', 'CONST HV Mode', 'CONST mA Mode', 'Interlock Closed', 'Spark', 'Over Temp Fault', 'AC Fault']}
# All other indicators
indicatorLabels = ['Door Closed 1', 'Door Closed 2']

# Power supply constants
maxVoltagePowerSupply = {'PLEIADES': 100e3, 'EB-100': 100e3, 'TDK': 50e3} # V
maxCurrentPowerSupply = {'PLEIADES': 60e-3, 'EB-100': 1.0, 'TDK': 360e-3} # A
maxAnalogInput = 10 # V
systemStatus_sample_rate = 100 # Hz, rate at which the NI hardware updates the voltage

# Oscilloscope parameters
scopeChannelDefaults = {'INT01_DRIVER': '2', 'INT01': '1'}
scopeChannelOptions = ['1', '2', '3', '4']
scopeColumns = [key for key in scopeChannelDefaults]

# Working gas options
gasOptions = ['Hydrogen', 'Deuterium', 'Helium', 'Nitrogen', 'None']
primaryGasDefault = 'Deuterium'
secondaryGasDefault = 'None'

# User Inputs
userInputs = {'chargeVoltage': {'label': 'Charge Voltage (kV)',
                            'default': 20,
                            'max': maxVoltagePowerSupply[POWER_SUPPLY],
                            'min': 0},
            'primaryGasStart': {'label': 'Primary Gas Start (ms)',
                                 'default': 0,
                                 'max': 200,
                                 'min': 0},
            'primaryGasTime': {'label': 'Primary Gas Time (ms)',
                                 'default': 1,
                                 'max': 200,
                                 'min': 0},
            'secondaryGasStart': {'label': 'Secondary Gas Start (ms)',
                                 'default': 0,
                                 'max': 200,
                                 'min': 0},
            'secondaryGasTime': {'label': 'Secondary Gas Time (ms)',
                                   'default': 0,
                                   'max': 200,
                                   'min': 0},
            'ignitronDelay': {'label': 'Ignitron Delay (ms)',
                            'default': 5,
                            'max': 200,
                            'min': 0},
            'dumpDelay': {'label': 'Dump Delay (ms)',
                        'default': 50,
                        'max': 500,
                        'min': 0},
            'spectrometerDelay': {'label': 'Spectrometer Delay (ms)',
                                'default': 25,
                                'max': 500,
                                'min': 0}}

# Add inputs to saved data
userInputColumns = {variable: {'name': description['label'], 'type': 'scalar'} for variable, description in userInputs.items()}
single_columns.update(userInputColumns)

# Columns to save to master lookup files
master_columns = {}
for variable, description in single_columns.items():
    if description['type'] == 'scalar':
        master_columns[variable] = description['name']

# NI DAQ parameters
output_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
systemStatus_name = 'PXI1Slot2' # The name of the DAQ device as shown in MAX
diagnostics_name = 'PXI1Slot4' # The name of the DAQ device as shown in MAX
diagnostics2_name = 'PXI1Slot5' # The name of the DAQ device as shown in MAX
misc_name = 'PXI1Slot8' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
PFIPort1Name = 'port1'
PFIPort2Name = 'port2'

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
charge_ao_defaults = {'Voltage Set': f'{output_name}/ao0',
                      'Current Set': f'{output_name}/ao1'} # analog outputs
systemStatus_defaults = {'Power Supply Voltage': f'{systemStatus_name}/ai0',
                         'Power Supply Current': f'{systemStatus_name}/ai1',
                         'Capacitor Voltage': f'{systemStatus_name}/ai2'} # analog inputs
do_defaults = {'Dump Switch': f'{output_name}/{digitalOutName}/line0',
               'Power Supply Switch': f'{output_name}/{digitalOutName}/line1',
               'Load Switch': f'{output_name}/{digitalOutName}/line2',
               'Enable HV': f'{output_name}/{digitalOutName}/line3'}
di_defaults = {'HV On': f'{output_name}/{PFIPort1Name}/line1',
               'CONST HV Mode': f'{output_name}/{PFIPort1Name}/line2',
               'CONST mA Mode': f'{output_name}/{PFIPort2Name}/line1',
               'Interlock Closed': f'{output_name}/{PFIPort1Name}/line4',
               'Spark': f'{output_name}/{PFIPort2Name}/line2',
               'Over Temp Fault': f'{output_name}/{PFIPort1Name}/line6',
               'AC Fault': f'{output_name}/{PFIPort1Name}/line7',
               'Door Closed 1': f'{output_name}/{PFIPort2Name}/line6',
               'Door Closed 2': f'{output_name}/{PFIPort2Name}/line7'}
diagnostics_defaults = {'dischargeCurrent': f'{diagnostics_name}/ai2',
                        'DIODE02': f'{diagnostics_name}/ai0',
                        'DIODE01': f'{diagnostics_name}/ai3',
                        'DIA03': f'{diagnostics_name}/ai6',
                        'DIA04': f'{diagnostics_name}/ai7',
                        'dumpCurrent': f'{diagnostics_name}/ai4',
                        'BR03': f'{diagnostics2_name}/ai2',
                        'chamberProtectionCurrent': f'{diagnostics2_name}/ai4',
                        'feedthroughVoltage': f'{diagnostics2_name}/ai5',
                        'feedthroughCurrent': f'{diagnostics2_name}/ai6',
                        'dischargeVoltage': f'{diagnostics2_name}/ai7',
                        'ACC01': f'{diagnostics2_name}/ai0',
                        'ACC02': f'{diagnostics2_name}/ai1'}
counters_defaults = {'HE3DET01': f'{output_name}/ctr0',
                     'HE3DET02': f'{output_name}/ctr3',
                     'EXCDET01': f'{misc_name}/ctr0',
                     'EXCDET02': f'{misc_name}/ctr1',
                     'EXCDET03': f'{misc_name}/ctr2',
                     'EXCDET04': f'{misc_name}/ctr3'}
charge_ao_options = [f'{output_name}/a0{i}' for i in list(range(2))]
systemStatus_options = [f'{systemStatus_name}/ai{i}' for i in list(range(8))]
do_options = [f'{output_name}/{digitalOutName}/line{i}' for i in list(range(8))]
di_options = [f'{output_name}/{PFIPort1Name}/line{i}' for i in list(range(8))] + \
             [f'{output_name}/{PFIPort2Name}/line{i}' for i in list(range(8))]
diagnostics_options = [f'{diagnostics_name}/ai{i}' for i in list(range(8))] + \
                      [f'{diagnostics2_name}/ai{i}' for i in list(range(8))] + \
                      [f'{misc_name}/ai{i}' for i in list(range(8))]
counters_options = [f'{output_name}/ctr{i}' for i in list(range(4))] + \
                   [f'{misc_name}/ctr{i}' for i in list(range(4))]
samp_freq = 1000000 # Frequency for acquiring data [Hz]
switch_samp_freq = 1000 # Frequency for triggering switches [Hz]

analysisVariables = {'decayTime': {'label': 'Decay Time (ms)', 'factor': 1e3},
                     'stored_energy': {'label': 'Plasma Energy (J)', 'factor': 1},
                     'capacitance': {'label': 'Plasma Cap. (uF)', 'factor': 1e6},
                     'tau_M': {'label': 'RC Time (ms)', 'factor': 1e3},
                     'dumpVelocity': {'label': 'Avg. Vel. (km/s)', 'factor': 1e-3}}

# Results plot
# Create a small class to store line label and data so that the data is mutable (unlike namedtuple, for example)
class Line:
    def __init__(self, label, data):
        self.label = label
        self.data = data

# Structure for storing data to plot lines:
# {variable_name: Line(legend_entry, [])}
voltageLines = {'dischargeVoltage': Line('Voltage', []),
                'feedthroughVoltage': Line('Feedthrough', [])}
currentLines = {'dischargeCurrent': Line('Dis. Current', []),
                'feedthroughCurrent': Line('Feedthrough', []),
                'dumpCurrent': Line('Dump Current', []),
                'chamberProtectionCurrent': Line('Cham. Prot. Current', [])}
# interferometerLines = {'INT01': Line('INT01', [])}
diamagneticLines = {'DIA01': Line('DIA01', []),
                    'DIA02': Line('DIA02', []),
                    'DIA03': Line('DIA03', []),
                    'DIA04': Line('DIA04', [])}
BRLines = {'BR01': Line('BR01', []),
           'BR02': Line('BR02', []),
           'BR03': Line('BR03', []),
           'BR04': Line('BR04', [])}
DIODELines = {'DIODE01': Line('DIODE01', []),
              'DIODE02': Line('DIODE02', [])}
ACCLines = {'ACC01': Line('ACC01', []),
            'ACC02': Line('ACC02', [])}

voltageAnalysisLines = {'dischargeVoltageFiltered': Line('Voltage', []),
                        'feedthroughVoltageFiltered': Line('Feedthrough', [])}
currentAnalysisLines = {'dischargeCurrentFiltered': Line('Dis. Current', []),
                        'feedthroughCurrentFiltered': Line('Feedthrough', []),
                        'dumpCurrentFiltered': Line('Dump Current', []),
                        'chamberProtectionCurrentFiltered': Line('Cham. Prot. Current', [])}
diamagneticAnalysisLines = {'DIA01Density': Line('DIA01', []),
                            'DIA02Density': Line('DIA02', []),
                            'DIA03Density': Line('DIA03', []),
                            'DIA04Density': Line('DIA04', [])}
DIODEAnalysisLines = {'DIODE01Filtered': Line('DIODE01', []),
                      'DIODE02Filtered': Line('DIODE02', [])}
ACCAnalysisLines = {'ACC01Filtered': Line('ACC01', []),
                    'ACC02Filtered': Line('ACC02', [])}

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
cameraRecordVoltageLimit = 0.90 # fraction above which we will begin recording on remote cameras

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'neschbac']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 100.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.5
hardCloseWaitTime = 4
gasPuffWaitTime = 0.2

# Circuit constants
maxVoltage = {'LBL': 5, 'BLU': 50, 'GRA': 10, '': 'N/A'}
capacitance = 144 # uF
ballastResistance = 500 # Ohms
dumpResistance = 0.0105 / 6 # Ohms
chamberProtectionResistance = 0.029 / 6 # Ohms

post_dump_duration = 0.1 # s
pretrigger_duration = 0.02 # s
pulse_period = 10.1e-3 # s
default_pulse_width = 50e-6 # s
spectrometer_delay = 0.040 # s
n_pulses = 1 # pulses sent to the spectrometer

iotaOneCOMPort = 6

pulseGeneratorModel = 'DG645'
if pulseGeneratorModel == 'DG535':
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
    
    pulseGeneratorAddress = 15

elif pulseGeneratorModel == 'DG645':
    # Pulse generator channels SRS DG645
    # Channel layout found on page 56 of https://www.thinksrs.com/downloads/pdfs/manuals/DG645m.pdf
    pulseGeneratorChans = {'T0': 0,
                           'T1': 1,
                           'A': 2,
                           'B': 3,
                           'C': 4,
                           'D': 5,
                           'E': 6,
                           'F': 7,
                           'G': 8,
                           'H': 9}
    
    pulseGeneratorAddress = 12

# Gas puff is on T0
pulseGeneratorOutputs = {'daq': {'chan': 'T0', 'ref': 'T0', 'delay': 0},
                         'primaryGasStart': {'chan': 'A', 'ref': 'T0', 'delay': 0},
                         'primaryGasTime': {'chan': 'B', 'ref': 'A', 'delay': userInputs['primaryGasTime']['default'] / 1000},
                         'secondaryGasStart': {'chan': 'C', 'ref': 'T0', 'delay': 0},
                         'secondaryGasTime': {'chan': 'D', 'ref': 'C', 'delay': userInputs['secondaryGasTime']['default'] / 1000},
                         'ignitronDelay': {'chan': 'E', 'ref': 'T0', 'delay': userInputs['ignitronDelay']['default'] / 1000},
                         'ignitronDelayPulse': {'chan': 'F', 'ref': 'E', 'delay': default_pulse_width},
                         'dumpDelay': {'chan': 'G', 'ref': 'T0', 'delay': userInputs['dumpDelay']['default'] / 1000 + userInputs['ignitronDelay']['default'] / 1000},
                         'dumpDelayPulse': {'chan': 'H', 'ref': 'G', 'delay': default_pulse_width},}
