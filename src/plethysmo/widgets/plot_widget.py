from PyQt5 import QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT 


class PlotWidget(QtWidgets.QWidget):
    """This class implements the widgets that stores a standard 1D plot.
    """

    def __init__(self, parent=None):

        super(PlotWidget, self).__init__(parent)

        self.init_ui()

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

        self._axes.clear()

        self._axes.plot(x, y)
        self._canvas.draw()

    @property
    def axes(self):
        """Getter for _axes attribute.
        """

        return self._axes