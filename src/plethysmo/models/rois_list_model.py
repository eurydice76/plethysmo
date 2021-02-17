from PyQt5 import QtCore

class ROISListModelError(Exception):
    """Error handler for exception related with ROISListModel class.
    """

class ROISListModel(QtCore.QAbstractListModel):
    """This class implements a model for a list of Region Of Interest.
    """

    no_roi = QtCore.pyqtSignal()

    SelectedROI = QtCore.Qt.UserRole + 1

    def __init__(self, rois, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(ROISListModel, self).__init__(parent)

        self._rois = rois

    def add_roi(self, roi):
        """Add a new ROI to the model.

        Args:
            roi (plethysmo.kernel.roi.ROI): the ROI
        """

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        self._rois.append(roi)

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

        selected_roi = self._rois[row]

        if role == QtCore.Qt.DisplayRole:
            return selected_roi.name

        elif role == QtCore.Qt.ToolTipRole:

            lower_corner = selected_roi.lower_corner
            upper_corner = selected_roi.upper_corner

            return 'from ({:f},{:f}) to ({:f}:{:f})'.format(lower_corner[0],lower_corner[1],upper_corner[0],upper_corner[1])

        elif role == ROISListModel.SelectedROI:
            return selected_roi

        else:
            return QtCore.QVariant()

    def remove_roi(self, index):
        """Remove an EDF file from its index
        """

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        try:
            del self._rois[index]
        except IndexError:
            pass

        self.endRemoveRows()

        if self.rowCount() == 0:

            self.no_roi.emit()

    def rowCount(self, parent=None):
        """Returns the number of row of the model.
        """

        return len(self._rois)