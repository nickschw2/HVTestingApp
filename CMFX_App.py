from TestingApp import *

# SAVE RESULTS EVEN WHEN THERE'S NO DISCHARGE

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
            frame.pack(expand=True)
            self.notebook.add(frame, text=tabName)
            self.notebookFrames[tabName] = frame

        #### SYSTEM STATUS SECTION ####
        # Add frames for text labels
        self.HVStatusFrame = ttk.LabelFrame(self.notebookFrames['System Status'], text='High Voltage Status')
        self.pressureStatusFrame = ttk.LabelFrame(self.notebookFrames['System Status'], text='Pressure Status')
        self.miscStatusFrame = ttk.LabelFrame(self.notebookFrames['System Status'], text='Misc. Status')

        self.HVStatusFrame.pack(side='left')
        self.pressureStatusFrame.pack(side='left')
        self.miscStatusFrame.pack(side='left')

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
        self.bankCapacitanceLabel = ttk.Label(self.miscStatusFrame, text=f'Bank Capacitance: {72} uF')

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pressureChamberLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.pressurePumpLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.bankCapacitanceLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

        #### CHARGING SECTION ####
        # Add charging input to notebook
        self.userInputs = ttk.LabelFrame(self.notebookFrames['Charging'], text='User Inputs')
        self.userInputs.pack(side='top')

        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):')
        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth)
        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, style='Accent.TButton')

        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')

        # New frame for plot and other indicators in one row
        self.chargingStatusFrame = ttk.Frame(self.notebookFrames['Charging'])
        self.chargingStatusFrame.pack(side='top')

        # Frame for indicators
        self.chargingIndicatorsFrame = ttk.Frame(self.chargingStatusFrame)
        self.chargingIndicatorsFrame.pack(side='left')

        # Add progress bar to notebook
        self.progressBar = ttk.widgets.Meter(master=self.chargingIndicatorsFrame,
                                             stripethickness=10, subtext='Charging', textright='%')
        self.progressBar.pack(side='top')

        # Add status variables, associate with labels, and place them
        self.chargeStateText = ttk.StringVar()
        self.countdownText = ttk.StringVar()

        self.chargeStateLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.chargeStateText)
        self.countdownLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.countdownText)

        self.chargeStateLabel.pack(side='top')
        self.countdownLabel.pack(side='top')

        # Plot of charge
        self.chargePlot = CanvasPlot(self.chargingStatusFrame, figsize=(10, 4))

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
        self.chargePlot.pack(side='right')

        # Row for buttons on the bottom
        self.buttons = ttk.LabelFrame(self.notebookFrames['Charging'], text='Operate Capacitor')
        self.buttons.pack(side='top')

        # Button definitions and placement
        self.checklistButton = ttk.Button(self.buttons, text='Checklist Complete',
                                    command=self.checklist, style='Accent.TButton')
        self.chargeButton = ttk.Button(self.buttons, text='Charge',
                                    command=self.charge, style='Accent.TButton')
        self.dischargeButton = ttk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, style='Accent.TButton')
        self.resetButton = ttk.Button(self.buttons, text='Reset',
                                    command=self.reset, style='Accent.TButton')

        self.checklistButton.pack(side='left', padx=buttonPadding)
        self.chargeButton.pack(side='left', padx=buttonPadding)
        self.dischargeButton.pack(side='left', padx=buttonPadding)
        self.resetButton.pack(side='left', padx=buttonPadding)

        #### RESULTS SECTION ####
        # Frame for displaying the results plots
        self.resultsPlotFrame = ttk.Frame(self.notebookFrames['Results'])
        self.resultsPlotFrame.pack(side='right')

        # Add plot and toolbar to frame
        self.resultsPlot = CanvasPlot(self.resultsPlotFrame, figsize=(10, 4))
        self.resultsPlot.ax.grid(which='both')
        self.resultsPlotToolbar = NavigationToolbar2Tk(self.resultsPlot.canvas, self.resultsPlotFrame)
        self.resultsPlotToolbar.update()

        self.resultsPlot.pack()

        # Frame for selecting which plots to show
        self.selectorFrame = ttk.LabelFrame(self.notebookFrames['Results'], text='Plot Selector')
        self.selectorFrame.pack(side='left', anchor='n')

        # Selector for showing a certain plot
        plotOptions = list(resultsPlots.keys())
        self.resultsPlotCombobox = ttk.Combobox(self.selectorFrame, value=plotOptions, state='readonly', **text_opts)
        self.resultsPlotCombobox.current(0) # Initializes the current value to first option
        self.resultsPlotCombobox.bind('<<ComboboxSelected>>', self.changeResultsPlot)
        self.resultsPlotCombobox.pack(side='top')

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
        self.consoleFrame.pack(fill='x', side='bottom')

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
        self.chargeStateText.set('Idle')
        self.countdownText.set('Coundtown: Idle')
        self.voltagePSText.set('Power Supply Voltage')
        self.currentPSText.set('Power Supply Current')
        self.capacitorVoltageText.set('CapacitorVoltage')

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

        # self.updateChargeValues()

        self.safetyLights()

    def readResults(self):
        print('read results')

    def discharge(self):
        print('discharge')

    def reset(self):
        print('Reset')
        # Clear user inputs
        self.chargeVoltageEntry.delete(0, 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.countdownStarted = False
        self.idleMode = True

        # Reset plots
        self.resetPlot(self.chargePlot)
        self.resetPlot(self.resultsPlot)

        # Disable all buttons if logged in
        self.disableButtons()

    def setUserInputs(self):
        print('set user inputs')

    def resetPlot(self, canvas):
        for line in canvas.ax.get_lines():
            line.set_data([],[])

        canvas.updatePlot()

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
                checkbutton.pack(anchor='w')

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

    
