# Import statements for creating plots in tkinter applications
import matplotlib as mpl
mpl.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from constants import *
from ttkbootstrap.themes import standard

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
                    # ax.lines.remove(lines[0])
                    ax.lines.pop(0)

        self.updatePlot()


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