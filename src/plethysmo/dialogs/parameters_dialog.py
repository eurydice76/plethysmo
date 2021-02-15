from PyQt5 import QtWidgets

class ParametersDialog(QtWidgets.QDialog):
    """This class implements a dialog for setting the valid parameters search parameters.
    """

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

        form_layout.addRow(QtWidgets.QLabel('threshold min'),self._threshold_min)
        form_layout.addRow(QtWidgets.QLabel('threshold max'),self._threshold_max)
        form_layout.addRow(QtWidgets.QLabel('signal duration (in s)'),self._signal_duration)
        form_layout.addRow(QtWidgets.QLabel('signal separation (in s)'),self._signal_separation)
        form_layout.addRow(QtWidgets.QLabel('exclusion zones'),self._exclusion_zones)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(self._button_box)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def _build_widgets(self):
        """Build the widgets of the dialog.
        """

        self._threshold_min = QtWidgets.QDoubleSpinBox()
        self._threshold_min.setMinimum(-1)
        self._threshold_min.setMaximum(1)
        self._threshold_min.setValue(self._parameters.get('threshold min',-0.8))
        self._threshold_min.setSingleStep(0.01)

        self._threshold_max = QtWidgets.QDoubleSpinBox()
        self._threshold_max.setMinimum(-1)
        self._threshold_max.setMaximum(1)
        self._threshold_max.setValue(self._parameters.get('threshold max',0.8))
        self._threshold_max.setSingleStep(0.01)

        self._signal_duration = QtWidgets.QSpinBox()
        self._signal_duration.setMinimum(1)
        self._signal_duration.setMaximum(100000)
        self._signal_duration.setValue(self._parameters.get('signal duration',5))

        self._signal_separation = QtWidgets.QSpinBox()
        self._signal_separation.setMinimum(1)
        self._signal_separation.setMaximum(100000)
        self._signal_separation.setValue(self._parameters.get('signal separation',15))

        self._exclusion_zones = QtWidgets.QLineEdit()
        self._exclusion_zones.setText(self._parameters.get('exclusion zones',''))

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def _init_ui(self):
        """Init the UI
        """

        self._build_widgets()

        self._build_layout()

    @property
    def parameters(self):
        """Returns the parameters stored in the dialog.
        """

        params = {}
        params['threshold min'] = self._threshold_min.value()
        params['threshold max'] = self._threshold_max.value()
        params['signal duration'] = self._signal_duration.value()
        params['signal separation'] = self._signal_separation.value()
        params['exclusion zones'] = self._exclusion_zones.text()

        return params

