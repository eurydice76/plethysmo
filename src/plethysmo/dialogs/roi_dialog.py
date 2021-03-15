import logging

from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT 
from matplotlib.widgets import RectangleSelector

from plethysmo.kernel.roi import ROI

class ROIDialog(QtWidgets.QDialog):
    """This class implements a dialog for drawing a rectangular ROI over a signal.
    """

    def __init__(self, reader, parent):
        """Constructor.
        """

        super(ROIDialog,self).__init__(parent)

        self._reader = reader

        self._lower_corner = None

        self._upper_corner = None

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        self._main_layout = QtWidgets.QVBoxLayout()

        self._main_layout.addWidget(self._canvas)
        self._main_layout.addWidget(self._toolbar)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(QtWidgets.QLabel('Name:'))
        hlayout.addWidget(self._name)

        self._main_layout.addLayout(hlayout)

        self._main_layout.addWidget(self._button_box)

        self.setGeometry(0, 0, 600, 600)

        self.setLayout(self._main_layout)

    def build_widgets(self):
        """Builds the widgets.
        """

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        self._rs = RectangleSelector(self._axes, 
                                     self.on_draw_roi,
                                     drawtype='box',
                                     useblit=True,
                                     button=[1],
                                     minspanx=5,
                                     minspany=5,
                                     spancoords='pixels',
                                     interactive=True)

        self._name = QtWidgets.QLineEdit()

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.plot()

    def on_draw_roi(self, eclick, erelease):
        """Callback bound to the rectangle selector which keeps track of the coordinates of the ROI.
        """

        x1, y1 = eclick.xdata, eclick.ydata
        self._lower_corner = [x1,y1]

        x2, y2 = erelease.xdata, erelease.ydata
        self._upper_corner = [x2,y2]

    def plot(self):
        """Plot the signal contained in the reader.
        """

        self._axes.clear()

        self._axes.plot(self._reader.times, self._reader.signal)

        self._canvas.draw()

    def accept(self):
        """Event called when the user accept the settings.
        """

        name = self._name.text().strip()

        if not name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'The ROI has no name. Can not save it.')
            return

        if self._lower_corner is None or self._upper_corner is None:
            QtWidgets.QMessageBox.warning(self, 'warning', 'No ROI defined.')
            return

        super(ROIDialog,self).accept()

    @property
    def roi(self):
        """Build and return a ROI.
        """

        name = self._name.text().strip()

        roi = ROI(self._lower_corner, self._upper_corner)

        return name, roi

