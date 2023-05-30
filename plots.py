# Import statements for creating plots in tkinter applications
import matplotlib as mpl
mpl.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from constants import *
from ttkbootstrap.themes import standard
import numpy as np

# Change color cycler for dark mode
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=color_palette) 

# Change the colors of plot to match the theme
theme_colors = standard.STANDARD_THEMES[themename]['colors']
mpl.rcParams['figure.facecolor'] = theme_colors['bg']
mpl.rcParams['axes.facecolor'] = theme_colors['bg']
mpl.rcParams['axes.labelcolor'] = theme_colors['fg']
mpl.rcParams['axes.edgecolor'] = theme_colors['fg']
mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.color'] = theme_colors['fg']
mpl.rcParams['xtick.color'] = theme_colors['fg']
mpl.rcParams['ytick.color'] = theme_colors['fg']
mpl.rcParams['text.color'] = theme_colors['fg']
mpl.rcParams['legend.facecolor'] = theme_colors['fg']
mpl.rcParams['legend.facecolor'] = theme_colors['secondary']


# Class for inserting plots into tkinter frames
class CanvasPlot(ttk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.master = master
        self.fig, self.ax = plt.subplots(constrained_layout=True, **kwargs)

        # Function calls to insert figure onto canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

    def updatePlot(self):
        #update graph
        # reset all axes in figure
        for ax in self.fig.axes:
            ax.relim()
            ax.autoscale_view()
        self.canvas.draw()

    # Removes all lines from a figure
    def clearFigLines(self):
        for ax in self.fig.axes:
            if len(ax.lines) != 0:
                for i in range(len(ax.lines)):
                    # Remove the first one each time in the loop
                    ax.lines[0].remove()
                    # ax.lines.pop(0)


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
            self._bg = cv.copy_from_bbox(cv.figure.bbox)
            self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()

class CustomToolbar(NavigationToolbar2Tk):  # subclass NavigationToolbar2Tk
    def __init__(self, figcanvas, parent):
        super().__init__(figcanvas, parent)  # init the base class as usual

    # copied the method 'draw_rubberband()' right from NavigationToolbar2Tk
    # we're only changing one line to add color to rectangle
    def draw_rubberband(self, event, x0, y0, x1, y1):
        height = self.canvas.figure.bbox.height
        y0 = height - y0
        y1 = height - y1
        if hasattr(self, "lastrect"):
            self.canvas._tkcanvas.delete(self.lastrect)
        self.lastrect = self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, outline=theme_colors['primary'])

    # copied the method '_update_view()' right from NavigationToolbar2 in backend_bases.py
    # we're only adding lines to relim and autoscale
    def _update_view(self):
        """
        Update the viewlim and position from the view and position stack for
        each axes.
        """
        nav_info = self._nav_stack()
        if nav_info is None:
            return
        # Retrieve all items at once to avoid any risk of GC deleting an Axes
        # while in the middle of the loop below.
        items = list(nav_info.items())
        for ax, (view, (pos_orig, pos_active)) in items:
            ax._set_view(view)

             # Rescale the plot
            ax.relim()
            ax.autoscale()

            # Restore both the original and modified positions
            ax._set_position(pos_orig, 'original')
            ax._set_position(pos_active, 'active')
        self.canvas.draw_idle()

