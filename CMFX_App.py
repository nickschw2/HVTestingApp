from TestingApp import *

# SAVE RESULTS EVEN WHEN THERE'S NO DISCHARGE
# CHANGE GUI TO LOOK MORE LIKE THAT IN TOKAMAK ENERGY PICTURE

class CMFX_App(TestingApp):
    def __init__(self):
        super().__init__()

        # Change circuit parameters in config.py    
        self.capacitance = capacitance
        self.ballastResistance = ballastResistance
        self.dumpResistance = dumpResistance
        self.chamberProtectionResistance = chamberProtectionResistance
        self.polarity = POLARITY
        self.userInputs = userInputs
        self.primaryGasDefault = primaryGasDefault
        self.secondaryGasDefault = secondaryGasDefault

        # Create and show user interface
        self.configure_ui()
        self.init_ui()

        # Connect to instruments
        if not DEBUG_MODE:
            self.init_DAQ()
            self.init_visaInstruments()

    def configure_ui(self):
        # set title
        self.title('CMFX App')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        # Notebook creates tabs at the top
        self.notebook = ttk.Notebook(self, takefocus=False, bootstyle='primary')
        self.notebook.pack(expand=True, side='top', padx=framePadding, pady=framePadding)

        tabNames = ['System Status', 'User Inputs', 'Charging', 'Results', 'Analysis']
        self.notebookFrames = {}
        for tabName in tabNames:
            frame = ttk.Frame(self.notebook)
            frame.pack(expand=True, fill='both')
            self.notebook.add(frame, text=tabName)
            self.notebookFrames[tabName] = frame

        #### SYSTEM STATUS SECTION ####
        # Add frames for text labels
        self.textStatusFrame = ttk.Frame(self.notebookFrames['System Status'])
        self.HVStatusFrame = ttk.LabelFrame(self.textStatusFrame, text='High Voltage Status', width=systemStatusFrameWidth, height=150, bootstyle='primary')
        self.pressureStatusFrame = ttk.LabelFrame(self.textStatusFrame, text='Pressure Status', width=systemStatusFrameWidth, height=110, bootstyle='primary')
        self.circuitValuesFrame = ttk.LabelFrame(self.textStatusFrame, text='Circuit Values', width=systemStatusFrameWidth, height=230, bootstyle='primary')

        self.textStatusFrame.pack(side='left', expand=True, fill='both', padx=framePadding, pady=framePadding)
        self.HVStatusFrame.pack(side='top', expand=True)
        self.pressureStatusFrame.pack(side='top', expand=True)
        self.circuitValuesFrame.pack(side='top', expand=True)

        # Force width of label frames
        self.HVStatusFrame.pack_propagate(0)
        self.pressureStatusFrame.pack_propagate(0)
        self.circuitValuesFrame.pack_propagate(0)

        # Create text variables for status indicators, associate with labels, and place
        self.voltagePSText = ttk.StringVar()
        self.currentPSText = ttk.StringVar()
        self.capacitorVoltageText = ttk.StringVar()
        self.chamberPressureText = ttk.StringVar()
        self.pumpPressureText = ttk.StringVar()

        self.voltagePSLabel = ttk.Label(self.HVStatusFrame, textvariable=self.voltagePSText)
        self.currentPSLabel = ttk.Label(self.HVStatusFrame, textvariable=self.currentPSText)
        self.capacitorVoltageLabel = ttk.Label(self.HVStatusFrame, textvariable=self.capacitorVoltageText)
        self.chamberPressureLabel = ttk.Label(self.pressureStatusFrame, textvariable=self.chamberPressureText)
        self.pumpPressureLabel = ttk.Label(self.pressureStatusFrame, textvariable=self.pumpPressureText)
        self.bankCapacitanceLabel = ttk.Label(self.circuitValuesFrame, text=f'Bank Capacitance: {self.capacitance} uF')
        self.ballastResistanceLabel = ttk.Label(self.circuitValuesFrame, text=f'Ballast Resistance: {self.ballastResistance} {Omega}')
        self.dumpResistanceLabel = ttk.Label(self.circuitValuesFrame, text=f'Dump Resistance: {int(self.dumpResistance * 1000)} m{Omega}')
        self.chamberProtectionResistanceLabel = ttk.Label(self.circuitValuesFrame, text=f'Chamb. Prot. Resistance: {int(self.chamberProtectionResistance * 1000)} m{Omega}')
        self.polarityLabel = ttk.Label(self.circuitValuesFrame, text=f'Polarity: {self.polarity}')

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.chamberPressureLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pumpPressureLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.bankCapacitanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.ballastResistanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.dumpResistanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.chamberProtectionResistanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.polarityLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

        # Add textboxes for adding notes about a given shot
        self.userNotesFrame = ttk.Frame(self.notebookFrames['System Status'])
        self.preShotNotesFrame = ttk.LabelFrame(self.userNotesFrame, text='Pre-Shot Notes', bootstyle='primary')
        self.postShotNotesFrame = ttk.LabelFrame(self.userNotesFrame, text='Post-Shot Notes', bootstyle='primary')

        # self.userNotesFrame.place(relx=0.5, rely=0.5, anchor='center')
        self.userNotesFrame.pack(side='left', expand=True, fill='both', padx=framePadding, pady=framePadding)
        self.preShotNotesFrame.pack(side='top', expand=True)
        self.postShotNotesFrame.pack(side='top', expand=True)

        self.preShotNotesEntry = scrolled.ScrolledText(self.preShotNotesFrame, font=('Helvetica', 10), height=10, wrap='word')
        self.postShotNotesEntry = scrolled.ScrolledText(self.postShotNotesFrame, font=('Helvetica', 10), height=10, wrap='word')

        self.preShotNotesButton = ttk.Button(self.preShotNotesFrame, text='Record', command=self.recordPreShotNotes)
        self.postShotNotesButton = ttk.Button(self.postShotNotesFrame, text='Record', command=self.recordPostShotNotes)

        self.preShotNotesEntry.pack(side='left', expand=True, padx=(framePadding, 0), pady=framePadding)
        self.postShotNotesEntry.pack(side='left', expand=True, padx=(framePadding, 0), pady=framePadding)
        self.preShotNotesButton.pack(side='right', expand=True, padx=labelPadding)
        self.postShotNotesButton.pack(side='right', expand=True, padx=labelPadding)

        ### USER INPUTS SECTION ###
        # There are two columns of user inputs
        n_rows = int(np.ceil(len(self.userInputs) / 2))
        self.userEntries = {}
        userInputFrame = ttk.LabelFrame(self.notebookFrames['User Inputs'], text='Value Input', bootstyle='primary')
        userInputFrame.grid(row=0, column=0, columnspan=3, sticky='nsew', padx=(framePadding, 0), pady=framePadding)
        self.notebookFrames['User Inputs'].grid_rowconfigure(0, weight=1)
        self.notebookFrames['User Inputs'].grid_columnconfigure(0, weight=1)

        for i, (variable, description) in enumerate(self.userInputs.items()):
            label = ttk.Label(userInputFrame, text=f'{description["label"]}:')
            entry = ttk.Entry(userInputFrame, width=userInputWidth, font=('Helvetica', 12))

            self.userEntries[variable] = entry

            label.grid(row=i % n_rows, column=2 * int(i / n_rows), sticky='e', padx=labelPadding)
            entry.grid(row=i % n_rows, column=2 * int(i / n_rows) + 1, sticky='w', padx=labelPadding)
            validation.add_range_validation(entry, description['min'], description['max'], when='focus')

            userInputFrame.grid_rowconfigure(i % n_rows, weight=1)
            userInputFrame.grid_columnconfigure(2 * int(i / n_rows), weight=1)
            userInputFrame.grid_columnconfigure(2 * int(i / n_rows) + 1, weight=1)


        setButton = ttk.Button(self.notebookFrames['User Inputs'], text='Set', bootstyle='primary', command=self.setUserInputs)
        setButton.grid(row=1, column=0, columnspan=2, pady=buttonPadding)

        makeDefaultButton = ttk.Button(self.notebookFrames['User Inputs'], text='Make Default', bootstyle='primary', command=self.setUserInputsDefault)
        makeDefaultButton.grid(row=1, column=1, columnspan=2, pady=buttonPadding)

        # Selection of gases
        gasSelectionFrame = ttk.LabelFrame(self.notebookFrames['User Inputs'], text='Gas Selection', bootstyle='primary')
        gasSelectionFrame.grid(row=0, column=3, rowspan=n_rows, padx=framePadding)

        primaryGasLabel = ttk.Label(gasSelectionFrame, text='Primary Gas')
        secondaryGasLabel = ttk.Label(gasSelectionFrame, text='Secondary Gas')
        self.primaryGasComboBox = ttk.Combobox(gasSelectionFrame, value=gasOptions, state='readonly', bootstyle='primary', **text_opts)
        self.secondaryGasComboBox = ttk.Combobox(gasSelectionFrame, value=gasOptions, state='readonly', bootstyle='primary', **text_opts)

        self.primaryGasComboBox.current(gasOptions.index(self.primaryGasDefault))
        self.secondaryGasComboBox.current(gasOptions.index(self.secondaryGasDefault))

        self.primaryGasComboBox.bind('<<ComboboxSelected>>', self.setGases)
        self.secondaryGasComboBox.bind('<<ComboboxSelected>>', self.setGases)

        primaryGasLabel.pack(side='top', padx=framePadding, anchor='w')
        self.primaryGasComboBox.pack(side='top', padx=framePadding, pady=(0, framePadding))
        secondaryGasLabel.pack(side='top', padx=framePadding, anchor='w')
        self.secondaryGasComboBox.pack(side='top', padx=framePadding, pady=(0, framePadding))

        #### CHARGING SECTION ####
        # Add charging input to notebook
        # New frame for plot and other indicators in one row
        self.chargingStatusFrame = ttk.Frame(self.notebookFrames['Charging'])
        self.chargingStatusFrame.pack(side='top', expand=True, padx=framePadding, pady=framePadding)

        # Frame for indicators
        self.chargingIndicatorsFrame = ttk.Frame(self.chargingStatusFrame)
        self.chargingIndicatorsFrame.pack(side='left', expand=True, padx=framePadding, pady=framePadding)

        # Add progress bar to notebook
        self.progressBar = ttk.widgets.Meter(master=self.chargingIndicatorsFrame,
                                             stripethickness=3, subtext='Charged', textright='%',
                                             bootstyle='success')
        self.progressBar.pack(side='top', expand=True)

        # Add status variables, associate with labels, and place them
        self.chargeStateText = ttk.StringVar()

        self.chargeStateLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.chargeStateText)

        self.chargeStateLabel.pack(side='top', expand=True, pady=(labelPadding, 0))

        # Frame for power supply status
        self.powerSupplyStatusFrame = ttk.Frame(self.chargingStatusFrame)
        self.powerSupplyStatusFrame.pack(side='left', expand=True, padx=framePadding, pady=framePadding)

        self.booleanIndicators = {}
        # Specific indicators for a certain power supply AND all other indicators
        for indicator_label in powerSupplyIndicatorLabels[POWER_SUPPLY] + indicatorLabels:
            indicator = Indicator(self.powerSupplyStatusFrame, text=indicator_label)
            indicator.pack(side='top', anchor='w', pady=(0, labelPadding))
            self.booleanIndicators[indicator_label] = indicator

        # Plot of charge
        self.chargePlot = CanvasPlot(self.chargingStatusFrame, figsize=(10, 4))

        # Create two y-axes for current and voltage
        self.chargeVoltageAxis = self.chargePlot.ax
        self.chargeCurrentAxis = self.chargePlot.ax.twinx()

        # Turn off twin grid since it's normally on by default
        self.chargeCurrentAxis.grid(False)

        self.chargePlot.ax.set_xlabel('Time (s)')
        self.chargeVoltageAxis.set_ylabel('Voltage (kV)')
        self.chargeCurrentAxis.set_ylabel('Current (mA)')

        # Add lines to charging plot blit animation
        self.chargeVoltageLine, = self.chargeVoltageAxis.plot([],[], color=voltageColor) #Create line object on plot
        self.chargeCurrentLine, = self.chargeCurrentAxis.plot([],[], color=currentColor) #Create line object on plot
        self.capacitorVoltageLine, = self.chargeVoltageAxis.plot([],[], color=voltageColor, linestyle='--') #Create line object on plot
        self.chargePlot.ax.set_xlim(0, plotTimeLimit)
        self.chargeVoltageAxis.set_ylim(0, voltageYLim)
        self.chargeCurrentAxis.set_ylim(0, currentYLim)

        # Add actors to blit manager
        # Blit manager speeds up plotting by redrawing only necessary items
        self.bm = BlitManager(self.chargePlot.canvas, [self.chargeVoltageLine, self.chargeCurrentLine, self.capacitorVoltageLine,
                                                       self.chargePlot.ax.xaxis, self.chargePlot.ax.yaxis, self.chargeCurrentAxis.yaxis])

        # Create the legends before any plot is made
        self.chargePlot.ax.legend(handles=chargeHandles, loc='upper right')

        # Add navigation toolbar to plots
        self.chargePlotToolbar = CustomToolbar(self.chargePlot.canvas, self.chargingStatusFrame)
        self.chargePlotToolbar.update()

        # Place plot with toolbar in frame
        self.chargePlot.pack(side='right', expand=True, padx=plotPadding)

        # Row for buttons on the bottom
        self.buttons = ttk.LabelFrame(self.notebookFrames['Charging'], text='Operate Capacitor', bootstyle='primary')
        self.buttons.pack(side='top', expand=True, pady=(0, framePadding))

        # Button definitions and placement
        self.checklistButton = ttk.Button(self.buttons, text='Checklist Complete',
                                    command=self.checklist, bootstyle='success')
        self.enableHVButton = ttk.Button(self.buttons, text='Enable HV',
                                    command=self.enableHV, bootstyle='warning')
        self.chargeButton = ttk.Button(self.buttons, text='Charge',
                                    command=self.charge, bootstyle='warning')
        self.dischargeButton = ttk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bootstyle='danger')

        self.checklistButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)
        # Conditionals depending on the power supply in use
        if POWER_SUPPLY == 'PLEIADES':
            self.enableHVButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)
        self.chargeButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)
        self.dischargeButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)

        

        #### RESULTS SECTION ####
        # Initialize the data structure to hold results plot
        self.resultsPlotData = {'Voltage': {'twinx': False, 'ylabel': 'Voltage (V)', 'lines': voltageLines},
                                'Current': {'twinx': False, 'ylabel': 'Current (A)', 'lines': currentLines},
                                'Diamagnetic': {'twinx': False, 'ylabel': 'Diamagnetic (V)', 'lines': diamagneticLines},
                                'B-Radial': {'twinx': False, 'ylabel': 'B$_R$ (V)', 'lines': BRLines},
                                'Diode': {'twinx': False, 'ylabel': 'Diode (V)', 'lines': DIODELines}}
        
        self.resultsPlotViewer = PlotViewer(self.notebookFrames['Results'], self.resultsPlotData)

        # Row for diagnostics on the bottom
        misc_diagnostics = ttk.LabelFrame(self.notebookFrames['Results'], text='Misc. Diagnostics', bootstyle='primary')
        misc_diagnostics.pack(side='bottom', expand=True, pady=(0, framePadding))

        # Diagnostic definitions and placement
        # Creates a label for each He3 detector and stores the textvariable in a dictionary
        # Set the number of rows
        n_rows = 3
        self.counterText_dict = {}
        for i, counter in enumerate(self.counters_Pins):
            setattr(self, f'{counter}Text', ttk.StringVar())
            text = getattr(self, f'{counter}Text')
            self.counterText_dict[counter] = text
            text.set(f'{counter}: N/A')
            label = ttk.Label(misc_diagnostics, textvariable=text)
            label.grid(row=int(i / n_rows), column=int(i % n_rows), sticky='nsew', padx=buttonPadding, pady=labelPadding)

        #### ANALYSIS SECTION ####
        # Initialize the data structure to hold results plot
        self.analysisPlotData = {'Voltage': {'twinx': False, 'ylabel': 'Voltage (kV)', 'lines': voltageAnalysisLines},
                                 'Current': {'twinx': False, 'ylabel': 'Current (A)', 'lines': currentAnalysisLines},
                                 'Diamagnetic': {'twinx': False, 'ylabel': 'Density ($10^{18}$ m$^{-3}$)', 'lines': diamagneticAnalysisLines}}
        
        self.analysisPlotViewer = PlotViewer(self.notebookFrames['Analysis'], self.analysisPlotData)

        # Row for diagnostics on the bottom
        misc_analysis = ttk.LabelFrame(self.notebookFrames['Analysis'], text='Misc. Analysis', bootstyle='primary')
        misc_analysis.pack(side='bottom', expand=True, pady=(0, framePadding))

        # Analysis definitions and placement
        # Creates a label for each analysis variable and stores the textvariable in a dictionary
        self.analysisText_dict = {}
        for variable in analysisVariables:
            setattr(self, f'{variable}Text', ttk.StringVar())
            text = getattr(self, f'{variable}Text')
            self.analysisText_dict[variable] = text
            text.set(f'{analysisVariables[variable]["label"]}: N/A')
            label = ttk.Label(misc_analysis, textvariable=text)
            label.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)

        #### STATIC SECTION ####
        self.staticFrame = ttk.Frame(self)
        self.staticFrame.pack(fill='x', side='bottom', expand=True)

        # Create frame to hold console and scroll bar
        self.consoleFrame = ttk.LabelFrame(self.staticFrame, text='Console', bootstyle='primary')
        self.consoleFrame.pack(fill='x', side='left', expand=True, padx=framePadding, pady=(0, framePadding))

        # Height is number of lines to be displayed
        self.console = Console(self.consoleFrame, height=10)
        self.console.pack(side='left', fill='x', expand=True, padx=labelPadding, pady=labelPadding)

        # Create a frame to hold buttons
        self.buttonFrame = ttk.Frame(self.staticFrame)
        self.buttonFrame.pack(side='right', expand=False, padx=(0, framePadding), pady=(0, framePadding))
        
        # Add large emergency off button
        self.emergencyOffButton = ttk.Button(self.buttonFrame, text='Emergency\nOff', command=self.emergency_off, style='bigRed.TButton')
        self.emergencyOffButton.pack(side='top', fill='both', expand=True, pady=(0, framePadding))

        # Add a reset button
        self.resetButton = ttk.Button(self.buttonFrame, text='Reset', command=self.reset, style='bigOrange.TButton')
        self.resetButton.pack(side='top', fill='both', expand=True)

        #### MENUBAR ####
        self.menubar = ttk.Menu(self)
        self.filemenu = ttk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Open', command=self.readResults)
        self.filemenu.add_command(label='Save Folder', command=self.setSaveLocation)
        self.filemenu.add_command(label='Set Pins', command=self.pinSelector)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Quit', command=self.on_closing)
        self.menubar.add_cascade(label='File', menu=self.filemenu)

        self.helpmenu = ttk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label='Help', command=self.help)
        self.helpmenu.add_command(label='About...', command=self.openSite)
        self.menubar.add_cascade(label='Help', menu=self.helpmenu)

        self.config(menu=self.menubar)

        self.update()

    def init_ui(self):
        # Begin the operation of the program

        # center the app
        self.center_app()

        # Reset all fields on startup
        self.loggedIn = False
        self.reset()

        if ADMIN_MODE:
            self.loggedIn = True
            self.saveFolder = saveFolderShotDefault
            self.saveFolderSet = True

        else:
            # Prompt for login, save location, and pin selector automatically
            self.validateLogin()
            self.setSaveLocation()
            self.pinSelector()
        
        # If the user closes out of the application during a wait_window, no extra windows pop up
        self.update()
        
        self.updateSystemStatus()
        
        self.safetyLights()

    def editNotes(self, notes, type):
        # Change individual results file
        results_df = pd.read_csv(f'{self.saveFolder}/{self.runDate}/{self.filename}', low_memory=False)
        columnName = single_columns[type]['name']
        results_df.at[0, columnName] = notes
        results_df.to_csv(f'{self.saveFolder}/{self.runDate}/{self.filename}', index=False)

        # Change master file
        resultsMaster_df = pd.read_csv(f'{self.saveFolder}/{resultsMasterName}')
        row = resultsMaster_df.index[resultsMaster_df['Run Number'] == int(self.runNumber)].tolist()[0]
        resultsMaster_df.at[row, columnName] = notes
        resultsMaster_df.to_csv(f'{self.saveFolder}/{resultsMasterName}', index=False)


    def recordPreShotNotes(self):
        self.preShotNotes = self.preShotNotesEntry.text.get('1.0', 'end').strip()

        # Edit the csv file on a separate thread
        if self.resultsSaved:
            Thread(target=self.editNotes, args=[self.preShotNotes, 'preShotNotes']).start()

        print('Pre-shot notes recorded')

    def recordPostShotNotes(self):
        self.postShotNotes = self.postShotNotesEntry.text.get('1.0', 'end').strip()

        # Edit the csv file on a separate thread
        if self.resultsSaved:
            Thread(target=self.editNotes, args=[self.postShotNotes, 'postShotNotes']).start()

        print('Post-shot notes recorded')

    def setGases(self, event=None):
        self.primaryGas = self.primaryGasComboBox.get()
        self.secondaryGas = self.secondaryGasComboBox.get()

        print(f'Primary gas: {self.primaryGas}, Secondary gas: {self.secondaryGas}')

    def setUserInputs(self):
        # Assume that the user inputs are all valid to begin with, and then check each one
        validated = True
        for variable, entry in self.userEntries.items():
            # Check if the entry is within the range specified in the config file
            if not entry.validate() or len(entry.get()) == 0:
                validated = False
                entry.delete(0, 'end')

                text = f'''Please reenter a valid number for {self.userInputs[variable]["label"]}.
                           The range for this variable is {self.userInputs[variable]["min"]} to
                           {self.userInputs[variable]["max"]}.'''
                windowName = 'Invalid Input'
                MessageWindow(self, windowName, text)

        # If all user inputs are valid, set the variables to the values entered
        if validated:
            self.userInputsSet = True
            for variable, entry in self.userEntries.items():
                setattr(self, variable, float(entry.get()))

            # Set the scale on the oscilloscope based on inputs
            if not DEBUG_MODE:
                if USING_SCOPE:
                    self.scope.setScale(self.chargeVoltage)

                # Settings on visa instruments
                self.pulseGenerator.setDelay(pulseGeneratorOutputs['dump_ign']['chan'], self.dumpDelay / 1000 + self.ignitronDelay / 1000)
                self.pulseGenerator.setDelay(pulseGeneratorOutputs['load_ign']['chan'], self.ignitronDelay / 1000)
                # self.iotaOne.setGasPuffTime(self.primaryGasTime)

                # Reset the timing on the daq
                self.NI_DAQ.set_timing(self.dumpDelay / 1000, self.ignitronDelay / 1000, self.spectrometerDelay / 1000, self.secondaryGasTime / 1000)

            # Check if the save folder has been selected, and if so allow user to begin checklist
            if self.saveFolderSet:
                self.checklistButton.configure(state='normal')

            # Display pop up window to let user know that values have been set
            setUserInputName = 'User Inputs Set!'
            setUserInputText = 'User inputs have been set. They may be changed at any time for any subsequent run.'
            MessageWindow(self, setUserInputName, setUserInputText)

    def setUserInputsDefault(self):
        for variable, entry in self.userEntries.items():
            self.userInputs[variable]['default'] = entry.get()
        
        self.primaryGasDefault = self.primaryGas
        self.secondaryGasDefault = self.secondaryGas
        print('Set the new default values for the User Inputs')

    def updateSystemStatus(self):
        # Updates HV Status Frame
        def updateHVStatus():
            voltagePSPoint = np.nan	
            currentPSPoint = np.nan	
            capacitorVoltagePoint = np.nan

            # not applicable on startup	
            if hasattr(self, 'NI_DAQ'):
                if not DEBUG_MODE:	
                    voltages = self.NI_DAQ.systemStatusData	
                else:	
                    voltages = self.getChargingTestVoltages()

                # Update charging values in object while not discharged
                if self.charging:
                    self.chargeVoltagePS = (voltages['Power Supply Voltage']) * maxVoltagePowerSupply[POWER_SUPPLY] / maxAnalogInput	
                    self.chargeCurrentPS = (voltages['Power Supply Current'] + 10) * maxCurrentPowerSupply[POWER_SUPPLY] / maxAnalogInput # +10 because theres an offset for whatever reason	
                    self.capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider	
                    
                    voltagePSPoint = self.chargeVoltagePS[-1]
                    currentPSPoint = self.chargeCurrentPS[-1]
                    capacitorVoltagePoint = self.capacitorVoltage[-1]
                
                else:
                    chargeVoltagePS = (voltages['Power Supply Voltage']) * maxVoltagePowerSupply[POWER_SUPPLY] / maxAnalogInput	
                    chargeCurrentPS = (voltages['Power Supply Current'] + 10) * maxCurrentPowerSupply[POWER_SUPPLY] / maxAnalogInput # +10 because theres an offset for whatever reason	
                    capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider
                    	
                    voltagePSPoint = chargeVoltagePS[-1]
                    currentPSPoint = chargeCurrentPS[-1]
                    capacitorVoltagePoint = capacitorVoltage[-1]

            self.voltagePSText.set(f'Power Supply V: {voltagePSPoint / 1000:.2f} kV')	
            self.currentPSText.set(f'Power Supply I: {currentPSPoint * 1000:.2f} mA')
            self.capacitorVoltageText.set(f'Capacitor V: {capacitorVoltagePoint / 1000:.2f} kV')	

            if not self.idleMode:	
                self.progressBar.configure(amountused = np.abs(int(100 * capacitorVoltagePoint / 1000 / self.chargeVoltage)))

            # Logic heirarchy for charge state and countdown text
            if self.discharged:
                self.chargeStateText.set('Discharged!')

                self.dischargeTime = self.NI_DAQ.dischargeTime
                self.dischargeTimeUnit = self.NI_DAQ.tUnit

                # Once the save thread has finished, then we can replot the discharge results
                if hasattr(self, 'saveDischarge_thread') and not self.saveDischarge_thread.is_alive() and not self.resultsSaved:
                    # Update the neutron diagnostics
                    for counter, textVariable in self.counterText_dict.items():
                        textVariable.set(f'{counter}: {getattr(self, counter)}')

                    # Show results tab once finished plotting
                    self.notebook.select(4)
                    self.resultsSaved = True

                    print('Saving results to file and replotting...')
                    
                    # Start saving on separate threads
                    Thread(target=self.saveResults).start()
                    
                    # Analyze results and plot those as well
                    self.performAnalysis()

                    # Can't replot results on a separate thread from the main because it throws run time error
                    self.resultsPlotViewer.replot()
                    self.analysisPlotViewer.replot()

                # If using scope add new file for the scope data
                if USING_SCOPE and hasattr(self, 'saveScope_thread') and not self.saveScope_thread.is_alive() and not self.scopeDataSaved:
                    # Start saving on separate threads
                    self.scopeDataSaved = True
                    Thread(target=self.saveScopeResults).start()

            elif self.charged:
                self.chargeStateText.set('Charged')
            else:
                self.chargeStateText.set('Not Charged')

            if self.charging and not self.discharged:
                N = len(self.chargeVoltagePS)	
                self.chargeTime = np.linspace(0, (N - 1) / systemStatus_sample_rate, N)	
                self.timePoint = (N - 1) / systemStatus_sample_rate

                # Sometimes there's a mismatch in length of voltages read from daq
                if len(self.chargeVoltagePS) != len(self.chargeCurrentPS):
                    print('Length mismatch in NI DAQ read')
                    self.chargeCurrentPS = self.chargeCurrentPS[:len(self.chargeVoltagePS)]
                if len(self.chargeVoltagePS) != len(self.capacitorVoltage):
                    print('Length mismatch in NI DAQ read')
                    self.capacitorVoltage = self.capacitorVoltage[:len(self.chargeVoltagePS)]

                # Plot the new data
                self.replotCharge()

                # Voltage reaches a certain value of chargeVoltage to begin countown clock
                if np.abs(capacitorVoltagePoint) >= chargeVoltageLimit * self.chargeVoltage * 1000 and not self.charged:
                    # Reset the trigger just before discharging
                    self.NI_DAQ.reset_discharge_trigger()

                    # Actually begin discharging power supply before opening power supply switch so it doesnt overshoot
                    self.powerSupplyRamp(action='discharge')

                    # Open power supply switch
                    self.operateSwitch('Power Supply Switch', False)

                    # Disable HV
                    self.operateSwitch('Enable HV', False)

                    # Have to set charged to True before starting discharge thread
                    self.charged = True
                    thread = Thread(target=self.discharge)	
                    thread.start()

        def updatePressureStatus():
            chamberPressure = 8e-4
            pumpPressure = 2e-4
            self.chamberPressureText.set(f'Chamber Press.: {chamberPressure:.1e} Torr')
            self.pumpPressureText.set(f'Pump Press.: {pumpPressure:.1e} Torr')

        def updatePowerSupplyStatus():
            # Not applicable on startup
            if hasattr(self, 'NI_DAQ'):
                # Set the states for all boolean indicators
                for (name, state) in zip(self.NI_DAQ.task_di.di_channels.channel_names, self.NI_DAQ.task_di.read()):
                    # Power supply indicators work off reverse boolean logic, hence the "not"
                    if name in powerSupplyIndicatorLabels[POWER_SUPPLY]:
                        self.booleanIndicators[name].set(not state)
                    else:
                        self.booleanIndicators[name].set(state)

                # Stop charging and generate fault message if there has been a change in state
                # if self.charging and any([not self.booleanIndicators['HV On'].state,
                #         self.booleanIndicators['Interlock Closed'].state,
                #         self.booleanIndicators['Spark'].state,
                #         self.booleanIndicators['Over Temp Fault'].state,
                #         self.booleanIndicators['AC Fault'].state,
                #         not self.booleanIndicators['Door Closed 1'].state,
                #         not self.booleanIndicators['Door Closed 2'].state]):
                    
                    # if not any([self.booleanIndicators['Door Closed 1'].state,
                    #         self.booleanIndicators['Door Closed 2'].state]):
                    #     name = 'Door Open Fault'
                    #     text = 'The door to the lab has been left open. Discharging now.'
                    # else:
                    #     name = 'Power Supply Fault'
                    #     text = 'There has been a fault in the power supply. Discharging now.'

                    # faultWindow = MessageWindow(self, name, text)
                    # faultWindow.wait_window()
                    # self.discharge()
        
        updateHVStatus()
        updatePressureStatus()
        updatePowerSupplyStatus()

        self.after(int(1000 / refreshRate), self.updateSystemStatus)

    def recordPressure(self):
        self.chamberBasePressure = 8e-7
        self.pumpBasePressure = 2e-7

    def setData(self, data_dict):
        for plotOption, plotProperties in data_dict.items():
            for variable in plotProperties['lines'].keys():
                if hasattr(self, variable):
                    data_dict[plotOption]['lines'][variable].data = getattr(self, variable)

    def performAnalysis(self):
        print('Performing analysis...')
        analysis = Analysis(self.dischargeTime, self.dischargeTimeUnit, self.dischargeVoltage, self.dischargeCurrent,
                            self.dumpDelay, self.ignitronDelay, self.polarity)
        self.dischargeVoltageFiltered = analysis.voltage_filtered / 1000
        self.dischargeCurrentFiltered = analysis.current_filtered
        self.dumpCurrentFiltered = analysis.lowPassFilter(self.dumpCurrent)
        self.chamberProtectionCurrentFiltered = analysis.lowPassFilter(self.chamberProtectionCurrent)
        self.feedthroughVoltageFiltered = analysis.lowPassFilter(self.feedthroughVoltage) * 10
        self.feedthroughCurrentFiltered = analysis.lowPassFilter(self.feedthroughCurrent) / 10

        # Update the misc analysis text variables
        if analysis.success:
            for variable, textVariable in self.analysisText_dict.items():
                textVariable.set(f'{analysisVariables[variable]["label"]}: {getattr(analysis, variable) * analysisVariables[variable]["factor"]:.1f}')

        # Diamagnetic loops
        for variable, line in self.resultsPlotData['Diamagnetic']['lines'].items():
            if hasattr(self, variable):
                densityVariable = f'{variable}Density'
                signal = line.data
                density = analysis.get_diamagneticDensity(signal)
                setattr(self, densityVariable, density)

        self.setData(self.analysisPlotData)
        print('Analysis complete!')

    def saveDischarge(self):
            print('Saving discharge...')
            # Read from the scope
            if USING_SCOPE:
                print('Sleeping for 5 seconds to give scope its "me time"')	
                time.sleep(5)
                self.saveScope_thread = Thread(target=self.scope.read_scope)
                self.saveScope_thread.start()

            for i, variable in enumerate(self.diagnostics_Pins):
                setattr(self, variable, self.NI_DAQ.dischargeData[i,:])

            for i, variable in enumerate(self.counters_Pins):
                setattr(self, variable, 0)
                try:
                    setattr(self, variable, self.NI_DAQ.ci_tasks[variable].channels.ci_count)
                except:
                    setattr(self, variable, 0)
            
            self.dischargeCurrent /= pearsonCoilDischarge
            # self.dumpCurrent /= dumpResistance
            # self.chamberProtectionCurrent /= chamberProtectionResistance
            self.dischargeVoltage *= voltageDivider

            self.setData(self.resultsPlotData)

            self.preShotNotes = self.preShotNotesEntry.text.get('1.0', 'end')
            self.postShotNotes = self.postShotNotesEntry.text.get('1.0', 'end')    

            print('Discharge Saved!')      

    def reset(self):
        print('Reset')

        # Set gases to defaults
        self.primaryGas = self.primaryGasDefault
        self.secondaryGas = self.secondaryGasDefault
        self.primaryGasComboBox.current(gasOptions.index(self.primaryGasDefault))
        self.secondaryGasComboBox.current(gasOptions.index(self.secondaryGasDefault))

        # Close the switch tasks so we can close the switches with hardware instead of software
        if hasattr(self, 'NI_DAQ'):
            self.NI_DAQ.remove_tasks(self.NI_DAQ.dump_task_names + self.NI_DAQ.switch_task_names)

        # Open power supply and load and close dump
        self.operateSwitch('Enable HV', False)
        self.operateSwitch('Power Supply Switch', False)	
        time.sleep(switchWaitTime)	
        self.operateSwitch('Dump Switch', False)
        self.operateSwitch('Load Switch', False)

        # Clear user inputs
        for variable, entry in self.userEntries.items():
            entry.delete(0, 'end')
            if self.userInputs[variable]['default'] is not None:
                entry.insert(0, self.userInputs[variable]['default'])
        self.preShotNotesEntry.text.delete('1.0', 'end')
        self.postShotNotesEntry.text.delete('1.0', 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.discharged = False
        self.userInputsSet = False
        self.idleMode = True
        self.resultsSaved = False
        self.scopeDataSaved = False

        # Reset the charging time point
        self.timePoint = 0.0

        # Reset the discharge plot time axis
        self.dischargeTime = []
        self.dischargeTimeUnit = 's'

        # Reset the charge plot
        self.chargeVoltagePS = []
        self.chargeCurrentPS = []
        self.capacitorVoltage = []
        self.chargeTime = []

        # This condition executes every time except for the initialization
        if self.loggedIn:
            # Reset all plotted variables to empty array
            for variable, description in single_columns.items():
                if description['type'] == 'array' and hasattr(self, variable):
                    setattr(self, variable, np.array([]))

            # Reset all analysis variables to empty array
            for plotData in self.analysisPlotData.values():
                for variable in plotData['lines'].keys():
                    setattr(self, variable, np.array([]))

                if description['type'] == 'array' and hasattr(self, variable):
                    setattr(self, variable, np.array([]))

            self.setData(self.resultsPlotData)
            self.setData(self.analysisPlotData)

            # The filtered array is not in the list of saved variables, so set this equal to empty array as well
            self.capacitorVoltageFiltered = np.array([])

            # Reset ylim on charge plot
            self.chargePlot.ax.set_ylim(0, voltageYLim)
            self.chargeCurrentAxis.set_ylim(0, currentYLim)

            # Reset plots
            self.replotCharge()
            self.resultsPlotViewer.replot()
            self.analysisPlotViewer.replot()

        # Disable all buttons if logged in
        self.disableButtons()

        # Reset progress bar
        self.progressBar.configure(amountused=0)

        if hasattr(self, 'scope'):
            self.scope.reset() # Reset the scope