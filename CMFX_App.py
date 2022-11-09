from TestingApp import *

class CMFX_App(TestingApp):
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

    def pinSelector(self):
        # Create popup window with fields for username and password
        self.setPinWindow = tk.Toplevel(padx=setPinsPadding, pady=setPinsPadding)
        self.setPinWindow.title('Set Pins')
        # Bring pop up to the center and top
        self.eval(f'tk::PlaceWindow {str(self.setPinWindow)} center')
        self.setPinWindow.attributes('-topmost', True)

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
        # If the user would like to add or remove fields please make those changes in constant.py
        results = [getattr(self, variable) for variable in columns if hasattr(self, variable)]

        # Creates a data frame which is easier to save to csv formats
        results_df = pd.DataFrame([pd.Series(val) for val in results]).T
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

            for key, value in columns.items():
                if value['type'] == 'scalar':
                    if value['name'] in results_df:
                        self.__dict__.update({key: results_df[value['name']].values[0]})
                    else:
                        self.__dict__.update({key: np.nan})
                else:
                    if value['name'] in results_df:
                        self.__dict__.update({key: results_df[value['name']].dropna().values})
                    else:
                        self.__dict__.update({key: np.zeros(0)})

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
                    self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()
                except visa.errors.VisaIOError:
                    self.scope.connectInstrument()
                    self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                    self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                    self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
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
                self.pulseGenerator.triggerIgnitron()
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
