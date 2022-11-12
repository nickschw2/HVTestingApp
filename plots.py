# Import statements for creating plots in tkinter applications
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from constants import *

# Eventually implement blitting to speed up plotting: https://matplotlib.org/stable/tutorials/advanced/blitting.html

# Class for inserting plots into tkinter frames
class CanvasPlot(ttk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.master = master
        self.fig, self.ax = plt.subplots(constrained_layout=True, **kwargs)
        # self.fig.patch.set_facecolor(defaultbg)
        self.line, = self.ax.plot([],[]) #Create line object on plot
        # Function calls to insert figure onto canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

    def updatePlot(self):
        #update graph
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()


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

# class CircularProgressbar(object):
#     def __init__(self, canvas, x0, y0, x1, y1, width=0, start_ang=0, full_extent=360.):
#         self.canvas = canvas
#         self.x0, self.y0, self.x1, self.y1 = x0+width, y0+width, x1-width, y1-width
#         self.tx, self.ty = (x1-x0) / 2, (y1-y0) / 2
#         self.width = width
#         self.start_ang, self.full_extent = start_ang, full_extent
#         # draw static bar outline
#         w2 = width / 2
#         self.oval_id1 = self.canvas.create_oval(self.x0-w2, self.y0-w2,
#                                                 self.x1+w2, self.y1+w2)
#         self.oval_id2 = self.canvas.create_oval(self.x0+w2, self.y0+w2,
#                                                 self.x1-w2, self.y1-w2)
#
#         self.running = False
#
#     def start(self, interval=100):
#         self.interval = interval  # Msec delay between updates.
#         self.increment = self.full_extent / interval
#         self.extent = 0
#         self.arc_id = self.canvas.create_arc(self.x0, self.y0, self.x1, self.y1,
#                                              start=self.start_ang, extent=self.extent,
#                                              width=self.width, style='arc', fill=sv_blue)
#         percent = '0%'
#         self.label_id = self.canvas.create_text(self.tx, self.ty, text=f'Charge: {percent}')
#         self.running = True
#         self.canvas.after(interval, self.step, self.increment)
#
#     def step(self, delta):
#         """Increment extent and update arc and label displaying how much completed."""
#         if self.running:
#             self.extent = (self.extent + delta) % 360
#             self.canvas.itemconfigure(self.arc_id, extent=self.extent, fill=sv_blue)
#             # Update percentage value displayed.
#             percent = round(float(self.extent) / self.full_extent * 100)
#             self.canvas.itemconfigure(self.label_id, text=f'Charge: {percent}')
#         self.canvas.after(self.interval, self.step, delta)
#
#
#     def toggle_pause(self):
#         self.running = not self.running
