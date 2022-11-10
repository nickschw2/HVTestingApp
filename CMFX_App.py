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
        self.notebook = ttk.Notebook(self, style='Accent.TNotebook')
        self.notebook.pack(expand=True, side='top')

        tabNames = ['System Status', 'Charging', 'Results']
        self.notebookFrames = {}
        for tabName in tabNames:
            frame = ttk.Frame(self.notebook, style='Accent.TFrame', **frame_opts)
            frame.pack(expand=True)
            self.notebook.add(frame, text=tabName)
            self.notebookFrames[tabName] = frame

        # Add status indicators to notebook
        # Add frame for text labels
        self.labels = ttk.LabelFrame(self.notebookFrames['System Status'], text='High Voltage Status', style='Accent.TLabelframe', **frame_opts)
        self.labels.pack(side='left')

        # Voltage and current are read from the power supply
        self.voltagePSText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.capacitorVoltageText = tk.StringVar()

        self.voltagePSLabel = ttk.Label(self.labels, textvariable=self.voltagePSText, **text_opts)
        self.currentPSLabel = ttk.Label(self.labels, textvariable=self.currentPSText, **text_opts)
        self.capacitorVoltageLabel = ttk.Label(self.labels, textvariable=self.capacitorVoltageText, **text_opts)
        self.progress = ttk.Progressbar(self.labels, orient='vertical', value=0, mode='determinate', length=progressBarLength)

        self.voltagePSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.currentPSLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.capacitorVoltageLabel.pack(side='top', pady=labelPadding, padx=labelPadding)
        self.progress.pack(side='right', fill='y', pady=labelPadding, padx=labelPadding)

        # Add charging input to notebook
        self.userInputs = ttk.LabelFrame(self.notebookFrames['Charging'], text='User Inputs', style='Accent.TLabelframe', **frame_opts)
        self.userInputs.pack(side='top')

        self.chargeVoltageLabel = ttk.Label(self.userInputs, text='Charge (kV):', style='Accent.TLabel', **text_opts)
        self.chargeVoltageEntry = ttk.Entry(self.userInputs, width=userInputWidth, style='Accent.TEntry', **entry_opts)
        self.userInputOkayButton = ttk.Button(self.userInputs, text='Set', command=self.setUserInputs, style='Accent.TButton')

        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')

        # Plot of charge
        # Put plots and navigation bar in their own frames
        self.chargeFrame = ttk.Frame(self.notebookFrames['Charging'], style='Accent.TFrame', **frame_opts)
        self.chargeFrame.pack(side='top')

        self.chargePlot = CanvasPlot(self.chargeFrame)

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
        self.chargePlotToolbar = NavigationToolbar2Tk(self.chargePlot.canvas, self.chargeFrame)
        self.chargePlotToolbar.update()

        self.chargePlot.pack(side='top')
        self.chargePlotToolbar.pack(side='bottom')

        # Row for buttons on the bottom
        self.buttons = ttk.LabelFrame(self.notebookFrames['Charging'], text='Operate Capacitor', style='Accent.TLabelframe', **frame_opts)
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

        # Console output will always be visible, displays system output
        self.consoleFrame = ttk.LabelFrame(self, text='Console', style='Accent.TLabelframe', **frame_opts)
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

    def readResults(self):
        print('read results')

    def discharge(self):
        print('discharge')

    def reset(self):
        print('reset')

    def setUserInputs(self):
        print('set user inputs')
