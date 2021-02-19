from PyQt5 import QtWidgets

import matplotlib.ticker as ticker
import matplotlib.patches as patches
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class PlotWidget(QtWidgets.QWidget):
    """This class implements the widgets that stores a standard 1D plot.
    """

    def __init__(self, parent=None):

        super(PlotWidget, self).__init__(parent)

        self.init_ui()

        self._patch = None

    def build_layout(self):
        """Build the layout.
        """

        self._main_layout = QtWidgets.QVBoxLayout()

        self._main_layout.addWidget(self._canvas)
        self._main_layout.addWidget(self._toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(self._main_layout)

    def build_widgets(self):
        """Builds the widgets.
        """

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

    def update_plot(self, x, y):
        """Update the coverage plot

        Args:
            reader (): the reader for which the coverage plot should be set
            selected_property: the selected property
        """

        if len(x) != len(y):
            return

        # If these if already a plot instance, just update the plot
        if hasattr(self, '_plot'):
            self._plot.set_data(x, y)
        else:
            # See here for info https://stackoverflow.com/questions/16742765/matplotlib-2d-line-line-plot-comma-meaning
            self._plot, = self._axes.plot(x, y)

        self._canvas.draw()

    @property
    def axes(self):
        """Getter for _axes attribute.
        """

        return self._axes

    def clear_patch(self):
        """Remove the patch currently drawn if any.
        """

        if self._patch is not None:
            self._patch.remove()
            self._canvas.draw()
            self._patch = None

    def show_interval(self, x_start, y_start, width, height, color='red'):
        """Show the interval as a red rectangle over the plot.
        """

        if self._patch is not None:
            self._patch.remove()

        self._patch = patches.Rectangle(xy=[x_start, y_start],
                                        width=width,
                                        height=height,
                                        linewidth=1,
                                        color=color,
                                        fill=False,
                                        zorder=200)

        self._axes.add_patch(self._patch)

        self._canvas.draw()
