# Import statements for creating plots in tkinter applications
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk

# Eventually implement blitting to speed up plotting: https://matplotlib.org/stable/tutorials/advanced/blitting.html

# Class for inserting plots into tkinter frames
class CanvasPlot(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.fig, self.ax = plt.subplots(constrained_layout=True)
        # self.fig.patch.set_facecolor(defaultbg)
        self.line, = self.ax.plot([],[]) #Create line object on plot
        # Function calls to insert figure onto canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=1, fill=tk.BOTH)

    def updatePlot(self):
        #update graph
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
