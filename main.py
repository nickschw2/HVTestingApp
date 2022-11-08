import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os
import webbrowser
import nidaqmx
import scipy.optimize, scipy.signal
from constants import *
from plots import *
from messages import *
from config import *
from scope import *
from ni_daq import *
from timer import *
from gpib import *

# Change nidaqmx read/write to this format? https://github.com/AppliedAcousticsChalmers/nidaqmxAio

# Tkinter has quite a high learning curve. If attempting to edit this source code without experience, I highly
# recommend going through some tutorials. The documentation on tkinter is also quite poor, but
# this website has the best I can find (http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm). At times you may
# need to manually go into the tkinter source code to investigate the behavior/capabilities of some code.

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # set theme
        self.tk.call('source', 'Sun-Valley-ttk-theme/sun-valley.tcl')
        self.tk.call('set_theme', 'light')

        # Change style
        style = ttk.Style(self)
        style.configure('TButton', **button_opts)
        style.configure('TCheckbutton', **text_opts)
        style.configure('TLabelframe.Label', **text_opts)

        self.configure_ui()
        self.init_ui()
        if not DEBUG_MODE:
            self.init_DAQ()
            self.init_PulseGenerator()

    def configure_ui(self):
        # set title
        self.title('HV Capacitor Testing')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.saveFolderSet = False
        # Initialize pins to default values
        self.scopePins = scopeChannelDefaults
        self.ao_Pins = ao_Defaults
        self.ai_Pins = ai_Defaults
        self.do_Pins = do_Defaults

        self.dischargeTimeUnit = 's' # arbritrarily

        self.chargeFraction = tk.DoubleVar()
        self.chargeFraction.set(0.0)

        # Row for user inputs on the top
        self.userInputs = ttk.LabelFrame(self, text='User Inputs', **frame_opts)
        self.userInputs.grid(row=0, columnspan=3, sticky='ns', pady=framePadding)

        # User input fields along with a button for setting them
        self.serialNumberLabel = ttk.Label(self.userInputs, text='Cap Serial #:', **text_opts)
        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):', **text_opts)
        self.holdChargeTimeLabel = ttk.Label(self.userInputs, text='Hold Charge (s):', **text_opts)

        self.serialNumberEntry = ttk.Entry(self.userInputs, width=userInputWidth, **entry_opts)
        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth, **entry_opts)
        self.holdChargeTimeEntry = ttk.Entry(self.userInputs, width=userInputWidth, **entry_opts)

        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, style='Accent.TButton')

        self.serialNumberLabel.pack(side='left')
        self.serialNumberEntry.pack(side='left', padx=(0, userInputPadding))
        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.holdChargeTimeLabel.pack(side='left')
        self.holdChargeTimeEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')

        # Column for labels on the left
        self.grid_columnconfigure(0, w=1)
        self.labels = ttk.LabelFrame(self, text='Capacitor State', **frame_opts)
        self.labels.grid(row=1, column=0, padx=framePadding)

        # Voltage and current are read from the power supply
        self.voltagePSText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.capacitorVoltageText = tk.StringVar()
        self.chargeStateText = tk.StringVar()
        self.countdownText = tk.StringVar()
        self.internalResistanceText = tk.StringVar()

        self.voltagePSLabel = ttk.Label(self.labels, textvariable=self.voltagePSText, **text_opts)
        self.currentPSLabel = ttk.Label(self.labels, textvariable=self.currentPSText, **text_opts)
        self.capacitorVoltageLabel = ttk.Label(self.labels, textvariable=self.capacitorVoltageText, **text_opts)
        self.chargeStateLabel = ttk.Label(self.labels, textvariable=self.chargeStateText, **text_opts)
        self.countdownLabel = ttk.Label(self.labels, textvariable=self.countdownText, **text_opts)
        self.internalResistanceLabel = ttk.Label(self.labels, textvariable=self.internalResistanceText, **text_opts)
        self.progress = ttk.Progressbar(self.labels, orient='vertical', value=0, mode='determinate', length=progressBarLength)

        self.voltagePSLabel.grid(column=0, row=0, pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.grid(column=0, row=1, pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.grid(column=0, row=2, pady=labelPadding, padx=labelPadding)
        self.chargeStateLabel.grid(column=0, row=3, pady=labelPadding, padx=labelPadding)
        self.countdownLabel.grid(column=0, row=4, pady=labelPadding, padx=labelPadding)
        self.internalResistanceLabel.grid(column=0, row=5, pady=labelPadding, padx=labelPadding)
        self.progress.grid(column=1, row=0, rowspan=6, pady=labelPadding, padx=labelPadding)

        # Row for buttons on the bottom
        self.grid_rowconfigure(2, w=1)
        self.buttons = ttk.LabelFrame(self, text='Operate Capacitor', **frame_opts)
        self.buttons.grid(row=2, columnspan=3, sticky='ns', pady=framePadding)

        # Button definitions and placement
        self.checklistButton = ttk.Button(self.buttons, text='Checklist Complete',
                                    command=self.checklist, style='Accent.TButton')
        self.chargeButton = ttk.Button(self.buttons, text='Charge',
                                    command=self.charge, style='Accent.TButton')
        self.dischargeButton = ttk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, style='Accent.TButton')
        self.emergency_offButton = ttk.Button(self.buttons, text='Emergency Off',
                                    command=self.emergency_off, style='Accent.TButton')
        self.resetButton = ttk.Button(self.buttons, text='Reset',
                                    command=self.reset, style='Accent.TButton')

        self.checklistButton.pack(side='left', padx=buttonPadding)
        self.chargeButton.pack(side='left', padx=buttonPadding)
        self.dischargeButton.pack(side='left', padx=buttonPadding)
        self.emergency_offButton.pack(side='left', padx=buttonPadding)
        self.resetButton.pack(side='left', padx=buttonPadding)

        # Menubar at the top
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Open', command=self.readResults)
        self.filemenu.add_command(label='Save Folder', command=self.setSaveLocation)
        self.filemenu.add_command(label='Set Pins', command=self.pinSelector)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Quit', command=self.on_closing)
        self.menubar.add_cascade(label='File', menu=self.filemenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label='Help', command=self.help)
        self.helpmenu.add_command(label='About...', command=self.openSite)
        self.menubar.add_cascade(label='Help', menu=self.helpmenu)

        self.config(menu=self.menubar)

        # Configure Graphs
        self.grid_rowconfigure(1, w=1)
        self.grid_columnconfigure(1, w=1)
        self.grid_columnconfigure(2, w=1)

        # Plot of charge and discharge
        # Put plots and navigation bars in their own frames
        self.chargeFrame = ttk.Frame(self)
        self.dischargeFrame = ttk.Frame(self)

        self.chargeFrame.grid(row=1, column=1, sticky='ew', padx=plotPadding)
        self.dischargeFrame.grid(row=1, column=2, sticky='ew', padx=plotPadding)

        self.chargePlot = CanvasPlot(self.chargeFrame)
        self.dischargePlot = CanvasPlot(self.dischargeFrame)

        # Create two y-axes for current and voltage
        self.chargeVoltageAxis = self.chargePlot.ax
        self.chargeCurrentAxis = self.chargePlot.ax.twinx()
        self.dischargeVoltageAxis = self.dischargePlot.ax
        self.dischargeCurrentAxis = self.dischargePlot.ax.twinx()

        self.chargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.chargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)
        self.dischargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.dischargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.chargePlot.ax.set_xlabel('Time (s)')

        self.chargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.chargeCurrentAxis.set_ylabel('Current (mA)', color=currentColor)
        self.dischargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.dischargeCurrentAxis.set_ylabel('Current (A)', color=currentColor)

        self.chargePlot.ax.set_title('Charge Plot')
        self.dischargePlot.ax.set_title('Discharge Plot')

        # Add lines to charging plot blit animation
        self.chargeVoltageLine, = self.chargeVoltageAxis.plot([],[], color=voltageColor) #Create line object on plot
        self.chargeCurrentLine, = self.chargeCurrentAxis.plot([],[], color=currentColor) #Create line object on plot
        self.capacitorVoltageLine, = self.chargeVoltageAxis.plot([],[], color=voltageColor, linestyle='--') #Create line object on plot
        self.fitVoltageLine, = self.chargeVoltageAxis.plot([],[], color=fitColor, linestyle='-') #Create line object on plot
        self.chargePlot.ax.set_xlim(0, plotTimeLimit)
        self.chargeVoltageAxis.set_ylim(0, voltageYLim)
        self.chargeCurrentAxis.set_ylim(0, currentYLim)

        # Add two lines and x axis for now
        self.bm = BlitManager(self.chargePlot.canvas, [self.chargeVoltageLine, self.chargeCurrentLine, self.capacitorVoltageLine, self.fitVoltageLine, self.chargePlot.ax.xaxis, self.chargePlot.ax.yaxis])

        # Create the legends before any plot is made
        self.chargePlot.ax.legend(handles=chargeHandles, loc='upper right')
        self.dischargePlot.ax.legend(handles=dischargeHandles, loc='upper right')

        # Add navigation toolbar to plots
        self.chargePlotToolbar = NavigationToolbar2Tk(self.chargePlot.canvas, self.chargeFrame)
        self.dischargePlotToolbar = NavigationToolbar2Tk(self.dischargePlot.canvas, self.dischargeFrame)

        self.chargePlotToolbar.update()
        self.dischargePlotToolbar.update()

        self.chargePlot.pack(side='top')
        self.dischargePlot.pack(side='top')

        self.chargePlotToolbar.pack(side='bottom')
        self.dischargePlotToolbar.pack(side='bottom')

    def init_ui(self):
        # Begin the operation of the program
        # center the app
        self.eval('tk::PlaceWindow . center')

        # Reset all fields on startup, including making a connection to NI DAQ
        self.loggedIn = False
        self.reset()

        # On startup, disable buttons until login is correct
        self.disableButtons()

        if ADMIN_MODE:
            self.loggedIn = True
            self.saveFolder = 'C:/Users/Control Room/programs/HVCapTestingApp/CMFX'
            self.saveFolderSet = True
            self.scopePins = scopeChannelDefaults
            self.ao_Pins = ao_Defaults
            self.ai_Pins = ai_Defaults
            self.do_Pins = do_Defaults

        else:
            # Prompt for login, save location, and pin selector automatically
            self.validateLogin()
            self.setSaveLocation()
            self.pinSelector()

        # If the user closes out of the application during a wait_window, no extra windows pop up
        self.update()

        self.updateChargeValues()

        self.safetyLights()

        # Initialize internalResistance to save the discharge
        self.internalResistance = np.nan
        self.internalResistanceText.set(f'R{CapacitorSuperscript}: {self.internalResistance / 1e6:.2f} M\u03A9')

    # There are two pieces of hardware important for communication with the test cart
    # The NI panel extender provides an analog output and two analog inputs to read/write to the power supply during charging
    # The Oscilloscope is triggered when the capacitor discharges and reads waveform from the discharge
    def init_DAQ(self):
        # We need both an analog input and output
        self.NI_DAQ = NI_DAQ(input_name, output_name, sample_rate, ai_channels=self.ai_Pins, ao_channels=self.ao_Pins)

        # Initialize the scope over ethernet
        try:
            self.scope = Oscilloscope()
        except visa.errors.VisaIOError:
            scopeErrorName = 'Oscilloscope Connection'
            scopeErrorText = 'Cannot connect to oscilloscope because IP address is either incorrect or not present. Please make sure instrument is on and has IP address. The IP can be found on the instrument or NI MAX.'
            scopeErrorWindow = MessageWindow(self, scopeErrorName, scopeErrorText)

            scopeErrorWindow.wait_window()

            # If the user presses the Okay button, charging begins
            if scopeErrorWindow.OKPress:
                self.on_closing()

    def init_PulseGenerator(self):
        self.pulseGenerator = PulseGenerator()

    def openSite(self):
        webbrowser.open(githubSite)

    def setSaveLocation(self):
        # Creates folder dialog for user to choose save directory
        self.saveFolder = filedialog.askdirectory(initialdir=os.path.dirname(os.path.realpath(__file__)), title='Select directory for saving results.')
        if self.saveFolder != '':
            self.saveFolderSet = True

        # If the user inputs have already been set, enable the checklist button
        if self.userInputsSet:
            self.checklistButton.configure(state='normal')

    def pinSelector(self):
        # Create popup window with fields for username and password
        self.setPinWindow = tk.Toplevel(padx=setPinsPadding, pady=setPinsPadding)
        self.setPinWindow.title('Set Pins')
        # Bring pop up to the center and top
        self.eval(f'tk::PlaceWindow {str(self.setPinWindow)} center')
        self.setPinWindow.attributes('-topmost', True)

        # This function places pin labels and dropdown menus in the popup window
        def selectPins(channelDefaults, options):
            pins = {}
            nCols, nRows = self.setPinWindow.grid_size()
            for i, channel in enumerate(channelDefaults):
                channelVariable = tk.StringVar()
                channelVariable.set(channelDefaults[channel])
                label = ttk.Label(self.setPinWindow, text=channel, **text_opts)
                drop = ttk.OptionMenu(self.setPinWindow, channelVariable, channelDefaults[channel], *options)

                label.grid(row=nRows + i, column=0, sticky='w', padx=(0, setPinsPadding))
                drop.grid(row=nRows + i, column=1, sticky='w', padx=(setPinsPadding, 0))

                pins[channel] = channelVariable

            return pins

        scopePinsOptions = selectPins(scopeChannelDefaults, scopeChannelOptions)
        ao_PinsOptions = selectPins(ao_Defaults, ao_Options)
        ai_PinsOptions = selectPins(ai_Defaults, ai_Options)
        do_PinsOptions = selectPins(do_Defaults, do_Options)

        # Button on the bottom
        nCols, nRows = self.setPinWindow.grid_size()
        buttonFrame = ttk.Frame(self.setPinWindow)
        buttonFrame.grid(row=nRows + 1, columnspan=2)

        # Once the okay button is pressed, assign the pins
        def assignPins():
            for channel in scopePinsOptions:
                self.scopePins[channel] = scopePinsOptions[channel].get()

            for channel in ao_PinsOptions:
                self.ao_Pins[channel] = ao_PinsOptions[channel].get()

            for channel in ai_PinsOptions:
                self.ai_Pins[channel] = ai_PinsOptions[channel].get()

            for channel in do_PinsOptions:
                self.do_Pins[channel] = do_PinsOptions[channel].get()

            print(self.scopePins)
            print(self.ao_Pins)
            print(self.ai_Pins)
            print(self.do_Pins)
            self.setPinWindow.destroy()

        okayButton = ttk.Button(buttonFrame, text='Set Pins', command=assignPins, style='Accent.TButton')
        okayButton.pack()

        self.setPinWindow.wait_window()

    def saveResults(self):
        # Create a unique identifier for the filename in the save folder
        # Format: date_serialNumber_runNumber.csv
        date = today.strftime('%Y%m%d')
        run = 1
        filename = f'{today}_{self.serialNumber}_{run}.csv'
        while filename in os.listdir(self.saveFolder):
            run += 1
            filename = f'{today}_{self.serialNumber}_{run}.csv'

        # These results are listed in accordance with the 'columns' variable in constants.py
        # If the user would like to add or remove fields please make those changes both here and to 'columns'
        self.results = [self.serialNumber, self.capacitance, self.equivalentSeriesResistance, self.dielectricAbsorptionRatio,
            self.polarizationIndex, self.internalResistance, self.waterResistance, self.chargeVoltage, self.holdChargeTime,
            self.chargeTime, self.chargeVoltagePS, self.chargeCurrentPS, self.capacitorVoltage, self.dischargeTime,
            self.dischargeTimeUnit, self.dischargeVoltageLoad, self.dischargeCurrentLoad, self.interferometer, self.diamagnetic]

        # Creates a data frame which is easier to save to csv formats
        results_df = pd.DataFrame([pd.Series(val) for val in self.results]).T
        results_df.columns = columns
        results_df.to_csv(f'{self.saveFolder}/{filename}', index=False)

    # Read in a csv file and plot those results
    def readResults(self):
        readFile = filedialog.askopenfilename(filetypes=[('Comma separated values', '.csv')])
        if readFile != '':
            results_df = pd.read_csv(readFile)

            # Reset program and allow user to reset
            self.reset()
            self.resetButton.configure(state='normal')

            self.serialNumber = results_df['Serial Number'].values[0]
            self.capacitance = results_df['Capacitance (uF)'].values[0]
            self.equivalentSeriesResistance = results_df['ESR (Ohms)'].values[0]
            self.dielectricAbsorptionRatio = results_df['DAR'].values[0]
            self.polarizationIndex = results_df['PI'].values[0]
            self.internalResistance = results_df['Internal Resistance (Ohms)'].values[0]
            self.waterResistance = results_df['Water Resistance (Ohms)'].values[0]
            self.chargeVoltage = results_df['Charged Voltage (kV)'].values[0]
            self.holdChargeTime = results_df['Hold Charge Time (s)'].values[0]
            self.chargeTime = results_df['Charge Time (s)'].values
            self.chargeVoltagePS = results_df['Charge Voltage PS (V)'].values
            self.chargeCurrentPS = results_df['Charge Current PS (A)'].values
            self.capacitorVoltage = results_df['Capacitor Voltage (V)'].values
            self.dischargeTime = results_df['Discharge Time'].values
            self.dischargeTimeUnit = results_df['Discharge Time Unit'].values[0]
            self.dischargeVoltageLoad = results_df['Discharge Voltage (V)'].values
            self.dischargeCurrentLoad = results_df['Discharge Current (A)'].values
            self.interferometer = results_df['Interferometer (V)'].values
            self.diamagnetic = results_df['Diamagnetic (V)'].values

            # Place values for all user inputs and plots
            self.serialNumberEntry.insert(0, self.serialNumber)
            self.chargeVoltageEntry.insert(0, self.chargeVoltage)
            self.holdChargeTimeEntry.insert(0, self.holdChargeTime)

            self.replotCharge()
            self.replotDischarge()

    def getCapacitorData(self, serialNumber):
        capacitorSpecifications = pd.read_csv(capacitorSpecificationsName)
        index = capacitorSpecifications['Serial Number'] == serialNumber
        # If serial number is not in the list, raise ValueError
        if not index.any():
            raise ValueError

        return capacitorSpecifications[capacitorSpecifications['Serial Number'] == serialNumber]

    def setUserInputs(self):
        # Try to set the user inputs. If there is a ValueError, display pop up message.
        try:
            # If there is an exception, catch where the exception came from
            self.userInputError = 'serialNumber'
            self.serialNumber = self.serialNumberEntry.get()
            self.capacitorData = self.getCapacitorData(self.serialNumber)
            self.capModel = self.serialNumber[0:3]
            # Make sure that the serial number matches the correct format, if not raise error
            if format.match(self.serialNumber) is None or self.capModel not in maxVoltage:
                raise ValueError

            self.userInputError = 'chargeVoltage'
            self.chargeVoltage = float(self.chargeVoltageEntry.get())
            if self.chargeVoltage > maxVoltage[self.capModel]:
                raise ValueError

            self.userInputError = 'holdChargeTime'
            self.holdChargeTime = float(self.holdChargeTimeEntry.get())

            self.capacitance = float(self.capacitorData['MM Capacitance (uF)']) * 1e-6
            self.equivalentSeriesResistance = float(self.capacitorData['ESR (GOhms)']) * 1e9
            self.dielectricAbsorptionRatio = float(self.capacitorData['DAR'])
            self.polarizationIndex = float(self.capacitorData['PI'])

            # Initialize the countdown time to the hold charge time until the countdown begins
            self.countdownTime = self.holdChargeTime

            self.userInputsSet = True

            # Set the scale on the oscilloscope based on inputs
            self.scope.setScale(self.chargeVoltage, self.capacitance)

            # Check if the save folder has been selected, and if so allow user to begin checklist
            if self.saveFolderSet:
                self.checklistButton.configure(state='normal')

            # Display pop up window to let user know that values have been set
            setUserInputName = 'User Inputs Set!'
            setUserInputText = 'User inputs have been set. They may be changed at any time for any subsequent run.'
            setUserInputWindow = MessageWindow(self, setUserInputName, setUserInputText)

        # Pop up window for incorrect user inputs
        except ValueError as err:
            def incorrectUserInput(text):
                incorrectUserInputName = 'Invalid Input'
                incorrectUserInputWindow = MessageWindow(self, incorrectUserInputName, text)

            # Clear the user input fields
            if self.userInputError == 'chargeVoltage':
                self.chargeVoltageEntry.delete(0, 'end')

                incorrectUserInputText = f'Please reenter a valid number for the charge voltage. The maximum voltage for this capacitor is {maxVoltage[self.capModel]} kV.'
                incorrectUserInput(incorrectUserInputText)

            elif self.userInputError == 'holdChargeTime':
                self.holdChargeTimeEntry.delete(0, 'end')

                incorrectUserInputText = 'Please reenter a valid number for the charge time.'
                incorrectUserInput(incorrectUserInputText)

            elif self.userInputError == 'serialNumber':
                self.serialNumberEntry.delete(0, 'end')

                incorrectUserInputText = 'Either the serial number does not exist or the format is invalid. Please reenter a valid serial number.'
                incorrectUserInput(incorrectUserInputText)

    # Disable all buttons in the button frame
    def disableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, ttk.Button):
                w.configure(state='disabled')

    # Enable normal operation of all buttons in the button frame
    def enableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, ttk.Button):
                w.configure(state='normal')

    # def checklist(self):
    #     # Function to determine if the checklist is complete
    #     def checklistComplete():
    #         complete = False
    #         complete = all([cb.get() for keys, cb in self.checklist_Checkbuttons.items()])
    #
    #         # Only if the user inputs are also set will the buttons be enabled
    #         if complete and self.userInputsSet and len(self.checklist_Checkbuttons) !=0:
    #             self.enableButtons()
    #
    #         self.checklist_win.destroy()
    #
    #     # Any time the checklist is opened, all buttons are disabled except for the save, help, and checklist
    #     self.disableButtons()
    #     self.checklistButton.configure(state='normal')
    #
    #     # Top level window for checklist
    #     self.checklist_win = tk.Toplevel()
    #     # Bring pop up to the center and top
    #     self.eval(f'tk::PlaceWindow {str(self.checklist_win)} center')
    #     self.checklist_win.attributes('-topmost', True)
    #
    #     # Create a Checkbutton for each item on the checklist
    #     for i, step in enumerate(checklist_steps):
    #         # A BooleanVar is linked to each Checkbutton and its state is updated any time a check is changed
    #         # The completion of the checklist is checked every time a Checkbutton value is changed
    #         self.checklist_Checkbuttons[f'c{i + 1}'] = tk.BooleanVar()
    #         button = ttk.Checkbutton(self.checklist_win, variable=self.checklist_Checkbuttons[f'c{i + 1}'], text=f'Step {i + 1}: ' + step)
    #         button.grid(row=i, column=0, sticky='w')
    #
    #     # Add okay button to close the window
    #     OKButton = ttk.Button(self.checklist_win, text='Okay', command=checklistComplete, style='Accent.TButton')
    #     OKButton.grid(row=len(checklist_steps) + 1, column=0)

    def checklist(self):
        # Any time the checklist is opened, all buttons are disabled except for the save, help, and checklist
        self.disableButtons()
        self.checklistButton.configure(state='normal')

        # Popup window appears to confirm charging
        checklistName = 'Checklist Complete?'
        checklistText = 'Has the checklist been completed?'
        checklistWindow = MessageWindow(self, checklistName, checklistText)

        checklistWindow.OKButton['text'] = 'Yes'
        cancelButton = ttk.Button(checklistWindow.bottomFrame, text='Cancel', command=checklistWindow.destroy, style='Accent.TButton')
        cancelButton.pack(side='left')

        checklistWindow.wait_window()

        if checklistWindow.OKPress and self.userInputsSet:
            self.enableButtons()

    def operateSwitch(self, switchName, state):
        # If state is false, power supply switch opens and load switch closes
        # If state is true, power supply switch closes and load switch opens
        if not DEBUG_MODE:
            try:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(f'{output_name}/{digitalOutName}/{self.do_Pins[switchName]}')
                    value = task.write(state)
                    print(f'{switchName} in {state} state')

            except Exception as e:
                print(e)
                print('Cannot operate switches')

    # Sends signal from NI analog output to charge or discharge the capacitor
    def powerSupplyRamp(self, action='discharge'):
        mapVoltage = self.chargeVoltage / maxVoltagePowerSupply * maxVoltageInput * 1000

        if action == 'charge':
            value = mapVoltage
        else:
            value = 0

        if not DEBUG_MODE:
            self.NI_DAQ.write_value(value)

    def triggerShot(self):
        # Set up a task to trigger the gating of the camera based off the pulse generator signal
        with nidaqmx.Task() as task:
            freq = 20
            duty_cycle = 0.001
            task.co_channels.add_co_pulse_chan_freq(f'{output_name}/ctr0', freq=freq, duty_cycle=duty_cycle)
            task.channels.co_pulse_term = f'/{output_name}/PFI0'

            n_pulses = 10
            task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=n_pulses)
            task.triggers.start_trigger.cfg_dig_edge_start_trig(f'/{output_name}/PFI1', trigger_edge=nidaqmx.constants.Edge.RISING)

            task.start()
            self.pulseGenerator.triggerIgnitron()
            task.wait_until_done(timeout=np.inf)

    def charge(self):
        # Popup window appears to confirm charging
        chargeConfirmName = 'Begin charging'
        chargeConfirmText = 'Are you sure you want to begin charging?'
        chargeConfirmWindow = MessageWindow(self, chargeConfirmName, chargeConfirmText)

        cancelButton = ttk.Button(chargeConfirmWindow.bottomFrame, text='Cancel', command=chargeConfirmWindow.destroy, style='Accent.TButton')
        cancelButton.pack(side='left')

        chargeConfirmWindow.wait_window()

        # If the user presses the Okay button, charging begins
        if chargeConfirmWindow.OKPress:
            self.idleMode = False

            # Operate switches
            self.operateSwitch('Load Switch', True)
            time.sleep(switchWaitTime)
            self.operateSwitch('Power Supply Switch', True)
            self.operateSwitch('Voltage Divider Switch', True)
            self.voltageDividerClosed = True
            time.sleep(switchWaitTime)

            # Actually begin charging power supply
            self.powerSupplyRamp(action='charge')

            # Begin tracking time
            self.beginChargeTime = time.time()
            self.charging = True

            # Reset the charge plot and begin continuously plotting
            self.resetChargePlot()
            # self.updateCharge()
            self.updateChargeValues()
            self.chargePress = True

    def discharge(self):
        def popup():
            # Popup window to confirm discharge
            dischargeConfirmName = 'Discharge'
            dischargeConfirmText = 'Are you sure you want to discharge?'
            dischargeConfirmWindow = MessageWindow(self, dischargeConfirmName, dischargeConfirmText)

            cancelButton = ttk.Button(dischargeConfirmWindow.bottomFrame, text='Cancel', command=dischargeConfirmWindow.destroy, style='Accent.TButton')
            cancelButton.pack(side='left')

            dischargeConfirmWindow.wait_window()

            if dischargeConfirmWindow.OKPress:
                # Operate switches
                self.operateSwitch('Power Supply Switch', False)
                time.sleep(switchWaitTime)
                self.operateSwitch('Load Switch', False)

                # Force discharge to occur
                self.powerSupplyRamp(action='discharge')

        def saveDischarge():
            # Close voltage divider and stop repeating timer
            self.operateSwitch('Voltage Divider Switch', True)
            self.voltageDividerClosed = True
            if hasattr(self, 'switchTimer'):
                self.switchTimer.stop()

            # Read from the load
            if not DEBUG_MODE:
                try:
                    self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                    self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                    self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
                    self.diamagnetic = self.scope.get_data(self.scopePins['Diamagnetic'])
                    self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()
                except visa.errors.VisaIOError:
                    self.scope.connectInstrument()
                    self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                    self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                    self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
                    self.diamagnetic = self.scope.get_data(self.scopePins['Diamagnetic'])
                    self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()
                    # self.dischargeVoltageLoad = np.array([])
                    # self.dischargeTime = np.array([])
                    # self.dischargeTimeUnit = 's'
            else:
                self.dischargeVoltageLoad, self.dischargeCurrentLoad, self.dischargeTime, self.dischargeTimeUnit = self.getDischargeTestValues()

            if len(self.dischargeTime) != 0:
                # get resistance of water resistor
                try:
                    self.internalResistance, chargeFitTime, chargeFitVoltage = self.getResistance(self.chargeTime, self.capacitorVoltage)
                    self.waterResistance, self.dischargeFitTime, self.dischargeFitVoltage = self.getResistance(self.dischargeTime, self.dischargeVoltageLoad)
                except:
                    self.internalResistance, chargeFitTime, chargeFitVoltage = (0, 0, 0)
                    self.waterResistance, self.dischargeFitTime, self.dischargeFitVoltage = (0, 0, 0)
                self.fitVoltageLine.set_data(chargeFitTime, chargeFitVoltage / 1000)
                self.waterResistance /= 1000

                # Plot results on the discharge graph and save them
                # The only time results are saved is when there is a discharge that is preceded by charge
                self.replotCharge()
                self.replotDischarge()

                self.internalResistanceText.set(f'R{CapacitorSuperscript}: {self.internalResistance / 1e6:.2f} M\u03A9')

                self.saveResults()

            else:
                print('Oscilloscope was not triggered successfully')

        if self.charging:
            if not hasattr(self, 'countdownTime') or self.countdownTime > 0.0:
                popup()
                saveDischarge()
            else:
                self.triggerShot()
                time.sleep(hardCloseWaitTime)
                self.operateSwitch('Load Switch', False)
                saveDischarge()
        else:
            popup()

        # Disable all buttons except for save and help, if logged in
        self.disableButtons()
        if self.loggedIn:
            self.resetButton.configure(state='normal')

        self.discharged = True
        self.charging = False

    def getResistance(self, time, voltage):
        # Exponential decay function that decays to 0
        def expDecay(time, m, tau, b):
            return m * np.exp(-time / tau) + b

        # Find the point at which the capacitor is isolated
        try:
            peaks, _ = scipy.signal.find_peaks(voltage, width=10)
            startIndex = peaks[-1]
        except:
            startIndex = np.where(voltage == max(voltage))[0][0]
        expVoltage = voltage[startIndex:]
        if ignitronInstalled:
            endIndex = (expVoltage < 0).argmax()
        else:
            endIndex = len(time) - 1

        expVoltage = voltage[startIndex:endIndex]
        expTime = time[startIndex:endIndex]
        nanIndices = np.isnan(expVoltage)
        zeroIndices = expVoltage == 0
        expVoltage = expVoltage[~np.logical_or(nanIndices, zeroIndices)]
        expTime = expTime[~np.logical_or(nanIndices, zeroIndices)]

        # get estimate of tau
        tauGuess = (expTime[-1] - expTime[0]) / np.log(expVoltage[0] / expVoltage[-1])

        p0 = (max(voltage) * voltageDivider, tauGuess, expVoltage[-1]) # start with values near those we expect
        try:
            params, cv = scipy.optimize.curve_fit(expDecay, expTime, expVoltage, p0) # zero the time so that initial guess can be closer
            m, tau, b = params
            fitVoltage = expDecay(expTime, m, tau, b)
        except:
            tau = 0
            fitVoltage = np.zeros(len(expTime))

        return tau / self.capacitance, expTime, fitVoltage

    # Turn on safety lights inside the control room and outside the lab
    def safetyLights(self):
        print('Turn on safety lights')

    def emergency_off(self):
        print('Emergency Off')

    def validateLogin(self):
        # If someone is not logged in then the buttons remain deactivated
        def checkLogin(event):
            # Obtain login status. To change valid usernames and password please see constants.py
            self.username = self.usernameEntry.get()
            self.password = self.passwordEntry.get()
            self.loggedIn = self.username in acceptableUsernames and self.password in acceptablePasswords

            # Once logged in, enable the save location and help buttons
            if self.loggedIn:
                self.loginWindow.destroy()

            # If incorrect username or password, create popup notifying the user
            else:
                incorrectLoginName = 'Incorrect Login'
                incorrectLoginText = 'You have entered either a wrong name or password. Please reenter your credentials or contact nickschw@umd.edu for help'
                incorrectLoginWindow = MessageWindow(self, incorrectLoginName, incorrectLoginText)

                # Clear username and password entries
                self.usernameEntry.delete(0, 'end')
                self.passwordEntry.delete(0, 'end')

        # Create popup window with fields for username and password
        self.loginWindow = tk.Toplevel(padx=loginPadding, pady=loginPadding)
        self.loginWindow.title('Login Window')

        # Center and bring popup to the top
        self.loginWindow.attributes('-topmost', True)
        self.eval(f'tk::PlaceWindow {str(self.loginWindow)} center')

        login_text = 'Please enter UMD username.'
        password_text = 'Please enter password.'
        button_text = 'Login'

        self.usernameLabel = ttk.Label(self.loginWindow, text=login_text, **text_opts)
        self.usernameEntry = ttk.Entry(self.loginWindow, **entry_opts)
        self.passwordLabel = ttk.Label(self.loginWindow, text=password_text, **text_opts)
        self.passwordEntry = ttk.Entry(self.loginWindow, show='*', **entry_opts)
        self.loginButton = ttk.Button(self.loginWindow, text=button_text, command=lambda event='Okay Press': checkLogin(event), style='Accent.TButton')

        # User can press 'Return' key to login instead of loginButton
        self.loginWindow.bind('<Return>', checkLogin)

        self.usernameLabel.pack()
        self.usernameEntry.pack()
        self.passwordLabel.pack()
        self.passwordEntry.pack()
        self.loginButton.pack()

        self.loginWindow.wait_window()

    # Special function for closing the window and program
    def on_closing(self):
        # Open power supply and voltage divider switch and close load switch
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Load Switch', False)
        self.operateSwitch('Voltage Divider Switch', False)

        if not DEBUG_MODE:
            # Stop NI communication
            self.NI_DAQ.close()

            # Close visa communication with scope
            if hasattr(self, 'scope'):
                try:
                    self.scope.inst.close()
                except visa.errors.VisaIOError:
                    pass

        # Close plots
        plt.close('all')

        # Cancel all scheduled callbacks
        for after_id in self.tk.eval('after info').split():
            self.after_cancel(after_id)

        self.quit()
        self.destroy()

    def readScope(self, channel):
        try:
            pin = self.scopePins[channel]
            value = self.scope.get_data(pin)
            if channel == 'Load Voltage':
                value *= voltageDivider
            elif channel == 'Load Current':
                value /= pearsonCoil
            else:
                print('Incorrect channel chosen')

        except:
            value = np.nan
            print('Not connected to the scope')


        return value

    def readNI(self, channel):
        try:
            values = self.NI_DAQ.read()
            value = values[channel]
            if channel == 'Power Supply Voltage':
                value *= maxVoltagePowerSupply / maxVoltageInput
            elif channel == 'Power Supply Current':
                value *= maxCurrentPowerSupply / maxVoltageInput
            else:
                print('Incorrect channel chosen')

        except Exception as e:
            value = np.nan
            print('Not connected to the NI DAQ')
            print(e)

        return value

    def getChargingTestVoltages(self):
        if hasattr(self, 'waveform') and not self.discharged and len(self.waveform) != 0:
            powerSupplyVoltage = np.abs(self.waveform[0] + (np.random.rand() - 0.5) * 0.01)
            capacitorVoltage = np.abs(self.waveform[0] + (np.random.rand() - 0.5) * 0.01)
            powerSupplyCurrent = np.random.rand() * 0.01
            values = [powerSupplyVoltage, powerSupplyCurrent, capacitorVoltage]

            # remove the first element so that the next element is acquired on the next iteration
            self.waveform = self.waveform[1:]
        else:
            powerSupplyVoltage = np.random.rand() * 0.01
            powerSupplyCurrent = np.random.rand() * 0.01
            capacitorVoltage = np.random.rand() * 0.01
            values = [powerSupplyVoltage, powerSupplyCurrent, capacitorVoltage]

        return values

    def getDischargeTestValues(self):
        time = np.linspace(0, 1, 100)
        tUnit = 's'
        voltage = self.chargeVoltage * voltageDivider * np.exp( - time / RCTime)
        current = pearsonCoil * np.exp( - time / RCTime)
        return (voltage, current, time, tUnit)

    def intermittentVoltageDivider(self):
        self.operateSwitch('Voltage Divider Switch', True)
        time.sleep(switchWaitTime)
        self.voltageDividerClosed = True

    def updateChargeValues(self):
        voltagePSPoint = np.nan
        currentPSPoint = np.nan
        self.capacitorVoltagePoint = np.nan

        # not applicable on startup
        if hasattr(self, 'NI_DAQ'):
            if not DEBUG_MODE:
                voltages = self.NI_DAQ.h_task_ai.read()
                # voltages = self.NI_DAQ.read()
                # Retrieve charging data
                # voltages = self.NI_DAQ.data
            else:
                voltages = self.getChargingTestVoltages()
            voltagePSPoint = voltages[0] * maxVoltagePowerSupply / maxVoltageInput
            currentPSPoint = (voltages[1] + 10) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason
            # voltagePSPoint = voltages[]

            # Only record the voltage when the switch is closed
            # This occurs during all of charging and intermittently when the capacitor is isolated
            if self.voltageDividerClosed:
                self.capacitorVoltagePoint = voltages[2] * voltageDivider * attenuator
                self.capacitorVoltageText.set(f'V{CapacitorSuperscript}: {np.abs(self.capacitorVoltagePoint) / 1000:.2f} kV')

        self.voltagePSText.set(f'V{PSSuperscript}: {np.abs(voltagePSPoint) / 1000:.2f} kV')
        self.currentPSText.set(f'I{PSSuperscript}: {np.abs(currentPSPoint) * 1000:.2f} mA')

        # Once the DAQ has made a measurement, open up the switch again
        if self.voltageDividerClosed and self.countdownStarted:
            self.operateSwitch('Voltage Divider Switch', False)
            self.voltageDividerClosed = False

        if not self.idleMode and self.voltageDividerClosed:
            self.progress['value'] = 100 * self.capacitorVoltagePoint / 1000 / self.chargeVoltage

        # Logic heirarchy for charge state and countdown text
        if self.discharged:
            self.chargeStateText.set('Discharged!')
            self.countdownText.set(f'Coundown: 0.0 s')
        elif self.charged:
            self.chargeStateText.set('Charged')
            self.countdownText.set(f'Coundown: {self.countdownTime:.2f} s')
        else:
            self.chargeStateText.set('Not Charged')
            self.countdownText.set('Countdown: N/A')

        if self.charging:
            self.timePoint = time.time() - self.beginChargeTime

            self.chargeTime = np.append(self.chargeTime, self.timePoint)
            self.chargeVoltagePS = np.append(self.chargeVoltagePS, voltagePSPoint)
            self.chargeCurrentPS = np.append(self.chargeCurrentPS, currentPSPoint)
            self.capacitorVoltage = np.append(self.capacitorVoltage, self.capacitorVoltagePoint)

            # Plot the new data
            self.replotCharge()

            # Voltage reaches a certain value of chargeVoltage to begin countown clock
            if self.capacitorVoltagePoint >= chargeVoltageLimit * self.chargeVoltage * 1000 or self.countdownStarted:
                # Start countdown only once
                if not self.countdownStarted:
                    self.countdownTimeStart = time.time()
                    self.charged = True
                    self.countdownStarted = True

                    # Open power supply switch
                    self.operateSwitch('Power Supply Switch', False)

                    # Actually begin discharging power supply
                    time.sleep(0.5) # allow some time for power supply switch to open
                    self.powerSupplyRamp(action='discharge')

                    if not DEBUG_MODE:
                        # Start repeated timer to measure capacitor at regular intervals
                        self.switchTimer = RepeatedTimer(measureInterval, self.intermittentVoltageDivider)

                # Time left before discharge
                self.countdownTime = self.holdChargeTime - (time.time() - self.countdownTimeStart)

                # Set countdown time to 0 seconds once discharged
                if self.countdownTime <= 0.0:
                    self.countdownTime = 0.0
                    self.countdownStarted = False
                    self.discharge()

            # # Discharge if the voltage is not increasing
            # # This is determined if the charge does not exceed a small percentage of the desired charge voltage within a given period of time
            # notCharging = voltagePSPoint <= epsilonDesiredChargeVoltage * self.chargeVoltage and self.timePoint > chargeTimeLimit
            # if notCharging:
            #     self.discharge()
            #     print('Not charging')
            #
            # # Also discharge if charging but not reaching the desired voltage
            # # This is determined by checking for steady state
            # # In the future it would be better to implement a more rigorous statistical test, like the student t
            # steadyState = False
            # window = 20 # number of points at the end of the data set from which to calculate slope
            # nWindows = 10 # number of windows to implement sliding window
            # lengthArray = len(self.chargeTime)
            # slopes, _ = np.array([np.polyfit(self.chargeTime[lengthArray - window - i:lengthArray - i], self.chargeVoltagePS[lengthArray - window - i:lengthArray - i], 1) for i in range(nWindows)]).T # first order linear regression
            # steadyState = np.std(slopes) / np.mean(slopes) < 0.05
            # if steadyState:
            #     self.discharge()
            #     print('Steady state reached without charging to desired voltage')

        self.after(int(1000 / refreshRate), self.updateChargeValues)

    # Removes all lines from a figure
    def clearFigLines(self, fig):
        axes = fig.axes
        for axis in axes:
            if len(axis.lines) != 0:
                for i in range(len(axis.lines)):
                    axis.lines[0].remove()

    def replotCharge(self):
        self.chargeVoltageLine.set_data(self.chargeTime, self.chargeVoltagePS / 1000)
        self.chargeCurrentLine.set_data(self.chargeTime, self.chargeCurrentPS * 1000)

        nanIndices = np.isnan(self.capacitorVoltage)
        self.capacitorVoltageLine.set_data(self.chargeTime[~nanIndices], self.capacitorVoltage[~nanIndices] / 1000)

        if self.timePoint > plotTimeLimit:
            self.chargePlot.ax.set_xlim(self.timePoint - plotTimeLimit, self.timePoint)
        else:
            self.chargePlot.ax.set_xlim(0, plotTimeLimit)

        if len(self.capacitorVoltage) != 0 and 1.2 * max(self.chargeVoltagePS) / 1000 > voltageYLim:
            self.chargePlot.ax.set_ylim(0, 1.2 * max(self.chargeVoltagePS) / 1000)

        self.bm.update()


        # # Remove lines every time the figure is plotted
        # self.clearFigLines(self.chargePlot.fig)
        #
        # # Add plots
        # self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltagePS / 1000, color=voltageColor, linestyle='--')
        # self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentPS, color=currentColor, linestyle='--')
        # self.chargePlot.updatePlot()

    def replotDischarge(self):
        # Remove lines every time the figure is plotted
        self.clearFigLines(self.dischargePlot.fig)
        self.dischargeVoltageAxis.set_xlabel(f'Time ({self.dischargeTimeUnit})')

        # Add plots
        self.dischargeVoltageAxis.plot(self.dischargeTime, self.dischargeVoltageLoad / 1000, color=voltageColor, label='V$_{load}$')
        self.dischargeCurrentAxis.plot(self.dischargeTime, self.dischargeCurrentLoad, color=currentColor, label='I$_{load}$')
        self.dischargeVoltageAxis.plot(self.dischargeFitTime, self.dischargeFitVoltage / 1000, color=fitColor, label='V$_{fit}$')
        self.dischargePlot.updatePlot()

    def resetChargePlot(self):
        # Set time and voltage to empty array
        self.chargeTime = np.array([])
        self.chargeVoltagePS = np.array([])
        self.chargeCurrentPS = np.array([])
        self.capacitorVoltage = np.array([])
        self.chargeFitTime = np.array([])
        self.chargeFitVoltage = np.array([])

        self.fitVoltageLine.set_data(self.chargeFitTime, self.chargeFitVoltage / 1000)

        # Also need to reset the twinx axis
        # self.chargeCurrentAxis.relim()
        # self.chargeCurrentAxis.autoscale_view()

        self.timePoint = 0
        self.capacitorVoltagePoint = 0
        self.replotCharge()

    def resetDischargePlot(self):
        # Set time and voltage to empty array
        self.dischargeTime = np.array([])
        self.dischargeFitTime = np.array([])
        self.dischargeVoltageLoad = np.array([])
        self.dischargeCurrentLoad = np.array([])
        self.dischargeFitVoltage = np.array([])

        # Also need to reset the twinx axis
        self.dischargeCurrentAxis.relim()
        self.dischargeCurrentAxis.autoscale_view()

        self.replotDischarge()

    def reset(self):
        # Clear all user inputs
        self.serialNumberEntry.delete(0, 'end')
        self.chargeVoltageEntry.delete(0, 'end')
        self.holdChargeTimeEntry.delete(0, 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.countdownStarted = False
        self.idleMode = True
        self.checklist_Checkbuttons = {}

        # Close voltage divider
        self.operateSwitch('Voltage Divider Switch', True)
        self.voltageDividerClosed = True

        # Reset plots
        self.resetChargePlot()
        self.resetDischargePlot()

        # Disable all buttons if logged in
        self.disableButtons()

        if hasattr(self, 'scope'):
            self.scope.reset() # Reset the scope

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
