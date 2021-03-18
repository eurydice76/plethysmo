import collections

from PyQt5 import QtCore, QtWidgets

from plethysmo.kernel.parameters import PARAMETERS


class ParametersDialog(QtWidgets.QDialog):
    """This class implements a dialog for setting the valid parameters search parameters.
    """

    settings_accepted = QtCore.pyqtSignal(dict)

    def __init__(self, parent):
        """Constructor

        Args:
            parameters (dict): the initial parameters
        """

        super(ParametersDialog,self).__init__(parent)

        self._init_ui()

    def _build_layout(self):
        """Build the layout of the dialog.
        """

        main_layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()

        form_layout.addRow(QtWidgets.QLabel('signal duration (in s)'),self._signal_duration)
        form_layout.addRow(QtWidgets.QLabel('signal separation (in s)'),self._signal_separation)
        form_layout.addRow(QtWidgets.QLabel('signal prominence'),self._signal_prominence)
        form_layout.addRow(QtWidgets.QLabel('frequency threshold'),self._frequency_threshold)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(self._button_box)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def _build_widgets(self):
        """Build the widgets of the dialog.
        """

        self._signal_duration = QtWidgets.QSpinBox()
        self._signal_duration.setMinimum(1)
        self._signal_duration.setMaximum(100000)
        self._signal_duration.setValue(PARAMETERS['signal duration'])

        self._signal_separation = QtWidgets.QSpinBox()
        self._signal_separation.setMinimum(1)
        self._signal_separation.setMaximum(100000)
        self._signal_separation.setValue(PARAMETERS['signal separation'])

        self._signal_prominence = QtWidgets.QDoubleSpinBox()
        self._signal_prominence.setMinimum(0.1)
        self._signal_prominence.setMaximum(10)
        self._signal_prominence.setSingleStep(0.1)
        self._signal_prominence.setValue(PARAMETERS['signal prominence'])

        self._frequency_threshold = QtWidgets.QDoubleSpinBox()
        self._frequency_threshold.setMinimum(0.1)
        self._frequency_threshold.setMaximum(1000)
        self._frequency_threshold.setSingleStep(0.1)
        self._frequency_threshold.setValue(PARAMETERS['frequency threshold'])

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def _init_ui(self):
        """Init the UI
        """

        self._build_widgets()

        self._build_layout()

    def accept(self):
        """Event called when the user accepts the settings.
        """

        PARAMETERS['signal duration'] = self._signal_duration.value()
        PARAMETERS['signal separation'] = self._signal_separation.value()
        PARAMETERS['signal prominence'] = self._signal_prominence.value()
        PARAMETERS['frequency threshold'] = self._frequency_threshold.value()

        super(ParametersDialog,self).accept()

