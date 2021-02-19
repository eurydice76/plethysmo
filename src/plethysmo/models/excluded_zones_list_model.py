from PyQt5 import QtCore

class ExcludedZonesListModelError(Exception):
    """Error handler for exception related with ExcludedZonesListModel class.
    """

class ExcludedZonesListModel(QtCore.QAbstractListModel):
    """This class implements a model for a list of Region Of Interest.
    """

    noROI = QtCore.pyqtSignal()

    SelectedROI = QtCore.Qt.UserRole + 1

    def __init__(self, reader, parent):
        """Constructor.

        Args:
            reader (plethysmo.kernel.edf_file_reader.EDFFileReader)
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(ExcludedZonesListModel, self).__init__(parent)

        self._reader = reader

    def add_roi(self, name, roi):
        """Add a new ROI to the model.

        Args:
            name (str): the name of the ROI
            roi (plethysmo.kernel.roi.ROI): the ROI
        """

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        self._reader.add_excluded_zone(name, roi)

        self.endInsertRows()

    def data(self, index, role):
        """Return the data for given index and role.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
            role (int): the role

        Return:
           PyQt5.QtCore.QVariant: the data 
        """

        if not index.isValid():
            return QtCore.QVariant()

        row = index.row()

        excluded_zones = self._reader.excluded_zones

        roi_names = list(excluded_zones.keys())

        selected_roi_name = roi_names[row]

        selected_roi = excluded_zones[selected_roi_name]

        if role == QtCore.Qt.DisplayRole:
            return selected_roi_name

        elif role == QtCore.Qt.ToolTipRole:

            lower_corner = selected_roi.lower_corner
            upper_corner = selected_roi.upper_corner

            return 'from ({:f},{:f}) to ({:f}:{:f})'.format(lower_corner[0],lower_corner[1],upper_corner[0],upper_corner[1])

        elif role == ExcludedZonesListModel.SelectedROI:
            return selected_roi

        else:
            return QtCore.QVariant()

    def remove_roi(self, index):
        """Remove an EDF file from its index
        """

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        roi_names = list(self._reader.excluded_zones.keys())

        selected_roi_name = roi_names[index]

        self._reader.delete_roi(selected_roi_name)

        self.endRemoveRows()

        if self.rowCount() == 0:

            self.noRoi.emit()

    def rowCount(self, parent=None):
        """Returns the number of row of the model.
        """

        return len(self._reader.excluded_zones)