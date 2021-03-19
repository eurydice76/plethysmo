import collections
import logging
import os
import sys

from scipy.signal import find_peaks

from PyQt5 import QtCore, QtGui, QtWidgets

import plethysmo
from plethysmo.__pkginfo__ import __version__
from plethysmo.dialogs.parameters_dialog import ParametersDialog
from plethysmo.dialogs.plot_dialog import PlotDialog
from plethysmo.dialogs.statistics_dialog import StatisticsDialog
from plethysmo.dialogs.roi_dialog import ROIDialog
from plethysmo.kernel.parameters import PARAMETERS
from plethysmo.models.edf_files_list_model import EDFFilesListModel, EDFFilesListModelError
from plethysmo.models.excluded_zones_list_model import ExcludedZonesListModel
from plethysmo.models.intervals_list_model import IntervalsListModel
from plethysmo.models.rois_list_model import ROISListModel
from plethysmo.utils.progress_bar import progress_bar
from plethysmo.views.deselectable_listview import DeselectableListView
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

        self._patch_holder = None

    def build_events(self):
        """Build the signal/slots.
        """

        self._search_valid_intervals_button.clicked.connect(self.on_search_valid_intervals)
        self._intervals_list.doubleClicked.connect(self.on_show_zoomed_data)
        self._add_roi_button.clicked.connect(lambda: self.on_add_roi(self._rois_list))
        self._add_excluded_zone_button.clicked.connect(lambda: self.on_add_roi(self._excluded_zones_list))
        self._compute_statistics.clicked.connect(self.on_compute_statistics)

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

        main_layout.addWidget(self._compute_statistics)

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

        parameters_action = QtWidgets.QAction('&Parameters', self)
        parameters_action.setShortcut('Ctrl+P')
        parameters_action.setStatusTip('Open parameters dialog')
        parameters_action.triggered.connect(self.on_open_parameters_dialog)
        file_menu.addAction(parameters_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit inspigtor')
        exit_action.triggered.connect(self.on_quit_application)
        file_menu.addAction(exit_action)

    def build_widgets(self):
        """Build the widgets.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._edf_files_list = QtWidgets.QListView()
        self._edf_files_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        edf_files_list_model = EDFFilesListModel(self)
        self._edf_files_list.setModel(edf_files_list_model)
        self._edf_files_list.installEventFilter(self)

        self._rois_list = DeselectableListView(self)
        self._add_roi_button = QtWidgets.QPushButton('Add ROI')
        self._rois_list.installEventFilter(self)
        self._rois_list.deselectItem.connect(self.on_deselect_item)

        self._excluded_zones_list = DeselectableListView(self)
        self._add_excluded_zone_button = QtWidgets.QPushButton('Add exclusion zone')
        self._excluded_zones_list.installEventFilter(self)
        self._excluded_zones_list.deselectItem.connect(self.on_deselect_item)

        self._search_valid_intervals_button = QtWidgets.QPushButton('Search valid intervals')

        self._intervals_list = DeselectableListView(self)
        self._intervals_list.installEventFilter(self)
        self._intervals_list.deselectItem.connect(self.on_deselect_item)

        self._plot_widget = PlotWidget(self)
        self._plot_widget.axes.set_xlabel('Time (s)')

        self._compute_statistics = QtWidgets.QPushButton('Compute statistics')

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

        icon_path = os.path.join(
            plethysmo.__path__[0], "icons", "plethysmo.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 1200, 800)

        self.setWindowTitle("plethysmo {}".format(__version__))

        self.show()

    def eventFilter(self, watched, event):
        """Filter the events.
        """

        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Delete:
            # Capture the Delete key press event for the roi _list
            if watched in [self._rois_list, self._excluded_zones_list]:
                current_index = watched.currentIndex()
                model = watched.model()
                model.remove_roi(current_index.row())
                return True

            elif watched == self._intervals_list:
                current_index = watched.currentIndex()
                model = watched.model()
                model.remove_interval(current_index.row())
                return True

            elif watched == self._edf_files_list:
                current_index = watched.currentIndex()
                model = watched.model()
                model.remove_reader_from_index(current_index.row())
                return True

        return super(MainWindow, self).eventFilter(watched, event)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    def on_add_roi(self, widget):
        """Pops up a dialog for drawing a ROI which will serve for setting up a zone of interest for intervals search.
        """

        # Check that some EDF files have been loaded
        edf_files_model = self._edf_files_list.model()
        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        # Get the current reader
        current_index = self._edf_files_list.currentIndex()
        reader = edf_files_model.data(
            current_index, role=EDFFilesListModel.Reader)

        # Pops up a dialog for drawing the ROI
        dialog = ROIDialog(reader, self)

        # The ROI is accepted
        if dialog.exec_():
            # Fetch the ROI from the dialog instance and add to the ROI list model
            name, new_roi = dialog.roi
            model = widget.model()
            if model is not None:
                model.add_roi(name, new_roi)
                logging.info('Added ROI {} to {} file'.format(
                    name, reader.filename))

    def on_compute_statistics(self):
        """Compute the statistics for all readers loaded so far.
        """

        # Check that some EDF files have been loaded
        edf_files_model = self._edf_files_list.model()
        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        all_readers = [edf_files_model.data(edf_files_model.index(i), role=EDFFilesListModel.Reader) for i in range(edf_files_model.rowCount())]

        all_statistics = collections.OrderedDict()

        progress_bar.reset(len(all_readers))

        logging.info('Start computing plethysmographic data ...')

        for i, reader in enumerate(all_readers):
            all_statistics[reader.filename] = reader.compute_statistics()
            progress_bar.update(i+1)

        logging.info('... done')

        if not all_statistics:
            logging.warning('No statistics computed')
            return

        dialog = StatisticsDialog(all_statistics, self)
        dialog.show()

    def on_deselect_item(self, widget):
        """Event called when the user unselected a selected item by reclicking on it.

        This is used by the ROI, excluded zone and interval list views.

        Args:
            widget (plethysmo.views.deselectable_listview.DeselectableListView): the list view whose item was unselected
        """

        if widget == self._patch_holder:
            self._plot_widget.clear_patch()
            self._patch_holder = None

    def on_load_data(self):
        """Event called when the user loads data from the main menu.
        """

        # Pop up a file browser
        edf_files = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open EDF file(s)', '', 'EDF Files (*.edf *.EDF)')[0]
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

        logging.info('Loaded successfully {} files out of {}'.format(
            n_loaded_files, n_edf_files))

    def on_open_parameters_dialog(self):
        """Event called when the user open the parameters dialog.
        """

        dialog = ParametersDialog(self)

        # The dialog should not be modal
        dialog.show()

    def on_quit_application(self):
        """Event called when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(
            self, 'Quit', "Do you really want to quit?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_search_valid_intervals(self):
        """Event triggered when the user clicks on the search valid intervals button.
        """

        # Check that some EDF files have been loaded
        edf_files_model = self._edf_files_list.model()
        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        # Check that some EDF files have been loaded
        edf_files_model = self._edf_files_list.model()
        if edf_files_model.rowCount() == 0:
            logging.info('No EDF file(s) loaded.')
            return

        all_readers = [edf_files_model.data(edf_files_model.index(i), role=EDFFilesListModel.Reader) for i in range(edf_files_model.rowCount())]

        progress_bar.reset(len(all_readers))

        logging.info('Search valid intervals ...')

        for i, reader in enumerate(all_readers):

            # Search for valid intervals
            reader.update_valid_intervals()

            progress_bar.update(i+1)

        logging.info('... done')

    def on_select_edf_file(self, index):
        """Event fired when an EDF file is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the EDF file in the corresponding list view
        """

        edf_files_list_model = self._edf_files_list.model()

        reader = edf_files_list_model.data(
            index, role=EDFFilesListModel.Reader)

        if reader == QtCore.QVariant():
            return

        # Plot the signal contained in the selected reader
        self._plot_widget.update_plot(reader.times, reader.signal)

        # Replace the current ROIs list model by the one from the selected reader
        rois_list_model = ROISListModel(reader, self)
        self._rois_list.setModel(rois_list_model)
        rois_list_model.noROI.connect(lambda: self._plot_widget.clear_patch())
        self._rois_list.selectionModel().currentChanged.connect(self.on_select_roi)

        # Replace the current excluded zones list model by the one from the selected reader
        excluded_zones_list_model = ExcludedZonesListModel(reader, self)
        self._excluded_zones_list.setModel(excluded_zones_list_model)
        excluded_zones_list_model.noROI.connect(
            lambda: self._plot_widget.clear_patch())
        self._excluded_zones_list.selectionModel(
        ).currentChanged.connect(self.on_select_excluded_zone)

        # Replace the current intervals found with the one from the selected reader and roi
        intervals_list_model = IntervalsListModel([], reader.dt, self)
        self._intervals_list.setModel(intervals_list_model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        self._plot_widget.clear_patch()

    def on_select_interval(self, index):
        """Event fired when an interval is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the interval in the corresponding list view
        """

        # Get the selected reader
        selected_edf_file_index = self._edf_files_list.currentIndex()
        edf_files_list_model = self._edf_files_list.model()
        reader = edf_files_list_model.data(selected_edf_file_index, role=EDFFilesListModel.Reader)

        # Get the selected interval
        intervals_list_model = self._intervals_list.model()
        interval = intervals_list_model.data(index, role=IntervalsListModel.SelectedInterval)

        if interval == QtCore.QVariant():
            return

        # Convert the start and end of the interval from index unit to time unit
        min_x = interval[0]*reader.dt
        max_x = interval[1]*reader.dt

        min_y = reader.signal[interval[0]:interval[1]].min()
        max_y = reader.signal[interval[0]:interval[1]].max()

        # Show the interval
        width = max_x - min_x
        height = max_y - min_y
        self._plot_widget.show_interval(min_x, min_y, width, height, 'blue')

        self._patch_holder = self._intervals_list

    def on_select_excluded_zone(self, index):
        """Event called when the user clicks on a ROI.
        """

        # Get the selected ROI
        model = self._excluded_zones_list.model()
        if model is None:
            return

        roi = model.data(index, role=ROISListModel.SelectedROI)

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

        self._patch_holder = self._excluded_zones_list

    def on_select_roi(self, index):
        """Event called when the user clicks on a ROI.
        """

        # Get the selected reader
        selected_edf_file_index = self._edf_files_list.currentIndex()
        edf_files_list_model = self._edf_files_list.model()
        reader = edf_files_list_model.data(
            selected_edf_file_index, role=EDFFilesListModel.Reader)

        # Get the selected ROI
        model = self._rois_list.model()
        if model is None:
            return

        roi_name = model.data(index, role=QtCore.Qt.DisplayRole)
        roi = model.data(index, role=ROISListModel.SelectedROI)

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

        self._patch_holder = self._rois_list

        # Replace the current intervals list model by a new one
        intervals_list_model = IntervalsListModel(reader.valid_intervals[roi_name], reader.dt, self)
        self._intervals_list.setModel(intervals_list_model)

        # Create a signal/slot connexion for row changed event
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

    def on_show_zoomed_data(self, index):
        """Pops a dialog with the zoomed data for a selected interval.
        """

        # Get the selected reader
        selected_edf_file_index = self._edf_files_list.currentIndex()
        edf_files_list_model = self._edf_files_list.model()
        reader = edf_files_list_model.data(
            selected_edf_file_index, role=EDFFilesListModel.Reader)

        # Get the selected interval
        intervals_list_model = self._intervals_list.model()
        interval = intervals_list_model.data(
            index, role=IntervalsListModel.SelectedInterval)

        # The zoomed data
        zoomed_times = reader.times[interval[0]:interval[1]]
        zoomed_signal = reader.signal[interval[0]:interval[1]]

        # Plot the zoomed data
        dialog = PlotDialog(zoomed_times, zoomed_signal, self)
        dialog.setWindowTitle('Signal at [{},{}] s'.format(
            zoomed_times[0], zoomed_times[-1]))
        dialog.axes.set_xlabel('Time (s)')

        peaks, _ = find_peaks(zoomed_signal, prominence=PARAMETERS['signal prominence'])
        peaks = [p for p in peaks if zoomed_signal[p] > 0]
        dialog.axes.plot(zoomed_times[peaks],zoomed_signal[peaks],"or")

        peaks, _ = find_peaks(-zoomed_signal, prominence=PARAMETERS['signal prominence'])
        peaks = [p for p in peaks if zoomed_signal[p] < 0]
        dialog.axes.plot(zoomed_times[peaks],zoomed_signal[peaks],"ob")

        dialog.show()
