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

        # Create and show user interface
        self.configure_ui()
        self.init_ui()

        # Connect to instruments
        if not DEBUG_MODE:
            self.init_DAQ()
            self.init_PulseGenerator()

    def configure_ui(self):
        # set title
        self.title('CMFX App')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        # Notebook creates tabs at the top
        self.notebook = ttk.Notebook(self, takefocus=False, bootstyle='primary')
        self.notebook.pack(expand=True, side='top', padx=framePadding, pady=framePadding)

        tabNames = ['System Status', 'Charging', 'Results', 'Analysis']
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
        self.circuitValuesFrame = ttk.LabelFrame(self.textStatusFrame, text='Circuit Values', width=systemStatusFrameWidth, height=150, bootstyle='primary')

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
        self.dumpResistanceLabel = ttk.Label(self.circuitValuesFrame, text=f'Dump Resistance: {self.dumpResistance:.2f} {Omega}')

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.chamberPressureLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pumpPressureLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.bankCapacitanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.ballastResistanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.dumpResistanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

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

        #### CHARGING SECTION ####
        # Add charging input to notebook
        self.userInputs = ttk.LabelFrame(self.notebookFrames['Charging'], text='User Inputs', bootstyle='primary')
        self.userInputs.pack(side='top', expand=True, pady=(framePadding, 0))

        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):')
        self.gasPuffLabel = ttk.Label(self.userInputs, text='Gas Puff Time (ms):')
        self.dumpDelayLabel = ttk.Label(self.userInputs, text='Dump Delay (ms):')

        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth, font=('Helvetica', 12))
        self.gasPuffEntry = ttk.Entry(self.userInputs, width=userInputWidth, font=('Helvetica', 12))
        self.dumpDelayEntry = ttk.Entry(self.userInputs, width=userInputWidth, font=('Helvetica', 12))

        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, bootstyle='primary')

        self.chargeVoltageLabel.pack(side='left', expand=True, padx=(labelPadding, 0), pady=labelPadding)
        self.chargeVoltageEntry.pack(side='left', expand=True, padx=(0, userInputPadding), pady=labelPadding)
        self.gasPuffLabel.pack(side='left', expand=True, pady=labelPadding)
        self.gasPuffEntry.pack(side='left', expand=True, padx=(0, userInputPadding), pady=labelPadding)
        self.dumpDelayLabel.pack(side='left', expand=True, pady=labelPadding)
        self.dumpDelayEntry.pack(side='left', expand=True, padx=(0, userInputPadding), pady=labelPadding)
        self.userInputOkayButton.pack(side='left', expand=True, padx=(0, labelPadding), pady=labelPadding)

        # Add validation to user inputs
        validation.add_range_validation(self.chargeVoltageEntry, 0, maxValidVoltage, when='focus')
        validation.add_range_validation(self.gasPuffEntry, 0, maxValidGasPuff, when='focus')
        validation.add_range_validation(self.dumpDelayEntry, 0, maxValidDumpDelay, when='focus')

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
        self.bm = BlitManager(self.chargePlot.canvas, [self.chargeVoltageLine, self.chargeCurrentLine, self.capacitorVoltageLine, self.chargePlot.ax.xaxis, self.chargePlot.ax.yaxis])

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
        self.chargeButton = ttk.Button(self.buttons, text='Charge',
                                    command=self.charge, bootstyle='warning')
        self.dischargeButton = ttk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bootstyle='danger')

        self.checklistButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)
        self.chargeButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)
        self.dischargeButton.pack(side='left', expand=True, padx=buttonPadding, pady=labelPadding)

        #### RESULTS SECTION ####
        # Initialize the data structure to hold results plot
        self.resultsPlotData = {'Voltage': {'twinx': False, 'ylabel': 'Voltage (kV)', 'lines': voltageLines},
                                'Current': {'twinx': False, 'ylabel': 'Current (A)', 'lines': currentLines},
                                'Diamagnetic': {'twinx': False, 'ylabel': 'Diamagnetic (V)', 'lines': diamagneticLines},
                                'BR': {'twinx': False, 'ylabel': 'B_$R$ (V)', 'lines': BRLines},
                                'Interferometer': {'twinx': False, 'ylabel': 'Interferometer (V)', 'lines': interferometerLines}}
        
        self.resultsPlotViewer = PlotViewer(self.notebookFrames['Results'], self.resultsPlotData)

        #### ANALYSIS SECTION ####
        # Initialize the data structure to hold results plot
        self.analysisPlotData = {'Diamagnetic': {'twinx': False, 'ylabel': 'Density ($10^{18}$ m$^{-3}$)', 'lines': diamagneticAnalysisLines}}
        
        self.analysisPlotViewer = PlotViewer(self.notebookFrames['Analysis'], self.analysisPlotData)

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

    def setUserInputs(self):
        def incorrectUserInput(text):
                incorrectUserInputName = 'Invalid Input'
                MessageWindow(self, incorrectUserInputName, text)

        if not self.chargeVoltageEntry.validate() or len(self.chargeVoltageEntry.get()) == 0:
            self.chargeVoltageEntry.delete(0, 'end')

            self.checklistButton.configure(state='disabled')

            incorrectUserInputText = f'Please reenter a valid number for the charge voltage. The maximum voltage for this capacitor is {maxValidVoltage} kV.'
            incorrectUserInput(incorrectUserInputText)

        elif not self.gasPuffEntry.validate() or len(self.gasPuffEntry.get()) == 0:
            self.gasPuffEntry.delete(0, 'end')

            self.checklistButton.configure(state='disabled')

            incorrectUserInputText = f'Please reenter a valid number for the gas puff time. The maximum time for the gas puff is {maxValidGasPuff} ms.'
            incorrectUserInput(incorrectUserInputText)

        elif not self.dumpDelayEntry.validate() or len(self.dumpDelayEntry.get()) == 0:
            self.dumpDelayEntry.delete(0, 'end')

            self.checklistButton.configure(state='disabled')

            incorrectUserInputText = f'Please reenter a valid number for the dump delay time. The maximum time for the dump delay is {maxValidDumpDelay} ms.'
            incorrectUserInput(incorrectUserInputText)
            
        else:
            self.userInputsSet = True
            self.chargeVoltage = float(self.chargeVoltageEntry.get())
            self.gasPuffTime = float(self.gasPuffEntry.get())
            self.dumpDelay = float(self.dumpDelayEntry.get())

            # Set the scale on the oscilloscope based on inputs
            # if not DEBUG_MODE:
            #     # self.scope.setScale(self.chargeVoltage)
            #     self.pulseGenerator.setDelay(pulseGeneratorOutputs['dumpIgnitron']['chan'], self.dumpDelay / 1000)

            # Check if the save folder has been selected, and if so allow user to begin checklist
            if self.saveFolderSet:
                self.checklistButton.configure(state='normal')

            # Display pop up window to let user know that values have been set
            setUserInputName = 'User Inputs Set!'
            setUserInputText = 'User inputs have been set. They may be changed at any time for any subsequent run.'
            MessageWindow(self, setUserInputName, setUserInputText)

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
                    self.chargeVoltagePS = (voltages['Power Supply Voltage']) * maxVoltagePowerSupply / maxVoltageInput	
                    self.chargeCurrentPS = (voltages['Power Supply Current']) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason	
                    self.capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider	
                    
                    voltagePSPoint = self.chargeVoltagePS[-1]
                    currentPSPoint = self.chargeCurrentPS[-1]
                    capacitorVoltagePoint = self.capacitorVoltage[-1]
                
                else:
                    chargeVoltagePS = (voltages['Power Supply Voltage']) * maxVoltagePowerSupply / maxVoltageInput	
                    chargeCurrentPS = (voltages['Power Supply Current']) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason	
                    capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider
                    	
                    voltagePSPoint = chargeVoltagePS[-1]
                    currentPSPoint = chargeCurrentPS[-1]
                    capacitorVoltagePoint = capacitorVoltage[-1]

            self.voltagePSText.set(f'Power Supply V: {voltagePSPoint / 1000:.2f} kV')	
            self.currentPSText.set(f'Power Supply I: {currentPSPoint * 1000:.2f} mA')
            self.capacitorVoltageText.set(f'Capacitor V: {capacitorVoltagePoint / 1000:.2f} kV')	

            if not self.idleMode:	
                self.progressBar.configure(amountused = int(100 * capacitorVoltagePoint / 1000 / self.chargeVoltage))

            # Logic heirarchy for charge state and countdown text
            if self.discharged:
                self.chargeStateText.set('Discharged!')

                self.dischargeTime = self.NI_DAQ.dischargeTime
                self.dischargeTimeUnit = self.NI_DAQ.tUnit

                # Once the save thread has finished, then we can replot the discharge results
                if hasattr(self, 'saveDischarge_thread') and not self.saveDischarge_thread.is_alive() and not self.resultsSaved:
                    # Show results tab once finished plotting
                    self.notebook.select(2)
                    self.resultsSaved = True

                    print('Saving results to file and replotting...')
                    
                    # Start saving on separate threads
                    Thread(target=self.saveResults).start()

                    # Analyze results and plot those as well
                    self.performAnalysis()

                    # Can't replot results on a separate thread from the main because it throws run time error
                    self.resultsPlotViewer.replot()
                    self.analysisPlotViewer.replot()

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
                if capacitorVoltagePoint >= chargeVoltageLimit * self.chargeVoltage * 1000 and not self.charged:
                    # Actually begin discharging power supply before opening power supply switch so it doesnt overshoot
                    self.powerSupplyRamp(action='discharge')

                    # Open power supply switch
                    self.operateSwitch('Power Supply Switch', False)

                    # Have to set charged to True before starting discharge thread
                    self.charged = True
                    thread = Thread(target=self.discharge)	
                    thread.start()

        def updatePressureStatus():
            chamberPressure = 8e-4
            pumpPressure = 2e-4
            self.chamberPressureText.set(f'Chamber Press.: {chamberPressure:.1e} Torr')
            self.pumpPressureText.set(f'Pump Press.: {pumpPressure:.1e} Torr')
        
        updateHVStatus()
        updatePressureStatus()

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
        analysis = Analysis(self.dischargeTime, self.dischargeTimeUnit)

        # Diamagnetic loops
        for variable, line in self.resultsPlotData['Diamagnetic']['lines'].items():
            densityVariable = f'{variable}Density'
            signal = line.data
            density = analysis.analyzeDiamagnetic(signal)
            setattr(self, densityVariable, density)

        self.setData(self.analysisPlotData)
        print('Analysis complete!')

    def saveDischarge(self):
            print('Saving discharge...')
            # Read from the load
            # if not DEBUG_MODE:
            #     print('Sleeping for 5 seconds to give scope its "me time"')	
            #     time.sleep(5)
            #     dischargeVoltage = self.scope.get_data(self.scopePins['Discharge Voltage']) * voltageDivider
            #     # diamagneticAxial = self.scope.get_data(self.scopePins['diamagneticAxial'])
            #     # dischargeCurrent = self.scope.get_data(self.scopePins['Discharge Current']) / pearsonCoilDischarge
            #     # interferometer = self.scope.get_data(self.scopePins['Interferometer'])
            #     # trigger = self.scope.get_data(self.scopePins['Trigger'])
            #     dischargeTimeScope, dischargeTimeScopeUnit  = self.scope.get_time()
                
            # else:
            #     dischargeVoltage, dischargeCurrentLoad, dischargeTimeScope, dischargeTimeScopeUnit = self.getDischargeTestValues()

            # if len(dischargeTimeScope) != 0:
            #     # Plot results on the discharge graph and save them
            #     # The only time results are saved is when there is a discharge that is preceded by charge
            #     self.replotCharge()
            #     self.replotDischarge()

            #     self.saveResults()

            # else:
            #     print('Oscilloscope was not triggered successfully')

            for i, variable in enumerate(self.diagnostics_Pins):
                setattr(self, variable, self.NI_DAQ.dischargeData[i,:])
            
            self.dischargeCurrent /= pearsonCoilDischarge
            self.dumpCurrent /= dumpResistance
            self.dischargeVoltage *= voltageDivider

            # Transform scope data to be on same timebase as daq
            # self.dischargeVoltage = np.interp(self.NI_DAQ.dischargeTime, dischargeTimeScope, dischargeVoltage, left=np.nan, right=np.nan)
            # self.diamagneticAxial = np.interp(self.NI_DAQ.dischargeTime, dischargeTimeScope, diamagneticAxial, left=np.nan, right=np.nan)
            # self.dischargeCurrent = np.interp(self.NI_DAQ.dischargeTime, dischargeTimeScope, dischargeCurrent, left=np.nan, right=np.nan)
            # self.interferometer = np.interp(self.NI_DAQ.dischargeTime, dischargeTimeScope, interferometer, left=np.nan, right=np.nan)
            # self.trigger = np.interp(self.NI_DAQ.dischargeTime, dischargeTimeScope, trigger, left=np.nan, right=np.nan)
            # self.interferometer = self.diamagneticRadial
            # self.dischargeVoltage = self.diamagneticRadial

            self.setData(self.resultsPlotData)

            self.preShotNotes = self.preShotNotesEntry.text.get('1.0', 'end')
            self.postShotNotes = self.postShotNotesEntry.text.get('1.0', 'end')    

            print('Discharge Saved!')      

    def reset(self):
        print('Reset')

        # Open power supply and close load and dump
        self.operateSwitch('Power Supply Switch', False)	
        time.sleep(switchWaitTime)	
        self.operateSwitch('Load Switch', False)	
        self.operateSwitch('Dump Switch', False)

        # Clear user inputs
        self.chargeVoltageEntry.delete(0, 'end')
        self.gasPuffEntry.delete(0, 'end')
        self.dumpDelayEntry.delete(0, 'end')
        self.preShotNotesEntry.text.delete('1.0', 'end')
        self.postShotNotesEntry.text.delete('1.0', 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.discharged = False
        self.userInputsSet = False
        self.idleMode = True
        self.resultsSaved = False

        # Reset the charging time point
        self.timePoint = 0.0

        # Reset the discharge plot time axis
        self.dischargeTime = []
        self.dischargeTimeUnit = 's'

        # This condition executes every time except for the initialization
        if self.loggedIn:
            # Resets discharge trigger
            self.NI_DAQ.reset_discharge_trigger()

            # Reset all plotted variables to empty array
            for variable, description in single_columns.items():
                if description['type'] == 'array' and hasattr(self, variable):
                    setattr(self, variable, np.array([]))

            self.setData(self.resultsPlotData)
            self.setData(self.analysisPlotData)

            # The filtered array is not in the list of saved variables, so set this equal to empty array as well
            self.capacitorVoltageFiltered = np.array([])

            # Reset ylim on charge plot
            self.chargePlot.ax.set_ylim(0, voltageYLim)

            # Reset plots
            self.replotCharge()
            self.resultsPlotViewer.replot()
            self.analysisPlotViewer.replot()

        # Disable all buttons if logged in
        self.disableButtons()

        # Reset progress bar
        self.progressBar.configure(amountused = 0)

        # if hasattr(self, 'scope'):
        #     self.scope.reset() # Reset the scope