from PyQt5 import QtCore, QtWidgets

class ParametersDialog(QtWidgets.QDialog):
    """This class implements a dialog for setting the valid parameters search parameters.
    """

    settings_accepted = QtCore.pyqtSignal(dict)

    def __init__(self, parameters, parent):
        """Constructor

        Args:
            parameters (dict): the initial parameters
        """

        super(ParametersDialog,self).__init__(parent)

        self._parameters = parameters

        self._init_ui()

    def _build_layout(self):
        """Build the layout of the dialog.
        """

        main_layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()

        form_layout.addRow(QtWidgets.QLabel('signal duration (in s)'),self._signal_duration)
        form_layout.addRow(QtWidgets.QLabel('signal separation (in s)'),self._signal_separation)
        form_layout.addRow(QtWidgets.QLabel('signal prominence'),self._signal_prominence)

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
        self._signal_duration.setValue(self._parameters.get('signal duration',5))

        self._signal_separation = QtWidgets.QSpinBox()
        self._signal_separation.setMinimum(1)
        self._signal_separation.setMaximum(100000)
        self._signal_separation.setValue(self._parameters.get('signal separation',15))

        self._signal_prominence = QtWidgets.QDoubleSpinBox()
        self._signal_prominence.setMinimum(0.1)
        self._signal_prominence.setMaximum(10)
        self._signal_prominence.setSingleStep(0.1)
        self._signal_prominence.setValue(self._parameters.get('signal prominence',0.5))

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

        parameters = {}
        parameters['signal duration'] = self._signal_duration.value()
        parameters['signal separation'] = self._signal_separation.value()
        parameters['signal prominence'] = self._signal_prominence.value()

        self.settings_accepted.emit(parameters)

        super(ParametersDialog,self).accept()

