from TestingApp import *

class CMFX_App(TestingApp):
    def __init__(self):
        super().__init__()

        self.configure_ui()
        self.init_ui()
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
            frame = ttk.Frame(self.notebook, **frame_opts)
            frame.pack(expand=True)
            self.notebook.add(frame, text=tabName)
            self.notebookFrames[tabName] = frame

        # Add status indicators to notebook
        # Add frame for text labels
        self.labels = ttk.LabelFrame(self.notebookFrames['System Status'], text='High Voltage Status', **frame_opts)
        self.labels.pack(side='left')

        # Voltage and current are read from the power supply
        self.voltagePSText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.capacitorVoltageText = tk.StringVar()

        self.voltagePSLabel = ttk.Label(self.labels, textvariable=self.voltagePSText, **text_opts)
        self.currentPSLabel = ttk.Label(self.labels, textvariable=self.currentPSText, **text_opts)
        self.capacitorVoltageLabel = ttk.Label(self.labels, textvariable=self.capacitorVoltageText, **text_opts)

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

        # Add charging input to notebook
        self.userInputs = ttk.LabelFrame(self.notebookFrames['Charging'], text='User Inputs', **frame_opts)
        self.userInputs.pack(side='top')

        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):', **text_opts)
        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth, **entry_opts)
        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, style='Accent.TButton')

        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')

        # New frame for plot and other indicators in one row
        self.chargingStatusFrame = ttk.Frame(self.notebookFrames['Charging'], **frame_opts)
        self.chargingStatusFrame.pack(side='top')

        # Frame for indicators
        self.chargingIndicatorsFrame = ttk.Frame(self.chargingStatusFrame, **frame_opts)
        self.chargingIndicatorsFrame.pack(side='left')

        # Add progress bar to notebook
        self.canvas = tk.Canvas(self.chargingIndicatorsFrame, width=200, height=200, bg=sv_selfg)
        self.canvas.pack(side='top')

        self.progressBar = CircularProgressbar(self.canvas, 0, 0, 200, 200, 20)
        # self.progressBar.start()

        # Add status widgets
        self.chargeStateText = tk.StringVar()
        self.countdownText = tk.StringVar()

        self.chargeStateLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.chargeStateText, **text_opts)
        self.countdownLabel = ttk.Label(self.chargingIndicatorsFrame, textvariable=self.countdownText, **text_opts)

        self.chargeStateLabel.pack(side='top')
        self.countdownLabel.pack(side='top')

        # Plot of charge
        # Put plots and navigation bar in their own frames
        self.chargePlotFrame = ttk.Frame(self.chargingStatusFrame, **frame_opts)
        self.chargePlotFrame.pack(side='right')

        self.chargePlot = CanvasPlot(self.chargePlotFrame)

        # Create two y-axes for current and voltage
        self.chargeVoltageAxis = self.chargePlot.ax
        self.chargeCurrentAxis = self.chargePlot.ax.twinx()

        self.chargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.chargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.chargePlot.ax.set_xlabel('Time (s)')

        self.chargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.chargeCurrentAxis.set_ylabel('Current (mA)', color=currentColor)

        self.chargePlot.ax.set_title('Charge Plot')

        # Add lines to charging plot blit animation
        self.chargeVoltageLine, = self.chargeVoltageAxis.plot([],[], color=voltageColor) #Create line object on plot
        self.chargeCurrentLine, = self.chargeCurrentAxis.plot([],[], color=currentColor) #Create line object on plot
        self.chargePlot.ax.set_xlim(0, plotTimeLimit)
        self.chargeVoltageAxis.set_ylim(0, voltageYLim)
        self.chargeCurrentAxis.set_ylim(0, currentYLim)

        # Add two lines and x and y axis for now
        # Blit manager speeds up plotting by redrawing only necessary items
        self.bm = BlitManager(self.chargePlot.canvas, [self.chargeVoltageLine, self.chargeCurrentLine, self.chargePlot.ax.xaxis, self.chargePlot.ax.yaxis])

        # Create the legends before any plot is made
        self.chargePlot.ax.legend(handles=chargeHandles, loc='upper right')

        # Add navigation toolbar to plots
        self.chargePlotToolbar = NavigationToolbar2Tk(self.chargePlot.canvas, self.chargePlotFrame)
        self.chargePlotToolbar.update()

        self.chargePlot.pack(side='top')
        self.chargePlotToolbar.pack(side='bottom')

        # Row for buttons on the bottom
        self.buttons = ttk.LabelFrame(self.notebookFrames['Charging'], text='Operate Capacitor', **frame_opts)
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

        # Add features to Results tab
        # Frame for selecting which plots to show
        self.selectorFrame = ttk.LabelFrame(self.notebookFrames['Results'], text='Plot Selector', **frame_opts)
        self.selectorFrame.pack(side='left')

        # Selector for showing a certain plot
        plotOptions = ['Voltage/Current', 'Interferometer', 'Diamagnetic']
        self.resultsPlotCombobox = ttk.Combobox(self.selectorFrame, value=plotOptions, state='readonly', takefocus=False)
        self.resultsPlotCombobox.current(0)
        self.resultsPlotCombobox.bind('<<ComboboxSelected>>', self.changeResultsPlot)
        self.resultsPlotCombobox.pack(side='top')

        # Initialize list of checkbuttons
        self.resultsCheckbuttons = []
        self.resultsPlots = {}
        self.changeResultsPlot('') # Have to pass a dummy variable

        # Frame for displaying the results plots
        self.resultsPlotFrame = ttk.LabelFrame(self.notebookFrames['Results'], text='Results', **frame_opts)
        self.resultsPlotFrame.pack(side='right')

        # Console output will always be visible, displays system output
        self.consoleFrame = ttk.LabelFrame(self, text='Console', **frame_opts)
        self.consoleFrame.pack(expand=True, side='bottom')

        self.console = Console(self.consoleFrame)
        self.console.pack(expand=True, fill='x')

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


    def init_ui(self):
        print('init_ui')
        self.reset()

    def readResults(self):
        print('read results')

    def discharge(self):
        print('discharge')

    def reset(self):
        print('reset')
        self.chargeStateText.set('Idle')
        self.countdownText.set('Coundtown')
        self.voltagePSText.set('voltage_PS')
        self.currentPSText.set('current_PS')
        self.capacitorVoltageText.set('V_cap')

    def setUserInputs(self):
        print('set user inputs')

    def changeResultsPlot(self, event):
        # Remove all checkbuttons
        for checkButton in self.resultsCheckbuttons:
            checkButton.pack_forget()

        self.resultsCheckbuttons = []

        plotSelection = self.resultsPlotCombobox.get()

        ########## NEED TO CHANGE THESE NAMES INTO DICTIONARIES ########
        checkbuttonNames = ['Voltage', 'Current']
        if plotSelection == 'Voltage/Current':
            checkbuttonNames = ['Voltage', 'Current']
        elif plotSelection == 'Interferometer':
            checkbuttonNames = ['Central']
        elif plotSelection == 'Diamagnetic':
            checkbuttonNames = ['Axial', 'Radial']

        for checkbuttonName in checkbuttonNames:
            checkbutton = ttk.Checkbutton(self.selectorFrame, text=checkbuttonName, style='Switch.TCheckbutton')
            checkbutton.invoke()
            checkbutton.pack(anchor='w')
            self.resultsCheckbuttons.append(checkbutton)
