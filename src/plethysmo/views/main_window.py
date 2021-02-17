import logging
import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import plethysmo
from plethysmo.__pkginfo__ import __version__
from plethysmo.dialogs.parameters_dialog import ParametersDialog
from plethysmo.dialogs.plot_dialog import PlotDialog
from plethysmo.dialogs.roi_dialog import ROIDialog
from plethysmo.models.edf_files_list_model import EDFFilesListModel, EDFFilesListModelError
from plethysmo.models.intervals_list_model import IntervalsListModel
from plethysmo.models.rois_list_model import ROISListModel
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

        self._search_valid_intervals_button.clicked.connect(self.on_search_valid_intervals)
        self._intervals_list.doubleClicked.connect(self.on_show_zoomed_data)
        self._add_roi_button.clicked.connect(self.on_add_roi)
        self._add_excluded_zone_button.clicked.connect(self.on_add_excluded_zone)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        upper_hlayout = QtWidgets.QHBoxLayout()
        upper_hlayout.addWidget(self._edf_files_list)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._rois_list)
        vlayout.addWidget(self._add_roi_button)
        upper_hlayout.addLayout(vlayout)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._excluded_zones_list)
        vlayout.addWidget(self._add_excluded_zone_button)
        upper_hlayout.addLayout(vlayout)

        main_layout.addLayout(upper_hlayout)

        main_layout.addWidget(self._search_valid_intervals_button)

        middle_hlayout = QtWidgets.QHBoxLayout()
        middle_hlayout.addWidget(self._intervals_list)
        middle_hlayout.addWidget(self._plot_widget, stretch=2)

        main_layout.addLayout(middle_hlayout, stretch=4)

        main_layout.addWidget(self._logger.widget, stretch=1)

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
        parameters_action.triggered.connect(self.on_open_parameters_dialog)
        run_menu.addAction(parameters_action)

    def build_widgets(self):
        """Build the widgets.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._edf_files_list = QtWidgets.QListView()
        self._edf_files_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        edf_files_list_model = EDFFilesListModel(self)
        self._edf_files_list.setModel(edf_files_list_model)

        self._rois_list = QtWidgets.QListView()
        self._add_roi_button = QtWidgets.QPushButton('Add ROI')
        self._rois_list.installEventFilter(self)

        self._excluded_zones_list = QtWidgets.QListView()
        self._add_excluded_zone_button = QtWidgets.QPushButton('Add excluded zone')

        self._plot_widget = PlotWidget(self)

        self._intervals_list = QtWidgets.QListView()

        self._search_valid_intervals_button = QtWidgets.QPushButton('Search valid intervals')

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

    def eventFilter(self, watched, event):
        """
        """

        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Delete:
            if watched == self._rois_list:
                current_index = self._rois_list.currentIndex()
                rois_list_model = self._rois_list.model()
                rois_list_model.remove_roi(current_index.row())

        return False

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    def on_add_roi(self):
        """Pops up a dialog for drawing a ROI which will serve for setting up a zone of interest for intervals search.
        """

        edf_files_model = self._edf_files_list.model()

        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        dialog = ROIDialog(reader, self)

        if dialog.exec_():
            new_roi = dialog.roi
            rois_list_model = self._rois_list.model()
            if rois_list_model is not None:
                rois_list_model.add_roi(new_roi)

    def on_add_excluded_zone(self):
        """Pops up a dialog for drawing a ROI which will serve for setting an excluded zone.
        """

        edf_files_model = self._edf_files_list.model()

        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        dialog = ROIDialog(reader, self)

        if dialog.exec_():
            new_roi = dialog.roi
            excluded_zone_list_model = self._excluded_zones_list.model()
            if excluded_zone_list_model is not None:
                excluded_zone_list_model.add_roi(new_roi)

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

    def on_search_valid_intervals(self):
        """Event triggered when the user clicks on the search valid intervals button.
        """

        edf_files_model = self._edf_files_list.model()

        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        valid_intervals = reader.update_valid_intervals()

        intervals_list_model = IntervalsListModel(valid_intervals, reader.dt, self)

        self._intervals_list.setModel(intervals_list_model)

        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

    def on_select_edf_file(self, index):
        """Event fired when an EDF file is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the EDF file in the corresponding list view
        """

        edf_files_list_model = self._edf_files_list.model()

        reader = edf_files_list_model.data(index, role = EDFFilesListModel.Reader)

        # Plot the signal contained in the selected reader
        self._plot_widget.update_plot(reader.times, reader.signal)

        # Replace the current intervals found with the one from the selected reader
        intervals_list_model = IntervalsListModel(reader.valid_intervals, reader.dt, self)
        self._intervals_list.setModel(intervals_list_model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        # Replace the current ROIs list model by the one from the selected reader.
        rois_list_model = ROISListModel(reader.rois, self)
        self._rois_list.setModel(rois_list_model)
        rois_list_model.no_roi.connect(lambda : self._plot_widget.clear_patch())
        self._rois_list.selectionModel().currentChanged.connect(self.on_select_roi)

        # Replace the current excluded zones list model by the one from the selected reader.
        excluded_zones_list_model = ROISListModel(reader.excluded_zones, self)
        self._excluded_zones_list.setModel(excluded_zones_list_model)
        excluded_zones_list_model.no_roi.connect(lambda : self._plot_widget.clear_patch())
        self._excluded_zones_list.selectionModel().currentChanged.connect(self.on_select_excluded_zone)

    def on_select_interval(self, index):
        """Event fired when an interval is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the interval in the corresponding list view
        """

        # Get the selected reader
        selected_edf_file_index = self._edf_files_list.currentIndex()
        edf_files_list_model = self._edf_files_list.model()
        reader = edf_files_list_model.data(selected_edf_file_index, role = EDFFilesListModel.Reader)

        # Get the selected interval
        intervals_list_model = self._intervals_list.model()
        interval = intervals_list_model.data(index, role = IntervalsListModel.SelectedInterval)

        start = interval[0]*reader.dt

        end = interval[1]*reader.dt

        width = end - start

        self._plot_widget.show_interval(start, -1.0, width, 2.0, 'blue')

    def on_select_excluded_zone(self, index):
        """Event called when the user clicks on a ROI.
        """        

        # Get the selected ROI
        excluded_zone_list_model = self._excluded_zones_list.model()
        if excluded_zone_list_model is None:
            return

        roi = excluded_zone_list_model.data(index, role = ROISListModel.SelectedROI)

        # Case where there is no more ROI in the list
        if roi == QtCore.QVariant():
            return

        lower_corner = roi.lower_corner
        upper_corner = roi.upper_corner

        self._plot_widget.show_interval(lower_corner[0],
                                        lower_corner[1],
                                        upper_corner[0] - lower_corner[0],
                                        upper_corner[1] - lower_corner[1],
                                        'red')

    def on_select_roi(self, index):
        """Event called when the user clicks on a ROI.
        """        

        # Get the selected ROI
        rois_list_model = self._rois_list.model()
        if rois_list_model is None:
            return

        roi = rois_list_model.data(index, role = ROISListModel.SelectedROI)

        # Case where there is no more ROI in the list
        if roi == QtCore.QVariant():
            return

        lower_corner = roi.lower_corner
        upper_corner = roi.upper_corner

        self._plot_widget.show_interval(lower_corner[0],
                                        lower_corner[1],
                                        upper_corner[0] - lower_corner[0],
                                        upper_corner[1] - lower_corner[1],
                                        'green')

    def on_set_parameters(self, parameters):
        """Set the search parameters for the current edf file.
        """

        edf_files_model = self._edf_files_list.model()

        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        reader.parameters = parameters

    def on_open_parameters_dialog(self):
        """Event called when the user open the parameters dialog.
        """

        edf_files_model = self._edf_files_list.model()
        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        current_index = self._edf_files_list.currentIndex()

        reader = edf_files_model.data(current_index,role=EDFFilesListModel.Reader)

        dialog = ParametersDialog(reader.parameters, self)

        dialog.settings_accepted.connect(self.on_set_parameters)

        # The dialog should not be modal
        dialog.show()

    def on_show_zoomed_data(self, index):
        """Pops a dialog with the zoomed data for a selected interval.
        """

        # Get the selected reader
        selected_edf_file_index = self._edf_files_list.currentIndex()
        edf_files_list_model = self._edf_files_list.model()
        reader = edf_files_list_model.data(selected_edf_file_index, role = EDFFilesListModel.Reader)

        # Get the selected interval
        intervals_list_model = self._intervals_list.model()
        interval = intervals_list_model.data(index, role = IntervalsListModel.SelectedInterval)

        # The zoomed data
        zoomed_times = reader.times[interval[0]:interval[1]]
        zoomed_signal = reader.signal[interval[0]:interval[1]]

        # Plot the zoomed data
        dialog = PlotDialog(zoomed_times, zoomed_signal, self)
        dialog.setWindowTitle('Signal at [{},{}] s'.format(zoomed_times[0],zoomed_times[-1]))
        dialog.show()