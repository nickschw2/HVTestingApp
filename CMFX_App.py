from TestingApp import *


# SAVE RESULTS EVEN WHEN THERE'S NO DISCHARGE
# CHANGE GUI TO LOOK MORE LIKE THAT IN TOKAMAK ENERGY PICTURE

class CMFX_App(TestingApp):
    def __init__(self):
        super().__init__()

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
        self.notebook = ttk.Notebook(self, takefocus=False)
        self.notebook.pack(expand=True, side='top')

        tabNames = ['System Status', 'Charging', 'Results']
        self.notebookFrames = {}
        for tabName in tabNames:
            frame = ttk.Frame(self.notebook)
            frame.pack(expand=True, fill='both')
            self.notebook.add(frame, text=tabName)
            self.notebookFrames[tabName] = frame

        #### SYSTEM STATUS SECTION ####
        # Add frames for text labels
        self.textStatusFrame = ttk.Frame(self.notebookFrames['System Status'])
        self.HVStatusFrame = ttk.LabelFrame(self.textStatusFrame, text='High Voltage Status')
        self.pressureStatusFrame = ttk.LabelFrame(self.textStatusFrame, text='Pressure Status')
        self.miscStatusFrame = ttk.LabelFrame(self.textStatusFrame, text='Misc. Status')

        # self.textStatusFrame.place(relx=0.5, rely=0.5, anchor='center')
        self.textStatusFrame.pack(side='left', expand=True, fill='both')
        self.HVStatusFrame.pack(side='top', expand=True)
        self.pressureStatusFrame.pack(side='top', expand=True)
        self.miscStatusFrame.pack(side='top', expand=True)

        # Create text variables for status indicators, associate with labels, and place
        self.voltagePSText = ttk.StringVar()
        self.currentPSText = ttk.StringVar()
        self.capacitorVoltageText = ttk.StringVar()
        self.pressureChamberText = ttk.StringVar()
        self.pressurePumpText = ttk.StringVar()

        self.voltagePSLabel = ttk.Label(self.HVStatusFrame, textvariable=self.voltagePSText)
        self.currentPSLabel = ttk.Label(self.HVStatusFrame, textvariable=self.currentPSText)
        self.capacitorVoltageLabel = ttk.Label(self.HVStatusFrame, textvariable=self.capacitorVoltageText)
        self.pressureChamberLabel = ttk.Label(self.pressureStatusFrame, textvariable=self.pressureChamberText)
        self.pressurePumpLabel = ttk.Label(self.pressureStatusFrame, textvariable=self.pressurePumpText)
        self.bankCapacitanceLabel = ttk.Label(self.miscStatusFrame, text=f'Bank Capacitance: {capacitance} uF')

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pressureChamberLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pressurePumpLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.bankCapacitanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

        # Add textboxes for adding notes about a given shot
        self.userNotesFrame = ttk.Frame(self.notebookFrames['System Status'])
        self.preShotNotesFrame = ttk.LabelFrame(self.userNotesFrame, text='Pre-Shot Notes')
        self.postShotNotesFrame = ttk.LabelFrame(self.userNotesFrame, text='Post-Shot Notes')

        # self.userNotesFrame.place(relx=0.5, rely=0.5, anchor='center')
        self.userNotesFrame.pack(side='left', expand=True, fill='both')
        self.preShotNotesFrame.pack(side='top', expand=True)
        self.postShotNotesFrame.pack(side='top', expand=True)

        self.preShotNotesEntry = scrolled.ScrolledText(self.preShotNotesFrame, height=10)
        self.postShotNotesEntry = scrolled.ScrolledText(self.postShotNotesFrame, height=10)

        self.preShotNotesButton = ttk.Button(self.preShotNotesFrame, text='Record', command=self.recordPreShotNotes)
        self.postShotNotesButton = ttk.Button(self.postShotNotesFrame, text='Record', command=self.recordPostShotNotes)

        self.preShotNotesEntry.pack(side='left', expand=True)
        self.postShotNotesEntry.pack(side='left', expand=True)
        self.preShotNotesButton.pack(side='right', expand=True)
        self.postShotNotesButton.pack(side='right', expand=True)

        #### CHARGING SECTION ####
        # Add charging input to notebook
        self.userInputs = ttk.LabelFrame(self.notebookFrames['Charging'], text='User Inputs')
        self.userInputs.pack(side='top', expand=True)

        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):')
        self.gasPuffLabel = ttk.Label(self.userInputs, text='Gas Puff time (ms):')

        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth)
        self.gasPuffEntry = ttk.Entry(self.userInputs, width=userInputWidth)

        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, style='Accent.TButton')

        self.chargeVoltageLabel.pack(side='left', expand=True)
        self.chargeVoltageEntry.pack(side='left', expand=True, padx=(0, userInputPadding))
        self.gasPuffLabel.pack(side='left', expand=True)
        self.gasPuffEntry.pack(side='left', expand=True, padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left', expand=True)

        # Add validation to user inputs
        validation.add_range_validation(self.chargeVoltageEntry, 0, maximumValidVoltage, when='focus')
        validation.add_range_validation(self.gasPuffEntry, 0, maximumValidGasPuff, when='focus')

        # New frame for plot and other indicators in one row
        self.chargingStatusFrame = ttk.Frame(self.notebookFrames['Charging'])
        self.chargingStatusFrame.pack(side='top', expand=True)

        # Frame for indicators
        self.chargingIndicatorsFrame = ttk.Frame(self.chargingStatusFrame)
        self.chargingIndicatorsFrame.pack(side='left', expand=True)

        # Add progress bar to notebook
        self.progressBar = ttk.widgets.Meter(master=self.chargingIndicatorsFrame,
                                             stripethickness=10, subtext='Charging', textright='%')
        self.progressBar.pack(side='top', expand=True)

        # Add status variables, associate with labels, and place them
        self.chargeStateText = ttk.StringVar()

        self.chargeStateLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.chargeStateText)

        self.chargeStateLabel.pack(side='top', expand=True)

        # Plot of charge
        self.chargePlot = CanvasPlot(self.chargingStatusFrame, figsize=(10, 4))
        self.chargePlot.ax.grid(which='both')

        # Create two y-axes for current and voltage
        self.chargeVoltageAxis = self.chargePlot.ax
        self.chargeCurrentAxis = self.chargePlot.ax.twinx()

        self.chargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.chargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.chargePlot.ax.set_xlabel('Time (s)')

        self.chargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.chargeCurrentAxis.set_ylabel('Current (mA)', color=currentColor)

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
        self.chargePlotToolbar = NavigationToolbar2Tk(self.chargePlot.canvas, self.chargingStatusFrame)
        self.chargePlotToolbar.update()

        # Place plot with toolbar in frame
        self.chargePlot.pack(side='right', expand=True)

        # Row for buttons on the bottom
        self.buttons = ttk.LabelFrame(self.notebookFrames['Charging'], text='Operate Capacitor')
        self.buttons.pack(side='top', expand=True)

        # Button definitions and placement
        self.checklistButton = ttk.Button(self.buttons, text='Checklist Complete',
                                    command=self.checklist, style='Accent.TButton')
        self.chargeButton = ttk.Button(self.buttons, text='Charge',
                                    command=self.charge, style='Accent.TButton')
        self.dischargeButton = ttk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, style='Accent.TButton')
        self.resetButton = ttk.Button(self.buttons, text='Reset',
                                    command=self.reset, style='Accent.TButton')

        self.checklistButton.pack(side='left', expand=True, padx=buttonPadding)
        self.chargeButton.pack(side='left', expand=True, padx=buttonPadding)
        self.dischargeButton.pack(side='left', expand=True, padx=buttonPadding)
        self.resetButton.pack(side='left', expand=True, padx=buttonPadding)

        #### RESULTS SECTION ####
        # Frame for displaying the results plots
        self.resultsPlotFrame = ttk.Frame(self.notebookFrames['Results'])
        self.resultsPlotFrame.pack(side='right', expand=True)

        # Add plot and toolbar to frame
        self.resultsPlot = CanvasPlot(self.resultsPlotFrame, figsize=(10, 4))
        self.resultsPlot.ax.grid(which='both')
        self.resultsPlotToolbar = NavigationToolbar2Tk(self.resultsPlot.canvas, self.resultsPlotFrame)
        self.resultsPlotToolbar.update()

        self.resultsPlot.pack(side='top', expand=True)

        # Frame for selecting which plots to show
        self.selectorFrame = ttk.LabelFrame(self.notebookFrames['Results'], text='Plot Selector')
        self.selectorFrame.pack(side='left', expand=True, anchor='n')

        # Selector for showing a certain plot
        plotOptions = list(resultsPlots.keys())
        self.resultsPlotCombobox = ttk.Combobox(self.selectorFrame, value=plotOptions, state='readonly', **text_opts)
        self.resultsPlotCombobox.current(0) # Initializes the current value to first option
        self.resultsPlotCombobox.bind('<<ComboboxSelected>>', self.changeResultsPlot)
        self.resultsPlotCombobox.pack(side='top', expand=True)

        # Initialize checkbuttons
        self.resultsCheckbuttons = {}
        for plotOption, plotProperties in resultsPlots.items():
            # Need to create a dictionary for each checkbutton corresponding to its label
            self.resultsCheckbuttons[plotOption] = {}
            for label in plotProperties['lines']:
                checkbutton = ttk.Checkbutton(self.selectorFrame, text=label, style='Switch.TCheckbutton')
                checkbutton.invoke() # Initialize it to be turned on
                checkbutton.bind('<Button>', self.changeResultsPlot)
                self.resultsCheckbuttons[plotOption][label] = checkbutton

        # Set initial state, have to pass a dummy variable
        self.changeResultsPlot(None)

        #### CONSOLE SECTION ####
        # Create frame to hold console and scroll bar
        self.consoleFrame = ttk.LabelFrame(self, text='Console')
        self.consoleFrame.pack(fill='x', side='bottom', expand=True)

        # Console will output the sys.stdout messages
        # Scrollbar is attached to console
        # self.scrollbar = ttk.Scrollbar(self.consoleFrame, orient='vertical')
        # self.scrollbar.pack(side='right', fill='y')

        # Height is number of lines to be displayed
        # Link the textbox to scrollbar as well so that the length of bar corresponds
        self.console = Console(self.consoleFrame, height=10)
        # self.scrollbar.config(command=self.console.yview)
        self.console.pack(side='left', fill='x', expand=True)

        # Menubar at the top
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
        print('init_ui')
        # Begin the operation of the program
        # center the app
        self.eval('tk::PlaceWindow . center')

        # Reset all fields on startup
        self.loggedIn = False
        self.reset()

        if ADMIN_MODE:
            self.loggedIn = True
            self.saveFolder = 'C:/Users/Control Room/programs/HVCapTestingApp/CMFX'
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

    def recordPreShotNotes(self):
        self.preShotNotes = self.preShotNotesEntry.text.get('1.0', 'end')
        print('Pre-shot notes recorded')

    def recordPostShotNotes(self):
        self.postShotNotes = self.postShotNotesEntry.text.get('1.0', 'end')
        print('Post-shot notes recorded')

    def setUserInputs(self):
        def incorrectUserInput(text):
                incorrectUserInputName = 'Invalid Input'
                incorrectUserInputWindow = MessageWindow(self, incorrectUserInputName, text)

        if not self.chargeVoltageEntry.validate():
            self.chargeVoltageEntry.delete(0, 'end')

            self.checklistButton.configure(state='disabled')

            # CHANGE: NEED TO EVENTUALLY CHANGE THE MAX VALUE OF CHARGE IN VALIDATE AND MESSAGE
            incorrectUserInputText = f'Please reenter a valid number for the charge voltage. The maximum voltage for this capacitor is 100 kV.'
            incorrectUserInput(incorrectUserInputText)
            
        else:
            self.userInputsSet = True
            self.chargeVoltage = float(self.chargeVoltageEntry.get())

            # Set the scale on the oscilloscope based on inputs
            if not DEBUG_MODE:
                self.scope.setScale(self.chargeVoltage, capacitance)

            # Check if the save folder has been selected, and if so allow user to begin checklist
            if self.saveFolderSet:
                self.checklistButton.configure(state='normal')

            # Display pop up window to let user know that values have been set
            setUserInputName = 'User Inputs Set!'
            setUserInputText = 'User inputs have been set. They may be changed at any time for any subsequent run.'
            setUserInputWindow = MessageWindow(self, setUserInputName, setUserInputText)

    def updateSystemStatus(self):
        # Updates HV Status Frame
        def updateHVStatus():
            voltagePSPoint = np.nan	
            currentPSPoint = np.nan	
            self.capacitorVoltagePoint = np.nan

            # not applicable on startup	
            if hasattr(self, 'NI_DAQ'):	
                if not DEBUG_MODE:	
                    voltages = self.NI_DAQ.data	
                else:	
                    voltages = self.getChargingTestVoltages()

                # Update charging values in object while not discharged
                if self.charging:
                    self.chargeVoltagePS = voltages['Power Supply Voltage'] * maxVoltagePowerSupply / maxVoltageInput	
                    self.chargeCurrentPS = (voltages['Power Supply Current'] + 10) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason	
                    self.capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider * attenuator	
                    
                    # Capacitor signal is very noisy, so apply moving average filter over a period of 2 seconds	
                    # Also don't want to filter over nan's
                    nanIndices = np.isnan(self.capacitorVoltage)	
                    self.capacitorVoltageFiltered = uniform_filter1d(self.capacitorVoltage[~nanIndices], size=sample_rate * 2)	
                    voltagePSPoint = self.chargeVoltagePS[-1]
                    currentPSPoint = self.chargeCurrentPS[-1]
                    self.capacitorVoltagePoint = self.capacitorVoltageFiltered[-1]
                    
                
                else:
                    chargeVoltagePS = voltages['Power Supply Voltage'] * maxVoltagePowerSupply / maxVoltageInput	
                    chargeCurrentPS = (voltages['Power Supply Current'] + 10) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason	
                    capacitorVoltage = voltages['Capacitor Voltage'] * voltageDivider * attenuator	
                    
                    # Capacitor signal is very noisy, so apply moving average filter over a period of 2 seconds	
                    # Also don't want to filter over nan's
                    nanIndices = np.isnan(capacitorVoltage)	
                    capacitorVoltageFiltered = uniform_filter1d(capacitorVoltage[~nanIndices], size=sample_rate * 2)	
                    voltagePSPoint = chargeVoltagePS[-1]
                    currentPSPoint = chargeCurrentPS[-1]
                    self.capacitorVoltagePoint = capacitorVoltageFiltered[-1]

            self.voltagePSText.set(f'Power Supply V: {voltagePSPoint / 1000:.2f} kV')	
            self.currentPSText.set(f'Power Supply I: {currentPSPoint * 1000:.2f} mA')
            self.capacitorVoltageText.set(f'Capacitor V: {self.capacitorVoltagePoint / 1000:.2f} kV')	

            if not self.idleMode:	
                self.progressBar.configure(amountused = int(100 * self.capacitorVoltagePoint / 1000 / self.chargeVoltage))

            # Logic heirarchy for charge state and countdown text
            if self.discharged:
                self.chargeStateText.set('Discharged!')
            elif self.charged:
                self.chargeStateText.set('Charged')
            else:
                self.chargeStateText.set('Not Charged')

            if self.charging:
                N = len(self.chargeVoltagePS)	
                self.chargeTime = np.linspace(0, N / sample_rate, N)	
                self.timePoint = (N - 1) / sample_rate

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
                if self.capacitorVoltagePoint >= chargeVoltageLimit * self.chargeVoltage * 1000 and not self.discharged:
                    self.charged = True

                    # Actually begin discharging power supply before opening power supply switch so it doesnt overshoot
                    self.powerSupplyRamp(action='discharge')

                    # Open power supply switch
                    self.operateSwitch('Power Supply Switch', False)

                    # Have to set discharged to True and charging to False before starting discharge thread	
                    self.discharged = True	
                    self.charging = False	
                    thread = Thread(target=self.discharge)	
                    thread.start()

        def updatePressureStatus():
            self.pressureChamberText.set('Pressure @ Chamber:')
            self.pressurePumpText.set('Pressure @ Pump:')
        
        updateHVStatus()
        updatePressureStatus()

        self.after(int(1000 / refreshRate), self.updateSystemStatus)

    def saveDischarge(self):
            # Read from the load
            if not DEBUG_MODE:
                print('Sleeping for 5 seconds to give scope its "me time"')	
                time.sleep(5)
                self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
                self.diamagnetic = self.scope.get_data(self.scopePins['Diamagnetic'])
                self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()
                
            else:
                self.dischargeVoltageLoad, self.dischargeCurrentLoad, self.dischargeTime, self.dischargeTimeUnit = self.getDischargeTestValues()

            if len(self.dischargeTime) != 0:
                # Plot results on the discharge graph and save them
                # The only time results are saved is when there is a discharge that is preceded by charge
                self.replotCharge()
                self.replotDischarge()

                self.saveResults()

            else:
                print('Oscilloscope was not triggered successfully')

    def replotDischarge(self):
        # Remove lines every time the figure is plotted
        self.clearFigLines(self.dischargePlot.fig)
        self.dischargeVoltageAxis.set_xlabel(f'Time ({self.dischargeTimeUnit})')

        # Add plots NEED TO FINISH
        self.dischargeLines['voltage'] = voltage
        self.dischargeLines['current'] = current

    def readResults(self):
        print('read results')

    def changeResultsPlot(self, event):
        # Get value of combobox and associated checkbuttons
        plotSelection = self.resultsPlotCombobox.get()
        checkbuttons = self.resultsCheckbuttons[plotSelection]

        # Need to tell if event came from the combobox or a checkbutton
        # event==None is for dummy variable instantiation
        if event==None or isinstance(event.widget, ttk.Combobox):
            # Remove current checkbuttons
            for widget in self.selectorFrame.winfo_children():
                if isinstance(widget, ttk.Checkbutton) and widget.winfo_ismapped():
                    widget.pack_forget()

            # Remove current lines from plot
            self.clearFigLines(self.resultsPlot.fig)

            # Change checkbuttons to new selection
            for checkbutton in checkbuttons.values():
                checkbutton.pack(expand=True, anchor='w')

            # Change plot to new selection
            plotProperties = resultsPlots[plotSelection]
            axis = self.resultsPlot.ax
            axis.set_xlabel(f'Time ({timeUnit})')
            axis.set_ylabel(plotProperties['ylabel'])
            axis.set_prop_cycle(None) # Reset the color cycle

            # Some place to store the current lines on the plot to change visibility later
            self.currentLines = {}
            for label, data in plotProperties['lines'].items():
                visible = checkbuttons[label].instate(['selected'])
                line = axis.plot(timeArray, data, label=label, visible=visible)
                self.currentLines[label] = line[0]

            axis.legend()

        # Change visibility of line when the checkbutton for that line is changed
        elif isinstance(event.widget, ttk.Checkbutton):
            label = event.widget.cget('text')
            line = self.currentLines[label]
            visible = checkbuttons[label].instate(['!selected'])
            line.set_visible(visible)

            self.resultsPlot.ax.legend()

        # Update plot
        self.resultsPlot.updatePlot()

    def reset(self):
        print('Reset')

        # Open power supply and voltage divider switch and close load switch	
        self.operateSwitch('Power Supply Switch', False)	
        time.sleep(switchWaitTime)	
        self.operateSwitch('Load Switch', False)	
        self.operateSwitch('Voltage Divider Switch', False)

        # Clear user inputs
        self.chargeVoltageEntry.delete(0, 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.idleMode = True

        # Reset plots
        self.resetPlot(self.chargePlot)
        self.resetPlot(self.resultsPlot)

        # Disable all buttons if logged in
        self.disableButtons()

        # Reset progress bar
        self.progressBar.configure(amountused = 0)

        if hasattr(self, 'scope'):
            self.scope.reset() # Reset the scope