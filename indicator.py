import ttkbootstrap as ttk
from tkinter import Canvas
from constants import *
from ttkbootstrap.themes import standard

theme_colors = standard.STANDARD_THEMES[themename]['colors']

class Indicator(ttk.Frame):
    def __init__(self, master, text='', size=20, on_color=theme_colors['danger'], off_color=theme_colors['inputbg']):
        super().__init__(master)
        self.master = master
        self.text = text
        self.on_color = on_color
        self.off_color = off_color
        self.state = False

        self.indicatorFrame = ttk.Frame(self.master)
        self.indicatorFrame.pack(anchor='w')

        self.canvas = Canvas(self.indicatorFrame, width=size, height=size, highlightthickness=0)
        self.indicator_outline = self.canvas.create_oval(0, 0, size, size, fill=theme_colors['dark'], outline='')
        self.indicator = self.canvas.create_oval(0.1*size, 0.1*size, 0.9*size, 0.9*size, fill='#591f19', outline='')
        self.canvas.pack(side='left', padx=(0, labelPadding))

        self.label = ttk.Label(self.indicatorFrame, text=self.text)
        self.label.pack(side='left')

    def set(self, state):
        self.state = state
        if self.state:
            self.canvas.itemconfig(self.indicator, fill=self.on_color)
        else:
            self.canvas.itemconfig(self.indicator, fill=self.off_color)
