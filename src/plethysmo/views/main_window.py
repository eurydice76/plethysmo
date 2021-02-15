import logging
import os
import sys

from PyQt5 import QtGui, QtWidgets

import plethysmo
from plethysmo.__pkginfo__ import __version__
from plethysmo.dialogs.parameters_dialog import ParametersDialog
from plethysmo.models.edf_files_model import EDFFilesListModel, EDFFilesListModelError
from plethysmo.utils.progress_bar import progress_bar
from plethysmo.widgets.logger_widget import LoggerWidget
from plethysmo.widgets.plot_widget import PlotWidget

class MainWindow(QtWidgets.QMainWindow):
    """This class implements the main window of the plethysmo application.
    """

    def __init__(self, parent=None):
        """Constructor.
        """

        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Build the signal/slots.
        """

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        hlayout.addWidget(self._edf_files_list)
        hlayout.addWidget(self._plot_widget)

        main_layout.addLayout(hlayout, stretch=4)

        main_layout.addWidget(self._logger.widget, stretch=2)

        self._main_frame.setLayout(main_layout)

    def build_menu(self):
        """Build the menu.
        """

        menubar = self.menuBar()

        file_menu = menubar.addMenu('&File')

        file_action = QtWidgets.QAction('&Open EDF file(s)', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open EDF files')
        file_action.triggered.connect(self.on_load_data)
        file_menu.addAction(file_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit inspigtor')
        exit_action.triggered.connect(self.on_quit_application)
        file_menu.addAction(exit_action)

        run_menu = menubar.addMenu('&Run')

        parameters_action = QtWidgets.QAction('&Set interval search parameters', self)
        parameters_action.setShortcut('Ctrl+P')
        parameters_action.setStatusTip('Set interval search parameters')
        parameters_action.triggered.connect(self.on_set_intervals_search_parameters)
        run_menu.addAction(parameters_action)

    def build_widgets(self):
        """Build the widgets.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._edf_files_list = QtWidgets.QListView()
        self._edf_files_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        edf_files_model = EDFFilesListModel(self)
        self._edf_files_list.setModel(edf_files_model)

        self._plot_widget = PlotWidget(self)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 1200, 1100)

        self.setWindowTitle("plethysmo {}".format(__version__))

        self._logger = LoggerWidget(self)
        self._logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self._logger)
        logging.getLogger().setLevel(logging.INFO)

        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        progress_bar.set_progress_widget(self._progress_bar)
        self.statusBar().showMessage("plethysmo {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

        icon_path = os.path.join(plethysmo.__path__[0], "icons", "plethysmo.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    def on_load_data(self):
        """Event called when the user loads data from the main menu.
        """

        # Pop up a file browser
        edf_files = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open EDF file(s)', '', 'EDF Files (*.edf)')[0]
        if not edf_files:
            return

        edf_files_model = self._edf_files_list.model()

        n_edf_files = len(edf_files)
        progress_bar.reset(n_edf_files)

        n_loaded_files = 0

        # Loop over the pig directories
        for progress, filename in enumerate(edf_files):

            try:
                edf_files_model.add_edf_file(filename)
            except EDFFilesListModelError as e:
                logging.error(str(e))
            else:
                n_loaded_files += 1
            finally:
                progress_bar.update(progress+1)

        # Create a signal/slot connexion for row changed event
        self._edf_files_list.selectionModel().currentChanged.connect(self.on_select_edf_file)

        self._edf_files_list.setCurrentIndex(edf_files_model.index(0, 0))

        logging.info('Loaded successfully {} files out of {}'.format(n_loaded_files, n_edf_files))

    def on_quit_application(self):
        """Event called when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(self, 'Quit', "Do you really want to quit?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_select_edf_file(self, index):
        """Event fired when an EDF file is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the EDF file in the corresponding list view
        """

        edf_files_model = self._edf_files_list.model()

        reader = edf_files_model.data(index, role = EDFFilesListModel.Reader)

        self._plot_widget.update_plot(reader.times, reader.signal)

    def on_set_intervals_search_parameters(self):
        """Event called when the user open the parameters dialog.
        """

        edf_files_model = self._edf_files_list.model()

        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        dialog = ParametersDialog(reader.parameters, self)

        if dialog.exec_():
            reader.parameters = dialog.parameters
