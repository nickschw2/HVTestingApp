import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os
import webbrowser
from constants import *
from plots import *
from messages import *
from config import *
from scope import *

# Change nidaqmx read/write to this format? https://github.com/AppliedAcousticsChalmers/nidaqmxAio

# Tkinter has quite a high learning curve. If attempting to edit this source code without experience, I highly
# recommend going through some tutorials. The documentation on tkinter is also quite poor, but
# this website has the best I can find (http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm). At times you may
# need to manually go into the tkinter source code to investigate the behavior/capabilities of some code.

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # set theme
        self.tk.call('source', 'Sun-Valley-ttk-theme-master/sun-valley.tcl')
        self.tk.call('set_theme', 'light')

        # Change style
        style = ttk.Style(self)
        style.configure('TButton', **button_opts)
        style.configure('TCheckbutton', **text_opts)
        style.configure('TLabelframe.Label', **text_opts)

        self.configure_ui()
        self.init_ui()
        # self.init_DAQ()

    def configure_ui(self):
        # set title
        self.title('HV Capacitor Testing')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.saveFolderSet = False
        # Initialize pins to default values
        self.inputPins = inputPinDefaults
        self.outputPins = outputPinDefaults
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

        # Voltage and current are read from both the power supply and the load
        self.voltageLoadText = tk.StringVar()
        self.voltagePSText = tk.StringVar()
        self.currentLoadText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.chargeStateText = tk.StringVar()
        self.countdownText = tk.StringVar()

        self.voltageLoadLabel = ttk.Label(self.labels, textvariable=self.voltageLoadText, **text_opts)
        self.voltagePSLabel = ttk.Label(self.labels, textvariable=self.voltagePSText, **text_opts)
        self.currentLoadLabel = ttk.Label(self.labels, textvariable=self.currentLoadText, **text_opts)
        self.currentPSLabel = ttk.Label(self.labels, textvariable=self.currentPSText, **text_opts)
        self.chargeStateLabel = ttk.Label(self.labels, textvariable=self.chargeStateText, **text_opts)
        self.countdownLabel = ttk.Label(self.labels, textvariable=self.countdownText, **text_opts)
        self.progress = ttk.Progressbar(self.labels, orient='vertical', value=0, mode='determinate', length=progressBarLength)

        self.voltageLoadLabel.grid(column=0, row=0, pady=labelPadding, padx=labelPadding)
        self.voltagePSLabel.grid(column=0, row=1, pady=labelPadding, padx=labelPadding)
        self.currentLoadLabel.grid(column=0, row=2, pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.grid(column=0, row=3, pady=labelPadding, padx=labelPadding)
        self.chargeStateLabel.grid(column=0, row=4, pady=labelPadding, padx=labelPadding)
        self.countdownLabel.grid(column=0, row=5, pady=labelPadding, padx=labelPadding)
        self.progress.grid(column=1, row=0, rowspan=6, pady=labelPadding, padx=labelPadding)

        # Row for buttons on the bottom
        self.grid_rowconfigure(2, w=1)
        self.buttons = ttk.LabelFrame(self, text='Operate Capacitor', **frame_opts)
        self.buttons.grid(row=2, columnspan=3, sticky='ns', pady=framePadding)

        # Button definitions and placement
        self.checklistButton = ttk.Button(self.buttons, text='Begin Checklist',
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
        self.chargePlot = CanvasPlot(self)
        self.dischargePlot = CanvasPlot(self)

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
        self.chargeCurrentAxis.set_ylabel('Current (A)', color=currentColor)
        self.dischargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.dischargeCurrentAxis.set_ylabel('Current (A)', color=currentColor)

        self.chargePlot.ax.set_title('Charge Plot')
        self.dischargePlot.ax.set_title('Discharge Plot')

        # Create the legends before any plot is made
        self.chargePlot.ax.legend(handles=chargeHandles, loc='lower left')
        self.dischargePlot.ax.legend(handles=dischargeHandles, loc='lower left')

        self.chargePlot.grid(row=1, column=1, sticky='ew', padx=plotPadding)
        self.dischargePlot.grid(row=1, column=2, sticky='ew', padx=plotPadding)

    def init_ui(self):
        # Begin the operation of the program
        # center the app
        self.eval('tk::PlaceWindow . center')

        # Reset all fields on startup, including making a connection to NI DAQ
        self.loggedIn = False
        self.reset()

        # On startup, disable buttons until login is correct
        self.disableButtons()
        self.validateLogin()

        # If the user closes out of the application during a wait_window, no extra windows pop up
        self.update()

        # Prompt save location automatically
        self.setSaveLocation()

        # Try setting the pins automatically
        self.pinSelector()

        self.safetyLights()

    def init_DAQ():
        voltages = []
        frequencies = []
        shifts = []
        output_states = []

        for ch in inputPinDefaults:
            branch = "Output " + ch
            voltages.append(
                self.channel_param_tree.get_param_value(branch, "Voltage RMS")
            )
            frequencies.append(
                self.channel_param_tree.get_param_value(branch, "Frequency")
            )
            shifts.append(
                self.channel_param_tree.get_param_value(branch, "Phase Shift")
            )
            output_states.append(
                self.channel_param_tree.get_param_value(branch, "Toggle Output")
            )

        self.legend.update_rms_params(
            sample_rate=self.setting_param_tree.get_param_value(
                "Reader Config", "Sample Rate"
            )
        )

        # When NI instrument is attached
        if not DEBUG_MODE:
            # initiate read threads for analog input
            sample_rate = 10 # Hz
            sample_size = 1000 # buffer size, need to obtain default value
            channels = [key in outputPinDefaults]
            dev_name = sensorName
            self.read_thread = SignalReader(sample_rate, sample_size, channels, dev_name)
            self.read_thread.start()

            # initiate writer for analog output
            # not handled on separate thread b/c not blocking

            self.writer = SignalWriterDAQ(
                voltages=voltages,
                frequencies=frequencies,
                shifts=shifts,
                output_states=output_states,
                sample_rate=sample_rate,
                sample_size=sample_size,
                channels=[key in inputPinDefaults],
                dev_name=sensorName
            )
            self.writer.create_task()

        # Debugging on computer without NI instrument
        else:
            # Use software signal generator and read from that
            # Plot is displaying the samples and rate at which the real
            # signal generator would write to the output DAQ
            self.writer = SignalGeneratorBase(
                voltages=voltages,
                frequencies=frequencies,
                shifts=shifts,
                output_states=output_states,
                sample_rate=sample_rate,
                sample_size=sample_size
            )

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

        inputPins = selectPins(inputPinDefaults, inputPinOptions)
        outputPins = selectPins(outputPinDefaults, outputPinOptions)

        # Button on the bottom
        nCols, nRows = self.setPinWindow.grid_size()
        buttonFrame = ttk.Frame(self.setPinWindow)
        buttonFrame.grid(row=nRows + 1, columnspan=2)

        # Once the okay button is pressed, assign the pins
        def assignPins():
            for channel in inputPins:
                self.inputPins[channel] = inputPins[channel].get()

            for channel in outputPins:
                self.outputPins[channel] = outputPins[channel].get()

            print(self.inputPins)
            print(self.outputPins)
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
        self.results = [self.serialNumber, self.chargeVoltage, self.holdChargeTime,
            self.chargeTime, self.chargeVoltagePS, self.chargeVoltageLoad, self.chargeCurrentPS,
            self.chargeCurrentLoad, self.dischargeTime, self.dischargeTimeUnit, self.dischargeVoltageLoad, self.dischargeCurrentLoad]

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

            self.serialNumber = results_df['Serial Number'].dropna().values[0]
            self.chargeVoltage = results_df['Charged Voltage (kV)'].dropna().values[0]
            self.holdChargeTime = results_df['Hold Charge Time (s)'].dropna().values[0]
            self.chargeTime = results_df['Charge Time (s)'].dropna().values
            self.chargeVoltagePS = results_df['Charge Voltage PS (V)'].dropna().values
            self.chargeVoltageLoad = results_df['Charge Voltage Load (V)'].dropna().values
            self.chargeCurrentPS = results_df['Charge Current PS (A)'].dropna().values
            self.chargeCurrentLoad = results_df['Charge Current Load (A)'].dropna().values
            self.dischargeTime = results_df['Discharge Time'].dropna().values
            self.dischargeTime = results_df['Discharge Time Unit'].dropna().values[0]
            self.dischargeTimeUnit = results_df['Discharge Time (s)'].dropna().values
            self.dischargeVoltageLoad = results_df['Discharge Voltage (V)'].dropna().values
            self.dischargeCurrentLoad = results_df['Discharge Current (A)'].dropna().values

            # Place values for all user inputs and plots
            self.serialNumberEntry.insert(0, self.serialNumber)
            self.chargeVoltageEntry.insert(0, self.chargeVoltage)
            self.holdChargeTimeEntry.insert(0, self.holdChargeTime)

            self.replotCharge()
            self.replotDischarge()

    def setUserInputs(self):
        # Try to set the user inputs. If there is a ValueError, display pop up message.
        try:
            # If there is an exception, catch where the exception came from
            self.userInputError = 'serialNumber'
            self.serialNumber = self.serialNumberEntry.get()
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

            # Initialize the countdown time to the hold charge time until the countdown begins
            self.countdownTime = self.holdChargeTime

            self.userInputsSet = True

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

                incorrectUserInputText = 'Please reenter a valid format for serial number.'
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

    # Every time an item on the checklist is ticked complete, check to see if the entire list is complete
    def checklistComplete(self):
        complete = False
        complete = all([cb.get() for keys, cb in self.checklist_Checkbuttons.items()])

        # Only if the user inputs are also set will the buttons be enabled
        if complete and self.userInputsSet and len(self.checklist_Checkbuttons) !=0:
            self.enableButtons()

        self.checklist_win.destroy()

    def checklist(self):
        # Any time the checklist is opened, all buttons are disabled except for the save, help, and checklist
        self.disableButtons()
        self.checklistButton.configure(state='normal')

        # Top level window for checklist
        self.checklist_win = tk.Toplevel()
        # Bring pop up to the center and top
        self.eval(f'tk::PlaceWindow {str(self.checklist_win)} center')
        self.checklist_win.attributes('-topmost', True)

        # Create a Checkbutton for each item on the checklist
        for i, step in enumerate(checklist_steps):
            # A BooleanVar is linked to each Checkbutton and its state is updated any time a check is changed
            # The completion of the checklist is checked every time a Checkbutton value is changed
            self.checklist_Checkbuttons[f'c{i + 1}'] = tk.BooleanVar()
            button = ttk.Checkbutton(self.checklist_win, variable=self.checklist_Checkbuttons[f'c{i + 1}'], text=f'Step {i + 1}: ' + step)
            button.grid(row=i, column=0, sticky='w')

        # Add okay button to close the window
        self.OKButton = ttk.Button(self.checklist_win, text='Okay', command=self.checklistComplete, style='Accent.TButton')
        self.OKButton.grid(row=len(checklist_steps) + 1, column=0)

    def operateSwitch(self, switchName, state):
        # If state is false, power supply switch opens and load switch closes
        # If state is true, power supply switch closes and load switch opens
        try:
            with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(f'{sensorName}/{digitalOutName}/{self.outputPins[switchName]}')
                value = task.write(state)

        except:
            print('Cannot operate switches')

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
            # Operate switches
            self.operateSwitch('Load Switch', True)
            time.sleep(switchWaitTime)
            self.operateSwitch('Power Supply Switch', True)

            # Begin tracking time
            self.beginChargeTime = time.time()
            self.charging = True

            # Try charging
            try:
                with nidaqmx.Task() as task:
                    task.ao_channels.add_ao_voltage_chan(f'{sensorName}/{self.outputPins['Power Supply Voltage']}')

                    # Set the sampling rate
                    # https://nidaqmx-python.readthedocs.io/en/latest/timing.html
                    sample_rate = 100
                    seconds_to_acquire = 30
                    total_samples = sample_rate*seconds_to_acquire
                    task.timing.cfg_samp_clk_timing(rate=sample_rate, samps_per_chan=total_samples)

                    mapVoltage = self.chargeVoltage / maxVoltagePowerSupply * maxInputVoltage

                    chargeVoltageTrace = np.linspace(0, mapVoltage, total_samples) # linear charge rate
                    task.write(chargeVoltageTrace, auto_start=True)

            except:
                print('Cannot connect to NI DAQ')

            # Reset the charge plot and begin continuously plotting
            self.resetChargePlot()
            self.updateCharge()
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
                # Close Load switch
                self.operateSwitch('Load Switch', False)

        def saveResults():
            # Read from the load
            oscilloscopePins = [self.inputPins['Load Voltage'], self.inputPins['Load Current']]
            dischargeScope = ReadWriteScopeChannels(oscilloscopePins)
            self.dischargeTime = dischargeScope.time
            delf.dischargeTimeUnit = dischargeScope.tUnit
            self.dischargeVoltageLoad = dischargeScope.data[self.inputPins['Load Voltage']]
            self.dischargeCurrentLoad = dischargeScope.data[self.inputPins['Load Current']]


            # Plot results on the discharge graph and save them
            # The only time results are saved is when there is a discharge that is preceded by charge
            self.replotDischarge()
            self.saveResults()

        if self.charging:
            if not hasattr(self, 'countdownTime') or self.countdownTime > 0.0:
                popup()
                saveResults()
            else:
                saveResults()
        else:
            popup()

        # Disable all buttons except for save and help, if logged in
        self.disableButtons()
        if self.loggedIn:
            self.resetButton.configure(state='normal')

        self.discharged = True
        self.charging = False

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
        # Open power supply and close load switch
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Load Switch', False)

        # Close window
        plt.close('all')
        self.quit()
        self.destroy()

    def readSensor(self, pin):
        if TEST_MODE:
            if pin == 'ai0':
                value = np.random.rand() * 1000
            elif pin == 'ai1':
                value = powerSupplyVoltage * ( 1 -  np.exp( -self.timePoint / RCTime ) )
            elif pin == 'ai2':
                value = np.random.rand() / 10
            elif pin == 'ai3':
                period = 10 # seconds
                value = np.abs(np.cos(self.timePoint * 2 * np.pi / period))
            else:
                value = 'N/A'

        else:
            try:
                with nidaqmx.Task() as task:
                    task.ai_channels.add_ai_voltage_chan(f'{sensorName}/{pin}')
                    value = task.read()

            except:
                print('Cannot connect to NI DAQ')

        return value

    # Read oscilloscope data based on pins
    def readOscilloscope(self, pins):
        time = np.linspace(0, 1)
        voltageLoad = 1 - np.exp(-time)
        currentLoad = np.exp(-time)
        return time, voltageLoad, currentLoad

    # The labels for the load and power supply update in real time
    def updateLabels(self):
        loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
        PSSuperscript = '\u1D56\u02E2'
        self.voltageLoadText.set(f'V{loadSuperscript}: {self.readSensor(self.inputPins["Load Voltage"]) / 1000:.2f} kV')
        self.voltagePSText.set(f'V{PSSuperscript}: {self.readSensor(self.inputPins["Power Supply Voltage"]) / 1000:.2f} kV')
        self.currentLoadText.set(f'I{loadSuperscript}: {self.readSensor(self.inputPins["Load Current"]):.2f} A')
        self.currentPSText.set(f'I{PSSuperscript}: {self.readSensor(self.inputPins["Power Supply Current"]):.2f} A')

        if self.userInputsSet:
            self.progress['value'] = 100 * self.readSensor(self.inputPins["Power Supply Voltage"]) / 1000 / self.chargeVoltage

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

    # Removes all lines from a figure
    def clearFigLines(self, fig):
        axes = fig.axes
        for axis in axes:
            if len(axis.lines) != 0:
                for i in range(len(axis.lines)):
                    axis.lines[0].remove()

    def replotCharge(self):
        # Remove lines every time the figure is plotted
        self.clearFigLines(self.chargePlot.fig)

        # Add plots
        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltageLoad / 1000, color=voltageColor)
        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltagePS / 1000, color=voltageColor, linestyle='--')
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentLoad, color=currentColor)
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentPS, color=currentColor, linestyle='--')
        self.chargePlot.updatePlot()

    def replotDischarge(self):
        # Remove lines every time the figure is plotted
        self.clearFigLines(self.dischargePlot.fig)
        self.dischargePlot.ax.set_xlabel(f'Time ({self.dischargeTimeUnit})')

        # Add plots
        self.dischargeVoltageAxis.plot(self.dischargeTime, self.dischargeVoltageLoad / 1000, color=voltageColor, label='V$_{load}$')
        self.dischargeCurrentAxis.plot(self.dischargeTime, self.dischargeCurrentLoad, color=currentColor, label='I$_{load}$')
        self.dischargePlot.updatePlot()

    # Retrieves and processes the data for the charging plot in a continuous loop
    def updateCharge(self):
        # Retrieve charging data
        self.timePoint = time.time() - self.beginChargeTime
        voltageLoadPoint = self.readSensor(self.inputPins['Load Voltage'])
        voltagePSPoint = self.readSensor(self.inputPins['Power Supply Voltage'])
        currentLoadPoint = self.readSensor(self.inputPins['Load Current'])
        currentPSPoint = self.readSensor(self.inputPins['Power Supply Current'])

        self.chargeTime = np.append(self.chargeTime, self.timePoint)
        self.chargeVoltageLoad = np.append(self.chargeVoltageLoad, voltageLoadPoint)
        self.chargeVoltagePS = np.append(self.chargeVoltagePS, voltagePSPoint)
        self.chargeCurrentLoad = np.append(self.chargeCurrentLoad, currentLoadPoint)
        self.chargeCurrentPS = np.append(self.chargeCurrentPS, currentPSPoint)

        # Plot the new data
        self.replotCharge()

        # Voltage reaches a certain value of chargeVoltage to begin countown clock
        if voltagePSPoint >= chargeVoltageLimit * self.chargeVoltage * 1000:
            # Start countdown only once
            if not self.countdownStarted:
                self.countdownTimeStart = time.time()
                self.charged = True
                self.countdownStarted = True

                # Open power supply switch
                self.operateSwitch('Power Supply Switch', False)

            # Time left before discharge
            self.countdownTime = self.holdChargeTime - (time.time() - self.countdownTimeStart)

            # Set countdown time to 0 seconds once discharged
            if self.countdownTime <= 0.0:
                self.discharge()

        # Discharge if the voltage is not increasing
        # This is determined if the charge does not exceed a small percentage of the desired charge voltage within a given period of time
        notCharging = voltagePSPoint <= epsilonDesiredChargeVoltage * self.chargeVoltage and self.timePoint > chargeTimeLimit
        if notCharging:
            self.discharge()
            print('Not charging')

        # Also discharge if charging but not reaching the desired voltage
        # This is determined by checking for steady state
        # In the future it would be better to implement a more rigorous statistical test, like the student t
        steadyState = False
        window = 20 # number of points at the end of the data set from which to calculate slope
        nWindows = 10 # number of windows to implement sliding window
        lengthArray = len(self.chargeTime)
        slopes, _ = np.array([np.polyfit(self.chargeTime[lengthArray - window - i:lengthArray - i], self.chargeVoltagePS[lengthArray - window - i:lengthArray - i], 1) for i in range(nWindows)]).T # first order linear regression
        steadyState = np.std(slopes) / np.mean(slopes) < 0.05
        if steadyState:
            self.discharge()
            print('Steady state reached without charging to desired voltage')

        # Also update the labels with time
        self.updateLabels()

        # Loop through this function again continuously while charging
        if self.charging == True:
            self.after(int(1000 / refreshRate), self.updateCharge)

    def resetChargePlot(self):
        # Set time and voltage to empty array
        self.chargeTime = np.array([])
        self.chargeVoltageLoad = np.array([])
        self.chargeVoltagePS = np.array([])
        self.chargeCurrentLoad = np.array([])
        self.chargeCurrentPS = np.array([])

        # Also need to reset the twinx axis
        self.chargeCurrentAxis.relim()
        self.chargeCurrentAxis.autoscale_view()

        self.replotCharge()

    def resetDischargePlot(self):
        # Set time and voltage to empty array
        self.dischargeTime = np.array([])
        self.dischargeVoltageLoad = np.array([])
        self.dischargeCurrentLoad = np.array([])

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
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.timePoint = 0
        self.countdownStarted = False
        self.checklist_Checkbuttons = {}
        self.updateLabels()

        # Reset plots
        self.resetChargePlot()
        self.resetDischargePlot()

        # Disable all buttons if logged in
        self.disableButtons()

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
