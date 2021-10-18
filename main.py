import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

class MainApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('HV Capacitor Testing')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        # Column for buttons on the left
        self.grid_columnconfigure(0, w=1)
        self.buttons = ttk.Frame(self)
        self.buttons.grid(row=0, column=0, sticky='news')
        self.buttons.grid_columnconfigure(0, w=1)

        # Begin checklist button
        self.checklist_button = tk.Button(self.buttons, text='Begin Charging\nChecklist',
                                    font=('Times', 24), command=self.checklist)
        self.checklist_button.grid(row=2, column=0, sticky='ew')

        # Begin charging button
        self.charge_button = tk.Button(self.buttons, text='Begin Charging', font=('Times', 24), command=self.charge)
        self.charge_button.grid(row=3, column=0, sticky='ew')

        # Discharge button
        self.discharge_button = tk.Button(self.buttons, text='Discharge', font=('Times', 24), command=self.discharge)
        self.discharge_button.grid(row=4, column=0, sticky='ew')

        # Emergency Off button
        self.emergency_off_button = tk.Button(self.buttons, text='Emergency Off', font=('Times', 24), command=self.emergency_off)
        self.emergency_off_button.grid(row=5, column=0, sticky='ew')

        # Configure Graphs
        self.grid_rowconfigure(0, w=1)
        self.grid_rowconfigure(1, w=1)
        self.grid_columnconfigure(1, w=1)

        # Plot of results
        self.charge_plot = Can_Plot(self)
        self.charge_plot.grid(row=0, column=1, sticky='news')

        self.discharge_plot = Can_Plot(self)
        self.discharge_plot.grid(row=1, column=1, sticky='news')

        # On startup, ask for username
        try:
            self.check_username()
        except:
            print('Text')

    def checklist(self):
        self.checklist_win = tk.Toplevel()

        checklist_steps = ['Turn on ignitron heat lamp for 10 minutes',
            'Ensure that power supply is off',
            'Ensure that the charging switch is open',
            'Check system is grounded',
            'Turn on power supply',
            'Exit room and ensure nobody else is present',
            'Turn on HV Testing Light',
            'Close charging switch',
            'Increase voltage on power supply',
            'Open charging switch',
            'Trigger ignitron',
            'Save scope and video data',
            'Enter room, turn off power supply, and "idiot stick" all HV lines',
            'Turn off HV testing light'
            ]

        self.checlist_Checkbuttons = {}
        for i, step in enumerate(checklist_steps):
            self.checlist_Checkbuttons[f'c{i}'] = tk.Checkbutton(self.checklist_win, text=f'Step {i}: ' + step)
            self.checlist_Checkbuttons[f'c{i}'].grid(row=i, column=0, sticky='w')

        self.checklist_win.wait_window()


    def charge(self):
        print('Charge')

    def discharge(self):
        print('Discharge')

    def emergency_off(self):
        print('Emergency Off')

    def check_username(self):
        print('Check Username')

    def on_closing(self):
        plt.close('all')
        self.quit()
        self.destroy()

class Can_Plot(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.fig, self.ax = plt.subplots(constrained_layout=True)
        self.line, = self.ax.plot([],[]) #Create line object on plot
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=1, fill=tk.BOTH)

    def update(self):
        #update grap
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

class Data_Display(ttk.Frame):

    def __init__(self, master, lab_name):

        super().__init__(master)
        self.master = master
        s = ttk.Style()
        s.configure('.', font=('Times', 24))
        self.lab_tit = ttk.Label(self, text=lab_name) #Set Label Title
        self.lab_tit.pack(expand=1, fill=tk.BOTH)
        self.var = tk.StringVar()
        #self.var.set('test')
        self.lab_data = ttk.Label(self, textvariable=self.var)
        self.lab_data.pack(expand=1, fill=tk.BOTH)

    def update(self, x):

        self.var.set(str(x))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
