import logging
import os

import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets

from plethysmo.models.pandas_data_model import PandasDataModel
from plethysmo.utils.progress_bar import progress_bar
from plethysmo.views.copy_pastable_tableview import CopyPastableTableView

class StatisticsDialog(QtWidgets.QDialog):
    """This class implements the widgets that shows the results of plethysmographic data computation.
    """

    def __init__(self, statistics, parent=None):

        super(StatisticsDialog, self).__init__(parent)

        self._statistics = statistics

        self._init_ui()

    def _build_event(self):
        """Build the signal/slot related with this widget.
        """

        self._readers_listview.selectionModel().currentChanged.connect(self.on_select_reader)
        self._export_all_pushbutton.clicked.connect(self.on_export_results)

    def _build_layout(self):
        """Build the layout.
        """

        self._main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._readers_listview)
        vlayout.addWidget(self._rois_listview)
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self._statistics_tableview, stretch=2)

        self._main_layout.addLayout(hlayout)
        self._main_layout.addWidget(self._export_all_pushbutton)

        self.setLayout(self._main_layout)

        self.setGeometry(0, 0, 1000, 600)

    def _build_widgets(self):
        """Builds the widgets.
        """

        self._readers_listview = QtWidgets.QListView()

        # Create a model and populate it with the name of the readers
        model = QtGui.QStandardItemModel()
        for reader in self._statistics.keys():
            item = QtGui.QStandardItem(reader)
            model.appendRow(item)
        self._readers_listview.setModel(model)

        self._rois_listview = QtWidgets.QListView()

        self._statistics_tableview = CopyPastableTableView(',')

        self._export_all_pushbutton = QtWidgets.QPushButton('Export results')

    def _init_ui(self):
        """Initializes the ui.
        """

        self._build_widgets()
        self._build_layout()
        self._build_event()

    def on_export_results(self):
        """Export the results to an excel file.
        """

        progress_bar.reset(len(self._statistics))

        for i, (reader, dataframe_per_roi) in enumerate(self._statistics.items()):

            if not dataframe_per_roi:
                continue

            reader_without_ext = os.path.splitext(reader)[0]

            excel_file = '{}.xlsx'.format(reader_without_ext)

            # Create a Pandas Excel writer using XlsxWriter as the engine.
            writer = pd.ExcelWriter(excel_file, engine='openpyxl')

            for roi, dataframe in dataframe_per_roi.items():

                try:
                    dataframe.to_excel(writer, sheet_name=roi)
                except:
                    logging.error('Can not export {} sheet result to {} filename'.format(roi, excel_file))

            writer.save()

            progress_bar.update(i+1)

    def on_select_reader(self, index):
        """Select a reader and update the ROI list view with the ROI defined for the selected reader.
        """

        # The selected reader name
        readers_model = self._readers_listview.model()
        reader = readers_model.data(index, QtCore.Qt.DisplayRole)

        # Create a new model and populate it with the ROI names corresponding to the selected reader
        model = QtGui.QStandardItemModel()
        for roi in self._statistics[reader].keys():
            item = QtGui.QStandardItem(roi)
            model.appendRow(item)
        self._rois_listview.setModel(model)

        self._rois_listview.selectionModel().currentChanged.connect(self.on_select_roi)

        self._statistics_tableview.setModel(None)

    def on_select_roi(self, index):
        """Select a ROI and update the statistics table view accoding to the corresponding contents for the ROI.
        """

        # The selected reader name
        readers_model = self._readers_listview.model()
        reader = readers_model.data(self._readers_listview.currentIndex(), QtCore.Qt.DisplayRole)

        # The selected roi name
        rois_model = self._rois_listview.model()
        roi = rois_model.data(index, QtCore.Qt.DisplayRole)

        # Build up a pandas data model
        model = PandasDataModel(self, self._statistics[reader][roi])

        # Update the statistics table view
        self._statistics_tableview.setModel(model)