class PlotViewer(ttk.Frame):
    def __init__(self, master, plotData, **kwargs):

        super().__init__(master)
        self.master = master
        self.plotData = plotData

        # Frame for displaying the plots
        self.plotFrame = ttk.Frame(self.master)
        self.plotFrame.pack(side='right', expand=True, padx=plotPadding)

        # Add plot and toolbar to frame
        # There are currently two viewing modes, one with single plots and one with subplots
        self.plotSingle = CanvasPlot(self.plotFrame, figsize=(10, 4))
        nrows_subplots = int(np.ceil(len(self.plotData) / 2))
        self.plotSubplots = CanvasPlot(self.plotFrame, nrows=nrows_subplots, ncols=2, figsize=(12, 6))

        self.plotToolbar = CustomToolbar(self.plotSingle.canvas, self.plotFrame)
        self.plotSubplotsToolbar = CustomToolbar(self.plotSubplots.canvas, self.plotFrame)
        self.plotToolbar.update()
        self.plotSubplotsToolbar.update()

        self.plotSingle.pack(side='top', expand=True)
        self.plotSubplots.pack(side='top', expand=True)

        # Frame for adjusting all aspects of the plot view
        self.viewFrame = ttk.Frame(self.master)
        self.viewFrame.pack(side='left', expand=True, padx=framePadding, pady=framePadding)

        # Add frame for run number
        self.runNumberFrame = ttk.LabelFrame(self.viewFrame, text='Run #', width=systemStatusFrameWidth, height=20, bootstyle='primary')
        self.runNumberFrame.pack(side='top', expand=True, pady=(0, framePadding))

        # Create text variables for Run Number, associate with labels, and place
        self.runNumberText = ttk.StringVar()
        self.runNumberText.set(f'Run #N/A')	
        self.runNumberLabel = ttk.Label(self.runNumberFrame, textvariable=self.runNumberText)
        self.runNumberLabel.pack(side='top', pady=labelPadding, padx=labelPadding)

        # Frame for selecting which plots to show
        self.radioFrame = ttk.LabelFrame(self.viewFrame, text='View Style', width=systemStatusFrameWidth, bootstyle='primary')
        self.radioFrame.pack(side='top', expand=True, pady=(0, framePadding))

        # Radio buttons for choosing which display style to show
        self.plotView = ttk.IntVar()
        self.plotView.set(0) # initialize view
        singleRadiobutton = ttk.Radiobutton(self.radioFrame, text='Single', variable=self.plotView, value=0, command=lambda: self.replot(singleRadiobutton))
        subplotsRadiobutton = ttk.Radiobutton(self.radioFrame, text='Subplots', variable=self.plotView, value=1, command=lambda: self.replot(subplotsRadiobutton))

        singleRadiobutton.pack(side='top', expand=True, padx=framePadding, pady=setPinsPaddingY)
        subplotsRadiobutton.pack(side='top', expand=True, padx=framePadding, pady=setPinsPaddingY)

        # Frame for selecting which plots to show
        self.selectorFrame = ttk.LabelFrame(self.viewFrame, text='Plot Selector', width=systemStatusFrameWidth, bootstyle='primary')
        self.selectorFrame.pack(side='top', expand=True)

        # Selector for showing a certain plot
        plotOptions = list(self.plotData.keys())
        self.plotCombobox = ttk.Combobox(self.selectorFrame, value=plotOptions, state='readonly', bootstyle='primary', **text_opts)
        self.plotCombobox.current(0) # Initializes the current value to first option
        self.plotCombobox.bind('<<ComboboxSelected>>', self.replot)
        self.plotCombobox.pack(side='top', expand=True, padx=framePadding, pady=setPinsPaddingY)

        # Initialize checkbuttons
        self.checkbuttons = {}
        for plotOption, plotProperties in self.plotData.items():
            # Need to create a dictionary for each checkbutton corresponding to its label
            self.checkbuttons[plotOption] = {}
            for line in plotProperties['lines'].values():
                checkbutton = ttk.Checkbutton(self.selectorFrame, text=line.label)
                checkbutton.invoke() # Initialize it to be turned on
                checkbutton.bind('<Button>', self.replot)
                self.checkbuttons[plotOption][line.label] = checkbutton
        
        # Preset discharge timing
        self.dischargeTime = []
        self.dischargeTimeUnit = 's'
        
        self.replot()

    def replot(self, event=None):
        # Have to do some weird logic because tkinter doesn't have virtual events
        # for Radiobuttons, but does for comboboxes
        if event == None:
            eventType = None
        elif isinstance(event, ttk.Radiobutton):
            eventType = ttk.Radiobutton
        elif isinstance(event.widget, ttk.Combobox):
            eventType = ttk.Combobox
        elif isinstance(event.widget, ttk.Checkbutton):
            eventType = ttk.Checkbutton
        else:
            eventType = None

        # Get timing from grandparent (CMFX_App)
        if hasattr(self.master.master.master, 'dischargeTime'):
            self.dischargeTime = self.master.master.master.dischargeTime
            self.dischargeTimeUnit = self.master.master.master.dischargeTimeUnit

        # Update run number text
        if hasattr(self.master.master.master, 'runNumber'):
            self.runNumberText.set(f'Run #{int(self.master.master.master.runNumber)}')

        def setup_plots(plotSelection, ax):
            # Change plot to new selection
                plotProperties = self.plotData[plotSelection]
                ax.set_title(f'{plotSelection}')
                ax.set_xlabel(f'Time ({self.dischargeTimeUnit})')
                ax.set_prop_cycle(None) # Reset the color cycle
                
                # Remove extra twinx in single plot
                while len(self.plotSingle.fig.axes) > 1:
                    self.plotSingle.fig.axes[1].remove()

                # Add twin axis if specified
                if not plotProperties['twinx']:
                    ax.set_ylabel(plotProperties['ylabel'])
                else:
                    twin_ax = ax.twinx()
                    twin_ax.grid(False)
                    ax.set_ylabel(plotProperties['ylabel'][0])
                    twin_ax.set_ylabel(plotProperties['ylabel'][1])

                # Some place to store the current lines on the plot to change visibility later
                # Don't reset currentLines if we're just switching the view to/from subplots
                if eventType != ttk.Radiobutton:
                    self.currentLines = {}
                handles = []    
                labels = []
                for i, line in enumerate(plotProperties['lines'].values()):
                    if eventType == ttk.Radiobutton:
                        visible = True
                    else:
                        checkbuttons = self.checkbuttons[plotSelection]
                        visible = checkbuttons[line.label].instate(['selected'])

                    # try:
                    # Check for twin axis
                    if not plotProperties['twinx']:
                        handle = ax.plot(self.dischargeTime, line.data, label=line.label, visible=visible)
                    # Plot second line on twin axis
                    # Can only have a twin axis when there are two lines and no more
                    else:
                        if i == 0:
                            handle = ax.plot(self.dischargeTime, line.data, label=line.label, visible=visible)
                        elif i == 1:
                            # Skip first color
                            next(twin_ax._get_lines.prop_cycler)
                            handle = twin_ax.plot(self.dischargeTime, line.data, label=line.label, visible=visible)
                        elif i == 2:
                            # Skip first two color
                            next(twin_ax._get_lines.prop_cycler)
                            next(twin_ax._get_lines.prop_cycler)
                            handle = twin_ax.plot(self.dischargeTime, line.data, label=line.label, visible=visible)

                    if eventType != ttk.Radiobutton:
                        self.currentLines[line.label] = handle[0]
                    handles.append(handle[0])
                    labels.append(line.label)
                    # except ValueError:
                    #     print(f'Plotting failed on {line.label}.')

                # Get all labels onto one legend even if there's a twin axis
                ax.legend(handles, labels)            

        # Combobox selection
        if self.plotView.get() == 0:
            # Remove subplots and add single view
            self.plotSubplots.pack_forget()
            self.plotSubplotsToolbar.pack_forget()
            self.plotSingle.pack(side='top', expand=True)
            self.plotToolbar.pack(side='bottom', fill='x')

            # Enable combobox
            self.plotCombobox.configure(state='readonly')

            # Get value of combobox and associated checkbuttons
            plotSelection = self.plotCombobox.get()
            checkbuttons = self.checkbuttons[plotSelection]

            # Enable checkbutons
            for checkbutton in checkbuttons.values():
                checkbutton.configure(state='enabled')

            # Need to tell if event came from the combobox or a checkbutton
            # event==None is for dummy variable instantiation
            if eventType == None or eventType == ttk.Combobox:
                # Remove current checkbuttons
                for widget in self.selectorFrame.winfo_children():
                    if isinstance(widget, ttk.Checkbutton) and widget.winfo_ismapped():
                        widget.pack_forget()

                # Remove current lines from plot
                self.plotSingle.clearFigLines()

                # Change checkbuttons to new selection
                for checkbutton in checkbuttons.values():
                    checkbutton.pack(expand=True, anchor='w', padx=framePadding, pady=setPinsPaddingY)

                ax = self.plotSingle.ax
                setup_plots(plotSelection, ax)

                # Rescale the plot
                ax.relim()
                ax.autoscale()

            # Change visibility of line when the checkbutton for that line is changed
            elif eventType == ttk.Checkbutton:
                label = event.widget.cget('text')
                line = self.currentLines[label]
                visible = checkbuttons[label].instate(['!selected'])
                line.set_visible(visible)

                handles = self.currentLines.values()
                labels = self.currentLines.keys()

                self.plotSingle.ax.legend(handles, labels)

            # Update plot
            self.plotSingle.updatePlot()

        # Radiobutton selection
        elif self.plotView.get() == 1:
            # Remove single view and add subplots view
            self.plotSingle.pack_forget()
            self.plotToolbar.pack_forget()
            self.plotSubplots.pack(side='top', expand=True)
            self.plotSubplotsToolbar.pack(side='bottom', fill='x')

            # Disable combobox
            self.plotCombobox.configure(state='disabled')

            # Remove last subplot if there is an odd number
            if len(self.plotData) % 2 != 0:
                self.plotSubplots.fig.axes[-1].axis('off')

            for i, plotSelection in enumerate(self.plotData):
                # Disable check buttons
                checkbuttons = self.checkbuttons[plotSelection]
                for checkbutton in checkbuttons.values():
                    checkbutton.configure(state='disabled')

                ax = self.plotSubplots.fig.axes[i]
                setup_plots(plotSelection, ax)

            # Update plot
            self.plotSubplots.updatePlot()

        if eventType == None or eventType == ttk.Radiobutton:
            # Heirarchy: PlotViewer --> Notebook --> CMFX_App
            self.master.master.master.center_app()